'''
Library for Google Sheets functions. 
'''
import configparser
import os
import pickle
import logging
import re
import math
from string import ascii_uppercase 

from typing import Dict, List

import pandas as pd
import numpy as np 
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2 import service_account

from constants import rgx_age, rgx_sex, rgx_country, rgx_date, rgx_lives_in_wuhan, date_columns
from google.auth.transport.requests import Request
from objects import GoogleSheet


def get_GoogleSheets(config: configparser.ConfigParser) -> list:
    '''
    Loop through different sheets in config file, and init objects.

    Args : 
        config (ConfigParser) : configuration

    Returns :
        values (list) : list of GoogleSheet objects.
    '''
    # Fetch all sections in config referring to sheets.
    sheets = []
    pattern = r'^SHEET\d*$'
    sections = config.sections()
    for s in sections:
        if re.match(pattern, s):
            id_ = config[s]['ID']
            sid = config[s]['SID']
            name = config[s]['NAME']
            googlesheet = GoogleSheet(sid, name, id_, 
                    config['SHEETS'].get("TOKEN"),
                    config['SHEETS'].get('CREDENTIALS'),
                    config['SHEETS'].get('IS_SERVICE_ACCOUNT'))

            sheets.append(googlesheet)
    return sheets

    

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
    data  = pd.DataFrame(data=data, columns=columns)
    data = data.astype({
        "age": "string",
        "sex": "string",
        "city": "string",
        "province": "string",
        "country": "string",
        "date_onset_symptoms": "string",
        "date_admission_hospital": "string",
        "date_confirmation": "string",
        "symptoms": "string",
        # Should be bool but lot of info is on business trips to Wuhan etc, better kept as a string.
        "lives_in_Wuhan": "string",
        "travel_history_dates": "string",
        "travel_history_location": "string",
        "additional_information": "string",
        "chronic_disease_binary": "bool",
        "chronic_disease": "string",
        "source": "string",
        "outcome": "string",
        "date_death_or_discharge": "string",
        "notes_for_discussion": "string",
        "travel_history_binary": "bool",
    })
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
        return ascii_uppercase[num]
    elif 26 <= num <= 51:
        return 'A{}'.format(ascii_uppercase[num%26])
    elif 52 <= num <= 77:
        return 'B{}'.format(ascii_uppercase[num%26])
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
    
    error_table = pd.DataFrame(columns=['row', 'column', 'value', 'fix'])
    for c in df.columns:
        if c == 'row':
            continue
        else:
            try:
                stripped = df[c].str.strip()
            except AttributeError as ae:
                print("column:", c)
                raise ae
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

def generate_error_tables(data):
    '''
    Generate table for fields that don't pass the rgex tests. 
    For easy fixes (e.g. spacing) we can do it automatically, for tricker ones we save the table (fixed ones are omitted in error_report)
    '''
    table = pd.DataFrame(columns=['row', 'ID', 'value'])
    table = ErrorTest(data, ['age'], rgx_age, table)
    table = ErrorTest(data, ['sex'], rgx_sex, table)
    table = ErrorTest(data, ['city', 'province', 'country'], rgx_country, table)
    table = ErrorTest(data, date_columns, rgx_date, table)
    table = ErrorTest(data, ['lives_in_Wuhan'], rgx_lives_in_wuhan, table)
    fixable_errors = pd.DataFrame(columns=['row', 'ID', 'column', 'value', 'fix'])

    not_fixable = []
    for _, r in table.iterrows():
        row = r.copy()
        fix = False
        col = row['column']
        if col == 'age':
            test = bool(re.match(rgx_age, row['value'].replace(' ', '')))
            if test:
                fix = row['value'].replace(' ', '')

        elif col  == 'country':
            pass

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



def duplicate_rows_per_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Duplicate rows based on the integer number in 'col' if > 0.
    Changes the data frame in place, returned col will only contain nan."""
    for i, row in df.iterrows():
        if math.isnan(row[col]) or row[col] <= 0:
            continue
        num = int(row[col])
        row[col] = np.nan
        df.at[i, 'aggr'] = np.nan
        df = df.append([row] * num, ignore_index=True)
    return df