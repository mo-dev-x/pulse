# Zone Search Guide

## Purpose
Add searchable campus zones so users can find Universite Laval locations by name, code, or common alias instead of remembering numeric IDs.

## Backend Endpoints
- `GET /api/zones/search?q=<query>`
- `GET /api/zones/suggest?q=<query>`
- `GET /api/zones`
- `GET /api/zones/<id>`
- `GET /api/zones/types`

## Search Behavior
- `search`
  - Searches `name` and `description`
  - Supports optional `type` filter
  - Returns `match_score`
- `suggest`
  - Expands common aliases before searching
  - Examples:
    - `biblio` -> `Bonenfant`
    - `genie` -> `Pouliot`
    - `sport` -> `PEPS`
    - `cafe` -> `Café`

## Route Registration
- Blueprint file:
  - `backend/app/routes/zones.py`
- Registered in:
  - `backend/app/__init__.py`

## Data Model Notes
- `CampusZone.to_dict()` now returns both:
  - `type`
  - `zone_type`
- This keeps older consumers working while making search responses explicit.

## Seed Data
- `backend/schema.sql` now seeds real Universite Laval campus locations instead of the original placeholder set.
- If an existing database still has the older rows, apply an update script or reload the seed data manually.

## Example Queries
- `/api/zones/search?q=peps`
- `/api/zones/search?q=desjardins`
- `/api/zones/search?q=adj`
- `/api/zones/suggest?q=biblio`
- `/api/zones?type=academic`

## Frontend Integration Notes
- Use `/api/zones/search` for autocomplete.
- Persist the selected `zone.id` as `zone_id` when creating a post.
- Display `zone.name` to users and treat `zone_type` as a badge/filter value.
- Frontend integration files:
  - `Frontend/js/zone_autocomplete.js`
  - `Frontend/js/feed.js`
  - `Frontend/feed.html`

## Zone Seed Script
- Script location:
  - `backend/scripts/populate_campus_zones.py`
- Run with the project virtualenv:
  - `backend/venv/bin/python backend/scripts/populate_campus_zones.py`
- The script uses the existing backend `.env` variables:
  - `DB_HOST`
  - `DB_PORT`
  - `DB_USER`
  - `DB_PASSWORD`
  - `DB_NAME`

## Validation
1. Call `/api/zones/types` and confirm counts return by category.
2. Search `desjardins` and confirm academic + dining matches.
3. Search `peps` and confirm sports facilities appear first.
4. Call `/api/zones/suggest?q=biblio` and confirm Bonenfant is returned.
