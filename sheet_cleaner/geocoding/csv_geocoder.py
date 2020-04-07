"""This package contains a geocoder based on the former sheets VLOOKUP impl.

It uses a dump of the geo_admin sheet to csv to load all the locations in
memory and allows for fast access.
"""

from typing import NamedTuple, Dict
import csv
import logging

class Geocode(NamedTuple):
    """Geocode contains geocoding information about a location."""
    lat: float
    lng: float
    geo_resolution: str
    country_new: str
    admin_id: int

class CSVGeocoder:
    def __init__(self, init_csv_path: str):
        # Build a giant map of concatenated strings for fast lookup.
        # Do not try to be smart, just replicate whatever the spreadsheet was
        # doing. Data's so small it can all fit in memory and allow for fast
        # lookups.
        
        self.geocodes :Dict[str, Geocode] = {}
        with open(init_csv_path, newline="") as csvfile:
            # Delimiter is \t instead of , because google spreadsheets were
            # exporting lat,lng with commas, leading to an invalid number of
            # columns per row :(
            rows = csv.reader(csvfile, delimiter="\t")
            for row in rows:
                # Some admin_ids are not set (or set to "TBD") which can't parse
                # nicely, default to 0 for those.
                try:
                    admin_id = float(row[18])
                except ValueError:
                    admin_id = 0
                geocode = Geocode(float(row[10]), float(row[11]), row[12], row[17], admin_id)
                self.geocodes[row[8].lower()] = geocode
        logging.info("Loaded %d geocodes from %s", len(self.geocodes), init_csv_path)
        

    def Geocode(self, city :str="", province :str="", country :str="") -> Geocode:
        """Geocode matches the given locations to their Geocode information
        
        At least one of city, province, country must be set.

        Returns:
            None if no exact match were found.
        """
        key = f"{city};{province};{country}".lower()
        return self.geocodes.get(key)