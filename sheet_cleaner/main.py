'''
Run all sheet cleaning scripts.
'''
testing = False

import argparse
import configparser
import logging
import os
import shutil
import time
from datetime import datetime

import pandas as pd

from geocoding import csv_geocoder
from functions import get_GoogleSheets, values2dataframe, get_trailing_spaces, get_NA_errors, generate_error_tables 


parser = argparse.ArgumentParser(
    description='Cleanup sheet and output generation script')
parser.add_argument('-c', '--config_file', type=str, default="CONFIG",
                    help='Path to the config file')
parser.add_argument('--sleep_time_sec', type=int, default=30,
                    help='Sleep time between various fixes (to be removed)')
parser.add_argument('-p', '--push_to_git', default=False, const=True, action="store_const", dest='push_to_git',
                    help='Whether to push to the git repo specified in the config')

def main():
    args = parser.parse_args()
    config = configparser.ConfigParser()
    config.optionxform=str # to preserve case
    config.read(args.config_file) 
    logging.basicConfig(filename='cleanup.log', level=logging.INFO)
    

    sheets = get_GoogleSheets(config)
    for_github = []

    # Load geocoder early so that invalid tsv paths errors are caught early on.
    geocoder = csv_geocoder.CSVGeocoder(config['GEOCODING'].get('TSV_PATH'))
    for s in sheets:
        logging.info("Processing sheet %s", s.name)

        ### Clean Private Sheet Entries. ###
        # note : private sheet gets updated on the fly and redownloaded to ensure continuity between fixes (granted its slower).
        
        range_ = f'{s.name}!A:AG'
        data = values2dataframe(s.read_values(range_))

        # Trailing Spaces
        trailing = get_trailing_spaces(data)
        if len(trailing) > 0:
            logging.info('fixing %d trailing whitespace', len(trailing))
            s.fix_cells(trailing)
            data = values2dataframe(s.read_values(range_))
            time.sleep(args.sleep_time_sec)

        # fix N/A => NA
        na_errors = get_NA_errors(data)
        if len(na_errors) > 0:
            logging.info('fixing %d N/A -> NA', len(na_errors))
            s.fix_cells(na_errors)
            data   = values2dataframe(s.read_values(range_))
            time.sleep(args.sleep_time_sec)

        # Regex fixes
        fixable, non_fixable = generate_error_tables(data)
        if len(fixable) > 0:
            logging.info('fixing %d regexps', len(fixable))
            s.fix_cells(fixable)
            data = values2dataframe(s.read_values(range_))
            time.sleep(args.sleep_time_sec)

        
        clean = data[~data.ID.isin(non_fixable.ID)]
        clean = clean.drop('row', axis=1)
        clean.sort_values(by='ID')
        s.data = clean
        non_fixable = non_fixable.sort_values(by='ID')
        

        # Save error_reports
        # These are separated by Sheet.
        logging.info('Saving error reports')
        directory   = config['FILES']['ERRORS']
        file_name   = f'{s.name}.error-report.csv'
        error_file  = os.path.join(directory, file_name)
        non_fixable.to_csv(error_file, index=False, header=True)
        for_github.append(error_file)

        
    # Combine data from all sheets into a single datafile
    # + generate IDs
    all_data = []
    for s in sheets:
        data = s.data
        data['ID'] = s.ID + "-" + pd.Series(range(1, len(data)+1)).astype(str)
        all_data.append(data)
    
    all_data = pd.concat(all_data, ignore_index=True)
    all_data = all_data.sort_values(by='ID')

    # Fill geo columns.
    geocode_matched = 0
    for i, row in all_data.iterrows():
        geocode = geocoder.Geocode(row.city, row.province, row.country)
        if not geocode:
            continue
        geocode_matched += 1
        all_data.at[i, 'latitude'] = geocode.lat
        all_data.at[i, 'longitude'] = geocode.lng
        all_data.at[i, 'geo_resolution'] = geocode.geo_resolution
        all_data.at[i, 'location'] = geocode.location
        all_data.at[i, 'admin3'] = geocode.admin3
        all_data.at[i, 'admin2'] = geocode.admin2
        all_data.at[i, 'admin1'] = geocode.admin1
        all_data.at[i, 'admin_id'] = geocode.admin_id
        all_data.at[i, 'country_new'] = geocode.country_new
    logging.info("Geocode matched %d/%d", geocode_matched, len(all_data))
    # Reorganize csv columns so that they are in the same order as when we
    # used to have those geolocation within the spreadsheet.
    # This is to avoid breaking latestdata.csv consumers.
    all_data = all_data[["ID","age","sex","city","province","country","latitude","longitude","geo_resolution","date_onset_symptoms","date_admission_hospital","date_confirmation","symptoms","lives_in_Wuhan","travel_history_dates","travel_history_location","reported_market_exposure","additional_information","chronic_disease_binary","chronic_disease","source","sequence_available","outcome","date_death_or_discharge","notes_for_discussion","location","admin3","admin2","admin1","country_new","admin_id","data_moderator_initials","travel_history_binary"]]
    
    #drop_invalid_ids = []
    #for i, row in all_data.iterrows():
    #    if row['ID'].str.match('

    # save
    logging.info("Saving files to disk")
    dt = datetime.now().strftime('%Y-%m-%dT%H%M%S')
    file_name   = config['FILES']['DATA'].replace('TIMESTAMP', dt)
    latest_name = os.path.join(config['FILES']['LATEST'], 'latestdata.csv')
    all_data.to_csv(file_name, index=False)
    all_data.to_csv(latest_name, index=False)
    logging.info("Wrote %s, %s", file_name, latest_name)

    if args.push_to_git:
        logging.info("Pushing to github")
        # Create script for uploading to github
        for_github.extend([file_name, latest_name])
        script  = 'set -e\n'
        script += 'cd {}\n'.format(config['GIT']['REPO'])
        script += 'git pull origin master\n'
        
        for g in for_github:
            script += f'git add {g}\n'
        script += 'git commit -m "data update"\n'
        script += 'git push origin master\n'
        script += f'cd {os.getcwd()}\n'
        print(script)
        os.system(script)


if __name__ == '__main__':
    main()
