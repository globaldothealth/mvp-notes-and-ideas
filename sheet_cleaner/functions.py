'''
Library for Google Sheets functions. 
'''
import configparser
import os
import pickle
import re

from typing import Dict, List

import pandas as pd
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2 import service_account

# TODO: remove * imports and only import what's necessary.
from constants import *
from google.auth.transport.requests import Request


class GoogleSheet(object):
    '''
    Simple object to help added when we started getting multiple sheets.
    Attributes:
    :spreadsheetid:-> str, Google Spreadsheet ID (from url).
    :name: -> list or str, sheet name (list when multiple sheets in 1 spreadsheet).
    :ID: -> str, code for ID column in sheets (specific to region).
    :config: -> Dict, config dictionary as parsed at startup.
    '''

    def __init__(self, spreadsheetid, name, id, config):
        self.spreadsheetid = spreadsheetid
        self.name = name
        self.ID = id
        config = config
        
        r = f'{self.name}!A1:AG1'
        self.columns = read_values(self.spreadsheetid, r, config)[0]
        for i, c in enumerate(self.columns):

            # 'country' column name had disappeared
            if c.strip() == '' and self.columns[i-1] == 'province':
                self.columns[i] = 'country'

            # some white space gets added unoticed sometimes 
            self.columns[i] = c.strip()
        

def get_GoogleSheets(config: configparser.ConfigParser) -> list:
    '''
    Loop through different sheets in config file, and init objects.

    Args : 
        config (ConfigParser) : configuration

    Returns :
        values (list) : list of GoogleSheet objects.
    '''
    # fetch for original sheet
    sheet0 = config['ORIGINAL_SHEET']
    name1 = sheet0.get('NAME1')
    name2 = sheet0.get('NAME2')
    sid = sheet0.get('SID')
    ID  = sheet0.get('ID')
    s1 = GoogleSheet(sid, name1, ID, config)
    sheets = [s1]
    if name2:
        s2 = GoogleSheet(sid, name2, ID, config)
        sheets.append(s2)

    # Fetch for Regional Sheets. (follow pattern Sheet1, Sheet2, ... )
    pattern = r'^SHEET\d*$'
    sections = config.sections()
    for s in sections:
        if re.match(pattern, s):
            id_ = config[s]['ID']
            sid = config[s]['SID']
            name = config[s]['NAME']
            googlesheet = GoogleSheet(sid, name, id_, config)
            sheets.append(googlesheet)
            
    return sheets

def read_values(sheetid: str, range_: str, config: configparser.ConfigParser) -> list:
    '''
    Read values from Sheet and return as is
    Args : 
        sheetid (str) : spreadsheet id (from url).
        range_ (str)  : range to read in A1 notation.
        config (ConfigParser) : configuration
    
    Returns : 
        list: values from range_

    TODO: reconfigure as Sheet object method. 
    '''
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    creds = get_creds(config, SCOPES)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet   = service.spreadsheets()
    values  = sheet.values().get(spreadsheetId=sheetid, range=range_).execute().get('values', [])

    if not values:
        raise ValueError('Sheet data not found')
    else:
        return values

def get_creds(config: Dict, scopes: List[str]):
    """Gets credentials based on the given config file and scopes.
    
    Saves the pickled creds to a file for later re-use.
    """
    creds = None
    TOKEN  = config['SHEETS'].get('TOKEN')
    CREDENTIALS = config['SHEETS'].get('CREDENTIALS')
    if os.path.exists(TOKEN): 
        with open(TOKEN, 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if config['SHEETS'].get('IS_SERVICE_ACCOUNT'):
                creds = service_account.Credentials.from_service_account_file(
                    CREDENTIALS, scopes=scopes)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS, scopes)
                creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(TOKEN, 'wb') as token:
            pickle.dump(creds, token)
    return creds
     
    
def insert_values(sheetid: str, body: dict, config: configparser.ConfigParser, **kwargs) -> dict:
    '''
    Insert values into spreadsheet.
    Args : 
        sheetid (str) : spreadsheet id (from url).
        body (dict): body as defined by Googlespreadhseet API. 
        config (ConfigParser): configuration

    Kwargs:
        inputoption (str) : value input option, default='USER_ENTERED'
    
    Returns : 
        response (dict) : response from upload (no values)

    Example body:
    body = {
        'range': 'SheetName!A1:A3',
        'majorDimension': 'ROWS',
        'values': [[1], [2], [3]]
    }

    TODO: reconfigure as Sheet object method. 
    '''
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    INPUTOPTION = kwargs['inputoption'] if 'inputoption' in kwargs.keys() else 'USER_ENTERED'
    creds = get_creds(config, SCOPES)

    # Call the Sheets API
    service = build('sheets', 'v4', credentials=creds)
    sheet   = service.spreadsheets()
    request = sheet.values().update(spreadsheetId=sheetid,
                                    range=body['range'],
                                    body=body, 
                                    valueInputOption=INPUTOPTION)
    response = request.execute()
    return response

