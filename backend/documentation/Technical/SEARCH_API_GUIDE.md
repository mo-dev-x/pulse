# Search API Guide

## Purpose
Document the Phase 6 unified search endpoints, query parameters, and privacy guarantees.

## Endpoints
- `GET /api/search`
- `GET /api/search/users`

## `GET /api/search`

### Query Params
- `q`: required, minimum 2 characters
- `type`: optional, one of `posts`, `users`, `zones`, `all`
- `page`: optional, default `1`
- `per_page`: optional, default `20`, max `50`
- `zone_id`: optional, restricts post matches to a zone

### Response Shape
```json
{
  "query": "bibliotheque",
  "results": {
    "posts": [],
    "users": [],
    "zones": []
  },
  "counts": {
    "posts": 0,
    "users": 0,
    "zones": 0
  },
  "page": 1,
  "has_next": false
}
```

### Production Indexes
Search is intended to run with MySQL `FULLTEXT` indexes in production:

```sql
ALTER TABLE posts ADD FULLTEXT INDEX ft_posts_content (content);
ALTER TABLE users ADD FULLTEXT INDEX ft_users_identity (username, display_name, bio);
ALTER TABLE campus_zones ADD FULLTEXT INDEX ft_zones_search (name, description);
```

## `GET /api/search/users`

### Query Params
- `q`: required, minimum 1 character
- `limit`: optional, default `5`, max `20`

### Use Case
Used by `@mention` autocomplete in post and comment composition.

## Privacy Rules
- Anonymous posts are never returned
- Private profiles are never returned
- Deactivated users are never returned
- Posts by deactivated users are never returned
- Search results only expose public profile fields

## Implementation Notes
- Route file: `backend/app/routes/search.py`
- Search supports posts, users, and zones from one endpoint
- Zone search works alongside the dedicated zone search/suggest endpoints
- Post search should narrow results in SQL before Python-side match scoring
- Users and zones also narrow candidates in SQL before final ranking
- A feature-flagged Meilisearch path can be enabled later with `ENABLE_MEILISEARCH=true` while the database path remains the default

## Validation
1. Search with `type=posts` and confirm anonymous content is excluded.
2. Search with `type=users` and confirm private profiles are excluded.
3. Search with `type=zones` and confirm zone results return correctly.
4. Call `/api/search/users?q=jo` and confirm mention suggestions are returned.
