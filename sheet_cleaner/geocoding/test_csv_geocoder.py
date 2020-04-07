import unittest
from geocoding import csv_geocoder
import pathlib
import os

class TestCSVGeocoder(unittest.TestCase):

    def setUp(self):
        cur_dir = pathlib.Path(__file__).parent.absolute()
        self.geocoder = csv_geocoder.CSVGeocoder(os.path.join(cur_dir, "geo_admin.tsv"))

    def test_found(self):
        geo = self.geocoder.Geocode("Sunac City, Shangcheng, Changchun City", "Jilin", "China")
        self.assertAlmostEqual(geo.lat, 43.8296097)
        self.assertAlmostEqual(geo.lng, 125.25924)
        self.assertEqual(geo.geo_resolution, "point")
        self.assertEqual(geo.country_new, "China")
        self.assertEqual(geo.admin_id, 220104)
        self.assertEqual(geo.location, "Sunac City, Shangcheng")
        self.assertEqual(geo.admin1, "Jilin")
        self.assertEqual(geo.admin2, "Changchun City")
        self.assertEqual(geo.admin3, "Chaoyang District")

    def test_not_found(self):
        self.assertIsNone(self.geocoder.Geocode("foo", "bar", "baz"))