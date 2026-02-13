"""
Internationalization (i18n) Utility

Provides bilingual error messages and content for Université Laval.
All messages are in both French and English.
"""

# Bilingual error messages
MESSAGES = {
    # Authentication errors
    'invalid_email': {
        'en': 'Invalid email address',
        'fr': 'Adresse courriel invalide'
    },
    'email_domain_error': {
        'en': 'You must use your @ulaval.ca email address',
        'fr': 'Vous devez utiliser votre adresse courriel @ulaval.ca'
    },
    'password_weak': {
        'en': 'Password must be at least 8 characters with uppercase, lowercase, and digit',
        'fr': 'Le mot de passe doit contenir au moins 8 caractères avec majuscules, minuscules et chiffres'
    },
    'password_required': {
        'en': 'Password is required',
        'fr': 'Le mot de passe est requis'
    },
    'email_required': {
        'en': 'Email is required',
        'fr': 'Le courriel est requis'
    },
    'username_required': {
        'en': 'Username is required',
        'fr': "Le nom d'utilisateur est requis"
    },
    'username_invalid': {
        'en': 'Username must be 3-50 characters, alphanumeric and underscores only, cannot start with number',
        'fr': "Le nom d'utilisateur doit contenir 3-50 caractères, alphanumérique et traits de soulignement uniquement, ne peut pas commencer par un chiffre"
    },
    'user_exists_email': {
        'en': 'An account with this email already exists',
        'fr': 'Un compte avec ce courriel existe déjà'
    },
    'user_exists_username': {
        'en': 'This username is already taken',
        'fr': "Ce nom d'utilisateur est déjà pris"
    },
    'invalid_credentials': {
        'en': 'Invalid email or password',
        'fr': 'Courriel ou mot de passe invalide'
    },
    'account_disabled': {
        'en': 'Your account has been deactivated',
        'fr': 'Votre compte a été désactivé'
    },
    'user_not_found': {
        'en': 'User not found',
        'fr': 'Utilisateur non trouvé'
    },
    
    # Post errors
    'post_content_required': {
        'en': 'Post content is required',
        'fr': 'Le contenu de la publication est requis'
    },
    'post_too_short': {
        'en': 'Post must be at least 10 characters',
        'fr': 'La publication doit contenir au moins 10 caractères'
    },
    'post_too_long': {
        'en': 'Post cannot exceed 500 characters',
        'fr': 'La publication ne peut pas dépasser 500 caractères'
    },
    'rate_limit': {
        'en': 'Too many posts. Please wait before posting again.',
        'fr': 'Trop de publications. Veuillez patienter avant de publier à nouveau.'
    },
    'zone_not_found': {
        'en': 'Campus zone not found',
        'fr': 'Zone du campus non trouvée'
    },
    
    # Profile errors
    'display_name_invalid': {
        'en': 'Display name must be 1-100 characters',
        'fr': "Le nom d'affichage doit contenir 1-100 caractères"
    },
    'bio_too_long': {
        'en': 'Bio must be 500 characters or less',
        'fr': 'La biographie doit contenir 500 caractères ou moins'
    },
    'pseudonym_required': {
        'en': 'Pseudonym is required',
        'fr': 'Le pseudonyme est requis'
    },
    'pseudonym_cooldown': {
        'en': 'You can change your pseudonym in {days} days',
        'fr': 'Vous pouvez changer votre pseudonyme dans {days} jours'
    },
    'pseudonym_reserved': {
        'en': 'This pseudonym is reserved',
        'fr': 'Ce pseudonyme est réservé'
    },
    'pseudonym_invalid': {
        'en': 'Pseudonym must be 3-50 characters',
        'fr': 'Le pseudonyme doit contenir 3-50 caractères'
    },
    
    # General errors
    'validation_error': {
        'en': 'Validation error',
        'fr': 'Erreur de validation'
    },
    'server_error': {
        'en': 'An unexpected error occurred',
        'fr': 'Une erreur inattendue est survenue'
    },
    'not_found': {
        'en': 'Resource not found',
        'fr': 'Ressource non trouvée'
    },
    'unauthorized': {
        'en': 'Authentication required',
        'fr': 'Authentification requise'
    },
    'forbidden': {
        'en': 'You do not have permission to access this resource',
        'fr': "Vous n'avez pas la permission d'accéder à cette ressource"
    },
    
    # Success messages
    'user_created': {
        'en': 'User created successfully',
        'fr': 'Utilisateur créé avec succès'
    },
    'login_successful': {
        'en': 'Login successful',
        'fr': 'Connexion réussie'
    },
    'logout_successful': {
        'en': 'Logout successful',
        'fr': 'Déconnexion réussie'
    },
    'profile_updated': {
        'en': 'Profile updated successfully',
        'fr': 'Profil mis à jour avec succès'
    },
    'pseudonym_updated': {
        'en': 'Pseudonym updated successfully',
        'fr': 'Pseudonyme mis à jour avec succès'
    },
    'post_created': {
        'en': 'Post created successfully',
        'fr': 'Publication créée avec succès'
    },
    'post_deleted': {
        'en': 'Post deleted successfully',
        'fr': 'Publication supprimée avec succès'
    },

    # Social / Follow messages
    'cannot_follow_self': {
        'en': 'You cannot follow yourself',
        'fr': 'Vous ne pouvez pas vous suivre vous-même'
    },
    'already_following': {
        'en': 'You are already following this user',
        'fr': 'Vous suivez déjà cet utilisateur'
    },
    'not_following': {
        'en': 'You are not following this user',
        'fr': 'Vous ne suivez pas cet utilisateur'
    },
    'follow_success': {
        'en': 'Successfully followed user',
        'fr': 'Utilisateur suivi avec succès'
    },
    'unfollow_success': {
        'en': 'Successfully unfollowed user',
        'fr': 'Utilisateur désabonné avec succès'
    },

    # Feed messages
    'feed_empty': {
        'en': 'Your feed is empty. Follow users to see their posts!',
        'fr': 'Votre fil est vide. Suivez des utilisateurs pour voir leurs publications !'
    },

    # Reaction messages
    'emoji_required': {
        'en': 'Emoji is required',
        'fr': "L'émoji est requis"
    },
    'emoji_invalid': {
        'en': 'Invalid emoji. Use one of the allowed emojis.',
        'fr': 'Émoji invalide. Utilisez un des émojis autorisés.'
    },
    'reaction_added': {
        'en': 'Reaction added',
        'fr': 'Réaction ajoutée'
    },
    'reaction_updated': {
        'en': 'Reaction updated',
        'fr': 'Réaction mise à jour'
    },
    'reaction_removed': {
        'en': 'Reaction removed',
        'fr': 'Réaction retirée'
    },
    'no_reaction': {
        'en': 'You have not reacted to this post',
        'fr': "Vous n'avez pas réagi à cette publication"
    },

    # Post management
    'post_not_found': {
        'en': 'Post not found',
        'fr': 'Publication non trouvée'
    },
    'post_delete_expired': {
        'en': 'Posts can only be deleted within 24 hours of creation',
        'fr': 'Les publications ne peuvent être supprimées que dans les 24 heures suivant leur création'
    },

    # Media messages
    'file_type_invalid': {
        'en': 'Invalid file type. Allowed: PNG, JPG, GIF, WebP',
        'fr': 'Type de fichier invalide. Autorisés : PNG, JPG, GIF, WebP'
    }
}