def values2dataframe(values: list) -> pd.DataFrame:
    '''
    Convert raw values as retrieved from read_values to a pandas dataframe.
    Adds empty values so that all lists have the same length. 
    
    Args:
        values (list) : list of lists with values from read_values

    Returns:
        data (pd.DataFrame): same data with stripped column names.
    
    '''
    columns = values[0] 
    for i, c in enumerate(columns):

        # added when column name disappeared.
        if c.strip() == '' and columns[i-1] == 'province':
            columns[i] = 'country'

    ncols   = len(columns)
    data    = values[1:]
    for d in data:
        if len(d) < ncols:
            extension = ['']*(ncols-len(d))
            d.extend(extension)
    data    = pd.DataFrame(data=data, columns=columns)
    data['row'] = list(range(2, len(data)+2)) # keeping row number (+1 for 1 indexing +1 for column headers in sheet)
    data['row'] = data['row'].astype(str)
        
    # added the strip due to white space getting inputed somehow. 
    return data.rename({c : c.strip() for c in data.columns}, axis=1)

def index2A1(num: int) -> str:
    '''
    Converts column index to A1 notation. 

    Args: 
        num (int) : column index
    Returns :
        A1 notation (str)

    TODO: expand this for any number of columns (recursive function?)
    '''
    if 0 <= num <= 25:
        return alpha[num]
    elif 26 <= num <= 51:
        return 'A{}'.format(alpha[num%26])
    elif 52 <= num <= 77:
        return 'B{}'.format(alpha[num%26])
    else:
        raise ValueError('Could not convert index "{}" to A1 notation'.format(num))
        
def get_trailing_spaces(data: pd.DataFrame) -> pd.DataFrame:
    '''
    Generate error table for trailing whitespaces (front and back).
    Args : 
        data (pd.DataFrame)
    Returns :
        error_table (pd.DataFrame) : table listing cells with errors.
    '''
    df = data.copy()
    
    error_table = pd.DataFrame(columns=['row', 'ID', 'column', 'value', 'fix'])
    for c in df.columns:
        if c == 'row':
            continue
        else:
            stripped = df[c].str.strip()
            invalid_bool = stripped != df[c]
            invalid      = df[invalid_bool][['row', 'ID']].copy()
            invalid['column'] = c
            invalid['value'] = df[c][invalid_bool].copy()
            invalid['fix'] = stripped[invalid_bool]
        error_table = error_table.append(invalid, ignore_index=True, sort=True)        
    return error_table


def get_NA_errors(data: pd.DataFrame) -> pd.DataFrame:
    '''
    Generate error table for mispelled NA values.  
    We chose to write them as "NA", and so far we only
    fix = replace "N/A" with "NA"
    return error_table[row, ID, column, value, fix
    '''
    df = data.copy()
    table = pd.DataFrame(columns=['row', 'ID', 'column', 'value', 'fix'])
    for c in df.columns:
        if c == 'row':
            continue
        else:
            test   = df[c].str.match('N/A')
            errors = df[test][['row', 'ID']]
            errors['column'] = c
            errors['value'] = df[test][c]
            errors['fix'] = df[test][c].replace('N/A', 'NA')
            table = table.append(errors, ignore_index=True, sort=True)
    return table

def ErrorTest(data, columns, rgx, table):
    '''
    Test a regex pattern on passed columns, generate error table
    for things that did not pass the test. 
    Note this does not generate the fix.  We do this after.
    '''
    df = data.copy()
    for c in columns:
        test = df[c].str.match(rgx)
        invalid = df[~test][['row', "ID"]].copy()
        invalid['column'] = c
        invalid['value']  = df[~test][c]
        table = table.append(invalid, ignore_index=True, sort=False)
    return table

def fix_cells(sheetid, sheetname, error_table, column_dict, config):
    '''
    Fix specific cells on the private sheet, based on error table. 
    Error table also needs to provide the "fix" column which is what 
    we are replacing the current value with. 
    :column_dict: map from 'column_name' to A1 notation. 
    '''
    assert 'fix' in error_table.columns
    assert 'value' in error_table.columns 
    
    fixed = 0
    for _, error in error_table.iterrows():      
        row       = error['row']
        a1 = column_dict[error['column']] + row
        range_    = '{}!{}'.format(sheetname, a1)
        try:
            fetch = read_values(sheetid, f'{sheetname}!A{row}', config) # fetch ID to ensure that it is the same.
            assert error['ID'] == fetch[0][0]
            body = {
                'range': range_,
                'majorDimension': 'ROWS',
                'values': [[error['fix']]]
            }
            insert_values(sheetid, body, config)
            fixed += 1
            
        except Exception as E:
            print(error)
            print(fetch)
            raise E
    return fixed


