## File Descriptions

### `full-data.json`
File generated while retrieving information from Sheets, used as base to generate other files.<br> 
Currently: only has data from sheets, but will be a mix of JHU data for the U.S. and Line List data for the rest of the globe.<br>
To maintain format JHU data is split into individual lines and added to the full data.<br>

### `dailies.geojson`
Generated from `full-data.json`<br>
This is the data file used for [COVID-19 map](https://www.healthmap.org/covid-19/). Includes 1 entry per lat/long combination per week, each entry has total count and number of new cases.<br>

### `jhu_US_timeseries.csv`
data Fetched from [JHU repo](https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv). 

### `healthmap.covid19-data.json/csv`
Copy (and reformat to csv) of `full-data.json` for FM Global S3 Bucket. 

