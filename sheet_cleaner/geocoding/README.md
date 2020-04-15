# Geocoding of case data

This directory contains an offline geocoder used by the sheet_cleaner script.

The list of geocodes is loaded in memory from the `geo_admin.tsv` file.

Tab-separated file format is used to avoid potential pitfalls with commas in CSVs and addresses/longitude/latitude,etc.

## Adding missing geocodes

With each run of the sheet_cleaner script, the top 10 missing geocodes are logged in the `cleanup.log` file locally.
You can go through that file and look for geocodes yourself, then run the add_geocode.py script to add it to the `geo_admin.tsv` file and them push it to github.

```console
python3 add_geocode.py --country=France --city="Lyon" --province="Auvergne-Rhône-Alpes" --lat=0.1 --lng=0.2 --location="loc" --admin1="adm1" --admin2="adm2" --admin3="adm3"
```

Note that case doesn't matter for `country`, `city` and `province`, the rest of the fields are going to be taken as is. Only `country` is mandatory.
If `lat` and `lng` are missing then online geocoding will be attempted using AcrGIS.