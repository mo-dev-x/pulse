"""Optional Meilisearch integration for hybrid search rollout."""

from __future__ import annotations

from typing import Any

import requests
from flask import current_app


def is_enabled() -> bool:
    """Return whether Meilisearch-backed search is enabled."""
    return bool(current_app.config.get('ENABLE_MEILISEARCH', False))


def _base_url() -> str:
    return current_app.config.get('MEILISEARCH_URL', 'http://127.0.0.1:7700').rstrip('/')


def _headers() -> dict[str, str]:
    headers = {'Content-Type': 'application/json'}
    api_key = current_app.config.get('MEILISEARCH_API_KEY')
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    return headers


def _index_name(kind: str) -> str:
    return current_app.config.get(f'MEILISEARCH_{kind.upper()}_INDEX', kind)


def _document_url(kind: str, document_id: int | str | None = None) -> str:
    base = f"{_base_url()}/indexes/{_index_name(kind)}/documents"
    return f"{base}/{document_id}" if document_id is not None else base


def search(kind: str, query: str, limit: int = 50, filters: list[str] | None = None) -> list[dict[str, Any]]:
    """Search one Meilisearch index and return raw hit dictionaries."""
    payload: dict[str, Any] = {'q': query, 'limit': limit}
    if filters:
        payload['filter'] = filters
    try:
        response = requests.post(
            f"{_base_url()}/indexes/{_index_name(kind)}/search",
            json=payload,
            headers=_headers(),
            timeout=3,
        )
        response.raise_for_status()
        return response.json().get('hits', [])
    except Exception:
        current_app.logger.warning(
            'Meilisearch search failed for index=%s query=%s',
            _index_name(kind),
            query,
        )
        raise


def upsert_documents(kind: str, documents: list[dict[str, Any]]) -> None:
    """Create or update Meilisearch documents best-effort."""
    if not is_enabled() or not documents:
        return

    response = requests.post(
        _document_url(kind),
        json=documents,
        headers=_headers(),
        timeout=3,
    )
    response.raise_for_status()


def delete_document(kind: str, document_id: int | str) -> None:
    """Delete one Meilisearch document best-effort."""
    if not is_enabled():
        return

    response = requests.delete(
        _document_url(kind, document_id=document_id),
        headers=_headers(),
        timeout=3,
    )
    if response.status_code not in {200, 202, 204, 404}:
        response.raise_for_status()