def get_message(key, lang='en', **kwargs):
    """
    Get error message in specified language
    
    Args:
        key (str): Message key
        lang (str): 'en' or 'fr' (default: 'en')
        **kwargs: Format parameters for the message
    
    Returns:
        str: Translated message
    
    Example:
        get_message('pseudonym_cooldown', 'fr', days=45)
        # Returns: "Vous pouvez changer votre pseudonyme dans 45 jours"
    """
    msg = MESSAGES.get(key, {})
    text = msg.get(lang, msg.get('en', 'Unknown error'))
    
    # Format with kwargs if provided
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass  # If format key not found, return unformatted
    
    return text


def get_bilingual_message(key, **kwargs):
    """
    Get error message in both languages (French / English)
    
    Args:
        key (str): Message key
        **kwargs: Format parameters for the message
    
    Returns:
        str: Message in format "French / English"
    
    Example:
        get_bilingual_message('email_domain_error')
        # Returns: "Vous devez utiliser votre adresse courriel @ulaval.ca / 
        #           You must use your @ulaval.ca email address"
    """
    fr_msg = get_message(key, 'fr', **kwargs)
    en_msg = get_message(key, 'en', **kwargs)
    return f"{fr_msg} / {en_msg}"


def detect_language_preference(request):
    """
    Detect user's language preference from request
    
    Checks in order:
    1. Query parameter (?lang=fr)
    2. Accept-Language header
    3. Default to French (Université Laval is primarily French)
    
    Args:
        request: Flask request object
    
    Returns:
        str: 'fr' or 'en'
    """
    # Check query parameter
    lang_param = request.args.get('lang', '').lower()
    if lang_param in ['fr', 'en']:
        return lang_param
    
    # Check Accept-Language header
    accept_language = request.headers.get('Accept-Language', '')
    if 'fr' in accept_language.lower():
        return 'fr'
    if 'en' in accept_language.lower():
        return 'en'
    
    # Default to French
    return 'fr'