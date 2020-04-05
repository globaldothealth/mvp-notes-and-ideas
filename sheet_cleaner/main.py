'''
Run all sheet cleaning scripts.
'''
testing = False

import configparser
import os
import shutil
import time
from datetime import datetime

from constants import *
from functions import *

configfile = '/home/tbrewer/nCoV2019/code/sheet_cleaner/.CONFIG'
config = configparser.ConfigParser()
config.read(configfile)
sleeptime = 30

def main():
    sheets = get_GoogleSheets(config)
    for_github = [] 
    for s in sheets:
        if s.name is None:
            continue 

        r  = insert_ids(s, config)
        time.sleep(sleeptime)
        
        rs = update_lat_long_columns(s, config)
        time.sleep(sleeptime)
        
        r  = update_admin_columns(s, config)
        time.sleep(sleeptime)

      
        ### Clean Private Sheet Entries. ###
        # note : private sheet gets updated on the fly and redownloaded to ensure continuity between fixes (granted its slower).
        range_      = f'{s.name}!A:AG'
        values      = read_values(s.spreadsheetid, range_, config)
        columns     = s.columns
        column_dict = {c:index2A1(i) for i,c in enumerate(columns)} # to get A1 notation, doing it now to ensure proper order
        data        = values2dataframe(values)

        # Trailing Spaces
        trailing = get_trailing_spaces(data)
        if len(trailing) > 0:
            fix_cells(s.spreadsheetid, s.name, trailing, column_dict, config)
            values = read_values(s.spreadsheetid, range_, config)
            data   = values2dataframe(values)
            time.sleep(sleeptime)

        # fix N/A => NA
        na_errors = get_NA_errors(data)
        if len(na_errors) > 0:
            fix_cells(s.spreadsheetid, s.name, na_errors, column_dict, config)
            values = read_values(s.spreadsheetid, range_, config)
            data   = values2dataframe(values)
            time.sleep(sleeptime)

         # Regex fixes
        fixable, non_fixable = generate_error_tables(data)
        if len(fixable) > 0:
            fix_cells(s.spreadsheetid, s.name, fixable, column_dict, config)
            values = read_values(s.spreadsheetid, range_, config)
            data   = values2dataframe(values)
            time.sleep(sleeptime)

        
        clean = data[~data.ID.isin(non_fixable.ID)]
        clean = clean.drop('row', axis=1)
        clean.sort_values(by='ID')
        s.data = clean
        non_fixable = non_fixable.sort_values(by='ID')
        

        # Save error_reports
        # These are separated by Sheet.
        directory   = config['FILES']['ERRORS']
        file_name   = f'{s.name}.error-report.csv'
        error_file  = os.path.join(directory, file_name)
        non_fixable.to_csv(error_file, index=False, header=True)
        for_github.append(error_file)

        
    # Combine data from all sheets into a single datafile:
    all_data = []
    for s in sheets:
        data = s.data
        
        if s.name == 'outside_Hubei':
            data['ID'] = data['ID'].apply(lambda x : f'000-1-{x}')
        
        elif s.name  == 'Hubei':
            data['ID'] = data['ID'].apply(lambda x: f'000-2-{x}')

        all_data.append(data)
    
    all_data = pd.concat(all_data, ignore_index=True)
    all_data = all_data.sort_values(by='ID')
    
    #drop_invalid_ids = []
    #for i, row in all_data.iterrows():
    #    if row['ID'].str.match('

    # save
    dt = datetime.now().strftime('%Y-%m-%dT%H%M%S')
    file_name   = config['FILES']['DATA'].replace('TIMESTAMP', dt)
    latest_name = os.path.join(config['FILES']['LATEST'], 'latestdata.csv')
    all_data.to_csv(file_name, index=False) 
    all_data.to_csv(latest_name, index=False)    

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
    try:
        main()
    except Exception as E:
        with open(config['FILES']['LOG'], 'a') as F:   
            dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = f'{dt} {E}\n'
            F.write(message)
        raise E
