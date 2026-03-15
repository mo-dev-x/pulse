"""Moderation reports and admin review routes."""

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.middleware import require_admin
from app.models import Comment, Post, Report, User
from app.services.security_log_service import log_security_event
from app.utils.i18n import get_localized_message

bp = Blueprint('reports', __name__)

REPORTABLE_REASONS = {'spam', 'harassment', 'self_harm', 'misinformation', 'inappropriate', 'other'}
AUTO_FLAG_THRESHOLD = 5
AUTO_FLAG_WINDOW = timedelta(hours=24)


def _resolve_target(target_type, target_id):
    if target_type == 'post':
        return Post.query.get(target_id)
    if target_type == 'comment':
        return Comment.query.get(target_id)
    if target_type == 'user':
        return User.query.get(target_id)
    return None


def _target_owner_id(target_type, target):
    if target_type == 'user':
        return target.id
    return getattr(target, 'user_id', None)


def _target_preview(target_type, target):
    if not target:
        return None
    if target_type == 'post':
        return {'content': target.content[:160], 'hidden_by_mod': target.hidden_by_mod, 'is_flagged': target.is_flagged}
    if target_type == 'comment':
        return {'content': target.content[:160], 'parent_id': target.parent_id}
    if target_type == 'user':
        return {'username': target.username, 'display_name': target.display_name, 'is_deactivated': target.is_deactivated}
    return None


def _maybe_auto_flag_post(post_id):
    cutoff = datetime.utcnow() - AUTO_FLAG_WINDOW
    recent_count = Report.query.filter(
        Report.target_type == 'post',
        Report.target_id == post_id,
        Report.created_at >= cutoff
    ).count()

    post = Post.query.get(post_id)
    if post and recent_count >= AUTO_FLAG_THRESHOLD:
        post.is_flagged = True
        post.flagged_at = datetime.utcnow()
        post.hidden_by_mod = True


@bp.route('/reports', methods=['POST'])
@jwt_required()
def create_report():
    """Submit a moderation report for a post, comment, or user."""
    reporter_id = int(get_jwt_identity())
    data = request.get_json() or {}
    target_type = (data.get('target_type') or '').strip()
    target_id = data.get('target_id')
    reason = (data.get('reason') or '').strip()
    details = (data.get('details') or '').strip() or None

    if target_type not in {'post', 'comment', 'user'} or not isinstance(target_id, int) or reason not in REPORTABLE_REASONS:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': 'Invalid report payload'
        }), 400

    target = _resolve_target(target_type, target_id)
    if not target:
        return jsonify({
            'error': get_localized_message(request, 'not_found'),
            'message': 'Report target not found'
        }), 404

    if _target_owner_id(target_type, target) == reporter_id:
        return jsonify({
            'error': get_localized_message(request, 'validation_error'),
            'message': 'You cannot report your own content'
        }), 400

    existing = Report.query.filter_by(reporter_id=reporter_id, target_type=target_type, target_id=target_id).first()
    if existing:
        return jsonify({
            'error': 'duplicate_report',
            'message': 'You already reported this content'
        }), 409

    report = Report(
        reporter_id=reporter_id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        details=details,
    )
    db.session.add(report)
    db.session.flush()

    if target_type == 'post':
        _maybe_auto_flag_post(target_id)

    log_security_event(
        event_type='report_submitted',
        user_id=reporter_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        metadata={'report_id': report.id, 'target_type': target_type, 'target_id': target_id, 'reason': reason},
    )
    db.session.commit()

    return jsonify({
        'message': 'Report submitted. Our team will review it.',
        'report_id': report.id
    }), 201