def generate_error_tables(data):
    '''
    Generate table for fields that don't pass the rgex tests. 
    For easy fixes (e.g. spacing) we can do it automatically, for tricker ones we save the table (fixed ones are omitted in error_report)
    '''
    table = pd.DataFrame(columns=['row', 'ID', 'value'])
    table = ErrorTest(data, ['age'], rgx_age, table)
    table = ErrorTest(data, ['sex'], rgx_sex, table)
    table = ErrorTest(data, ['city', 'province', 'country'], rgx_country, table)
    table = ErrorTest(data, ['latitude', 'longitude'], rgx_latlong, table)
    table = ErrorTest(data, ['geo_resolution'], rgx_geo_res, table)
    table = ErrorTest(data, date_columns, rgx_date, table)
    table = ErrorTest(data, ['lives_in_Wuhan'], rgx_lives_in_wuhan, table)
    fixable_errors = pd.DataFrame(columns=['row', 'ID', 'column', 'value', 'fix'])

    not_fixable = []
    for _, r in table.iterrows():
        row = r.copy()
        fix = False
        col = row['column']
        if col == 'sex':
            test = row['value'].lower().strip() in ['male', 'female', '']
            if test:
                fix = row['value'].lower().strip()

        elif col == 'age':
            test = bool(re.match(rgx_age, row['value'].replace(' ', '')))
            if test:
                fix = row['value'].replace(' ', '')

        elif col  == 'country':
            pass

        elif col in ['latitude', 'longitude']:
            pass

        elif col == 'geo_resolution':
            s = row['value']
            test = bool(re.match(rgx_geo_res, s.replace(' ', '')))
            if test:
                fix = s.replace(' ', '')

        elif col in date_columns:
            pass

        elif col == 'lives_in_Wuhan':
            s = row['value']
            test1 = bool(re.match(rgx_lives_in_wuhan, s.lower().strip()))
            test2 = True if s in ['1', '0'] else False
            if test1:
                fix = s.lower().strip()
            elif test2:
                fix = 'yes' if s == '1' else 'no'


        if fix:
            row['fix'] = fix
            fixable_errors = fixable_errors.append(row, ignore_index=True, sort=False)
        else:
            not_fixable.append(r.name)
      
    fixable   = fixable_errors.reset_index(drop=True)
    unfixable = table.loc[not_fixable].copy().reset_index(drop=True)
    
    return [fixable, unfixable]

def insert_ids(Sheet: GoogleSheet, config: configparser.ConfigParser) -> dict:
    '''
    Insert Id numbers for any row that does not have any. 
    ID numbers are sequential, so we do MAX(current) + 1 for each new ID. 
    '''

    # Import columns to assert positions when updating
    print('insert_ids', Sheet.name)
    id_col = alpha[Sheet.columns.index('ID')]
    if 'country' in Sheet.columns:
        country_col = alpha[Sheet.columns.index('country')]
    else:
        country_col = 'F'

    # Import all IDs
    id_range = f'{Sheet.name}!{id_col}:{id_col}'
    IDS = read_values(Sheet.spreadsheetid, id_range, config)[1:]
    
    # Import country column for comparison
    country_range = f'{Sheet.name}!{country_col}:{country_col}'
    countries = read_values(Sheet.spreadsheetid, country_range, config)

    diff = len(countries) - len(IDS)
    #if diff <= 0:
    #    return None

    # Get numerical value of ids in order to get the max. 
    # For old sheets : int(x)
    # For new ones xxx-int(x)
    ids = []
    maxid = -9999
    for I in IDS:
        if len(I) == 1:
            x = I[0]
            if '-' in x:
                num = x.split('-')[1]
            else:
                num = x
            num = int(num)
            ids.append(num)
            if num > maxid :
                maxid = num
        else:
            ids.append(None)

    # Fill in null values
    for i, num in enumerate(ids):
        if num is None:
            ids[i] = maxid + 1
            maxid += 1

    
    # append new numbers for difference in ids and countries.
    new_ids = []
    while len(new_ids) < diff:
        new_ids.append(maxid + 1)
        maxid += 1
    
    new_ids = ids + new_ids

    # insert new ids : 
    if Sheet.name in ['Hubei', 'outside_Hubei']:
        new_values = [[str(x)] for x in new_ids]
    else:
        new_values =[[f'{Sheet.ID}-{x}'] for x in new_ids]

    start = len(IDS) + 1
    end   = start + len(new_values)
    new_range = f'{Sheet.name}!{id_col}2:{id_col}{end}'
    body = {
        'range': new_range,
        'majorDimension': 'ROWS',
        'values': new_values[:-1]
    }
    return insert_values(Sheet.spreadsheetid, body, config, inputoption='RAW')
