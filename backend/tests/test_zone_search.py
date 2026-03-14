"""Automated tests for campus zone search endpoints."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from app.models.campus_zone import CampusZone
from tests.phase5_test_utils import Phase5BaseTestCase


class TestZoneSearch(Phase5BaseTestCase):

    def setUp(self):
        super().setUp()
        db.session.add_all([
            CampusZone(
                name='Pavillon Alphonse-Desjardins',
                description='Administration, sciences sociales (ADJ)',
                zone_type='academic',
            ),
            CampusZone(
                name='PEPS - Pavillon principal',
                description='Centre sportif principal',
                zone_type='sports',
            ),
            CampusZone(
                name='Café Desjardins',
                description='Cafétéria Pavillon Alphonse-Desjardins',
                zone_type='dining',
            ),
            CampusZone(
                name='Pavillon Jean-Charles-Bonenfant',
                description='Bibliothèque des sciences humaines et sociales (BNF)',
                zone_type='academic',
            ),
        ])
        db.session.commit()

    def test_search_requires_query(self):
        response = self.client.get('/api/zones/search')
        self.assertEqual(response.status_code, 400)

    def test_search_by_partial_name(self):
        response = self.client.get('/api/zones/search?q=desjardins')
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertGreaterEqual(payload['count'], 2)
        self.assertEqual(payload['zones'][0]['name'], 'Pavillon Alphonse-Desjardins')

    def test_search_by_type_filter(self):
        response = self.client.get('/api/zones/search?q=desjardins&type=dining')
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertEqual(payload['count'], 1)
        self.assertEqual(payload['zones'][0]['zone_type'], 'dining')

    def test_alias_suggest_expands_common_terms(self):
        response = self.client.get('/api/zones/suggest?q=biblio')
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertEqual(payload['expanded_query'], 'Bonenfant')
        self.assertEqual(payload['zones'][0]['name'], 'Pavillon Jean-Charles-Bonenfant')

    def test_get_all_zones_and_types(self):
        zones_resp = self.client.get('/api/zones')
        self.assertEqual(zones_resp.status_code, 200, zones_resp.get_json())
        self.assertEqual(zones_resp.get_json()['count'], 4)

        types_resp = self.client.get('/api/zones/types')
        self.assertEqual(types_resp.status_code, 200, types_resp.get_json())
        types = {item['type']: item['count'] for item in types_resp.get_json()['types']}
        self.assertEqual(types['academic'], 2)
        self.assertEqual(types['sports'], 1)
        self.assertEqual(types['dining'], 1)
