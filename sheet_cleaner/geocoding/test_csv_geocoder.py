import unittest
from geocoding import csv_geocoder
import pathlib
import os

class TestCSVGeocoder(unittest.TestCase):

    def setUp(self):
        cur_dir = pathlib.Path(__file__).parent.absolute()
        self.geocoder = csv_geocoder.CSVGeocoder(os.path.join(cur_dir, "geo_admin.tsv"))

    def test_found(self):
        geo = self.geocoder.Geocode("Lyon", "Auvergne-Rhone-Alpes", "France")
        self.assertAlmostEqual(geo.lat, 45.76)
        self.assertAlmostEqual(geo.lng, 4.84)
        self.assertEqual(geo.geo_resolution, "point")
        self.assertEqual(geo.country_new, "France")
        self.assertEqual(geo.admin_id, 1)

    def test_not_founload(self):
        self.assertIsNone(self.geocoder.Geocode("foo", "bar", "baz"))