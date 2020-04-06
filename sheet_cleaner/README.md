# Spreadsheet management scripts.

This directory contains Google spreadsheets management scripts that setup new sheets, cleanup existing ones and merge them all to csv/s3 on a daily basis.

Note: this is a short-term solution until a more robust solution is worked on.

## Development

One time setup:

Install Python 3.6+, then (feel free to use a [virtual env](https://docs.python.org/3/library/venv.html) if you prefer):

```
pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

We could also provide a requirements.txt for pip to consume, contributions welcome.

## Workflow

TL;DR:
  - The sheets only contain columns that the contributors are supposed to fill in (reduces cognitive burden and increases sheet performance).
  - Basic validation is added to columns in the spreadsheet programmatically (can be retrofitted/applied to existing spreadsheets).
  - Two scripts take care of splitting the sheets when necessary and creating the csv output/push to s3 bucket to share with consumers.
  - Error reports are created in a form that's easily actionable. (Perhaps current state is good enough, not enough experience/data to judge yet).

### Generating new sheets

A script is made available to report on sheets with a high number of rows (exact number TBD, should be configurable).
This script can be run periodically automatically on a raspberry pi/VPS/AWS or some members can add it to their crontab and it can send an alert (email/better: slack) (integration through [monit](https://mmonit.com/monit/) is fairly easy for that if we want to go this way).

```
./check_rows.py --config=path/to/config
```

_Config contains all the sheet ids/continent info and potential mail/slack alert config as well._

When an alert is received, new sheets can be generated for a given location (continent seems reasonable) and those new sheets are automatically shared with the contributors for that location.

_To make sharing of sheets easier and consistent: move contributors to a google group if that's not already the case._

Spreadsheets created share a common format (same columns, same sharing settings).

Latest spreadsheet link for each location is made available on github so that contributors can easily get to it (see if we can automate this or if we want to have a mandatory peer review of it before pushing it to the repo/s3).

### Post-processing

A post-processing script is added to produce the final csv that is exported to github. This script does the geocoding (offline as it was done in sheets, this is mostly to avoid expensive VLOOKUPs in sheets) and also allows exporting to S3.

```
./generate_csv.py --config=path/to/config --export_to_s3=some/s3/bucket/path
```

This script reads through all the sheets present in the [config file](https://github.com/open-covid-data/mvp-notes-and-ideas/blob/master/sheet_cleaner/CONFIG) and produces the final csv and error reports.

### Priorities (high to low)

1. Low-hanging fruits
   1. remove unused columns
   1. Move contributors to google groups/unify sharing
1. Move geocoding logic out of the spreasheets
   1. Build offline geocoder
   1. Call geocoder from script generating the output csv.
1. Build script to split sheets and associated logic.