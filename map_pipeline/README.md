# Map Scripts

### `pipeline.py`
Main function for getting Sheet data for the [COVID-19 map](https://www.healthmap.org/covid-19/).

### `scrape_total_count.py`
Function to get total confirmed cases from [here]('https://docs.google.com/spreadsheets/d/e/2PACX-1vR30F8lYP3jG7YOq8es0PBpJIE5yvRVZffOyaqC0GgMBN6yt0Q-NI8pxS7hd1F9dYXnowSC6zpZmW9D/pubhtml/sheet?headers=false&gid=0&range=A1:I183')

### `get_WHO_data.py`
Request data from WHO RestAPI for count by country side bar. 

###  `pipeline.jhu_integration.py`
To replace pipeline.py, uses JHU data for the United states, and Line List data for the rest of the globe. 

### `functions.py`
Functions (+1 object) used in `pipeline.py`

### `s3push.py`
Script to format and push data to S3 bucket for FM-Global