@bp.route('/admin/reports', methods=['GET'])
@jwt_required()
@require_admin
def list_reports():
    """List moderation reports for admins."""
    status = (request.args.get('status') or 'pending').strip().lower()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    if status not in {'pending', 'reviewed', 'actioned', 'dismissed'}:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': 'Invalid status'}), 400

    pagination = Report.query.filter_by(status=status).order_by(Report.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    reports = []
    for report in pagination.items:
        target = _resolve_target(report.target_type, report.target_id)
        reports.append(report.to_dict(target_preview=_target_preview(report.target_type, target)))

    return jsonify({
        'reports': reports,
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'has_next': pagination.has_next,
    }), 200


@bp.route('/admin/reports/<int:report_id>', methods=['PATCH'])
@jwt_required()
@require_admin
def act_on_report(report_id):
    """Review or act on a moderation report."""
    admin_id = int(get_jwt_identity())
    data = request.get_json() or {}
    action = (data.get('action') or '').strip()
    report = Report.query.get(report_id)

    if not report:
        return jsonify({'error': get_localized_message(request, 'not_found'), 'message': 'Report not found'}), 404

    if action not in {'dismiss', 'hide_content', 'warn_user', 'deactivate_user'}:
        return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': 'Invalid action'}), 400

    target = _resolve_target(report.target_type, report.target_id)
    if not target:
        return jsonify({'error': get_localized_message(request, 'not_found'), 'message': 'Report target not found'}), 404

    target_user = target if report.target_type == 'user' else User.query.get(target.user_id)
    report.reviewed_by = admin_id
    report.reviewed_at = datetime.utcnow()

    if action == 'dismiss':
        report.status = 'dismissed'
    elif action == 'hide_content':
        if report.target_type != 'post':
            return jsonify({'error': get_localized_message(request, 'validation_error'), 'message': 'hide_content is only supported for posts'}), 400
        target.hidden_by_mod = True
        target.is_flagged = True
        target.flagged_at = target.flagged_at or datetime.utcnow()
        report.status = 'actioned'
        log_security_event(
            event_type='content_hidden_by_admin',
            user_id=admin_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            metadata={'report_id': report.id, 'post_id': target.id},
        )
    elif action == 'warn_user':
        report.status = 'reviewed'
        log_security_event(
            event_type='user_warned',
            user_id=admin_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            metadata={'report_id': report.id, 'target_user_id': target_user.id if target_user else None},
        )
    elif action == 'deactivate_user':
        if not target_user:
            return jsonify({'error': get_localized_message(request, 'not_found'), 'message': 'Target user not found'}), 404
        target_user.is_deactivated = True
        target_user.deactivated_at = datetime.utcnow()
        report.status = 'actioned'
        log_security_event(
            event_type='user_deactivated_by_admin',
            user_id=admin_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            metadata={'report_id': report.id, 'target_user_id': target_user.id},
        )

    log_security_event(
        event_type='report_reviewed',
        user_id=admin_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        metadata={'report_id': report.id, 'action': action},
    )
    db.session.commit()

    return jsonify({
        'message': 'Report updated',
        'report': report.to_dict(target_preview=_target_preview(report.target_type, target)),
    }), 200


@bp.route('/admin/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
@require_admin
def admin_delete_post(post_id):
    """Hard-delete a post as an admin moderation action."""
    admin_id = int(get_jwt_identity())
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': get_localized_message(request, 'not_found'), 'message': 'Post not found'}), 404

    db.session.delete(post)
    log_security_event(
        event_type='post_deleted_by_admin',
        user_id=admin_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        metadata={'post_id': post_id},
    )
    db.session.commit()
    return jsonify({'message': 'Post deleted', 'deleted': True}), 200


@bp.route('/admin/flagged', methods=['GET'])
@jwt_required()
@require_admin
def list_flagged_content():
    """List currently flagged posts for admin review."""
    posts = Post.query.filter(
        Post.is_flagged == True  # noqa: E712
    ).order_by(Post.flagged_at.desc(), Post.created_at.desc()).all()

    return jsonify({
        'posts': [
            {
                **post.to_dict(),
                'report_count': Report.query.filter_by(target_type='post', target_id=post.id).count(),
            }
            for post in posts
        ],
        'total': len(posts),
    }), 200
