'''
GoogleSheet Object
'''
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os


class GoogleSheet(object):
    '''
    Simple object to help added when we started getting multiple sheets.
    Attributes:
    :spreadsheetid:-> str, Google Spreadsheet ID (from url).
    :name: -> list or str, sheet name (list when multiple sheets in 1 spreadsheet).
    :ID: -> str, code for ID column in sheets (specific to region).
    '''

    def __init__(self, spreadsheetid, name, reference_id, token, credentials):
        self.spreadsheetid = spreadsheetid 
        self.name = name
        self.ID = reference_id
        self.token = token
        self.credentials = credentials
        self.columns = self.get_columns()
        self.column_dict = {c:self.index2A1(i) for i,c in enumerate(self.columns)}


    def Auth(self):
        '''
        Sets credentials for sheet.	
	Args:
          token (str) : path to pickled credentials. 
          credentials (str): Path Google API credentials (json).
          scopes (str) scopes associated to credentials.
        '''

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        TOKEN  = self.token 
        CREDENTIALS = self.credentials 

        creds = None
        if os.path.exists(TOKEN):
            with open(TOKEN, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                             CREDENTIALS, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(TOKEN, 'wb') as token:
                pickle.dump(creds, token)

        return creds
	

    def read_values(self, range_):
        '''
        Read values from Sheet and return as is
        Args : 
            range_ (str)  : range to read in A1 notation.
    
        Returns : 
            list: values from range_

    	'''
    
        service = build('sheets', 'v4', credentials=self.Auth())
        sheet = service.spreadsheets()
        values  = sheet.values().get(spreadsheetId=self.spreadsheetid, range=range_).execute().get('values', [])	
        if not values:
            raise ValueError("Sheet data not found")
        else:
          return values

    def insert_values(body, **kwargs):

        inputoption = kwargs.get('inputoption', 'USER_ENTERED')

        # Call the Sheets API
        service = build('sheets', 'v4', credentials = self.Auth())
        sheet   = service.spreadsheets()
        request = sheet.values().update(spreadsheetId=self.spreadsheetid,
                                    range=body['range'],
                                    body=body,
                                    valueInputOption=inputoption)
        response = request.execute()
        return response


    def get_columns(self):
        r = f'{self.name}!A1:AG1'
        self.columns = self.read_values(r)[0]
        for i, c in enumerate(self.columns):
                # 'country' column had disappeared
                if c.strip() == '' and self.columns[i-1] == 'province':
                    self.columns[i] = 'country'

                # some white space gets added unoticed sometimes 
                self.columns[i] = c.strip()


    def fix_cells(self, error_table):
        ''' 
        Fix specific cells on the private sheet, based on error table. 
        Error table also needs to provide the "fix" column which is what 
        we are replacing the current value with. 
        :column_dict: map from 'column_name' to A1 notation. 
        '''
        assert 'fix' in error_table.columns
        assert 'value' in error_table.columns 
           
        fixed = 0 
        for i,error in error_table.iterrows():    
            row       = error['row']
            a1 = self.column_dict[error['column']] + row 
            range_    = '{}!{}'.format(self.sheetname, a1) 
            
            fetch = self.read_values(f'{sheetname}!A{row}') # fetch ID to ensure that it is the same.
            assert error['ID'] == fetch[0][0]
            body = { 
                'range': range_,
                'majorDimension': 'ROWS',
                'values': [[error['fix']]]
            }   
            self.insert_values(body)
            fixed += 1
        
        return fixed

    def insert_ids(self):
        '''
        Insert Id numbers for any row that does not have any. 
        ID numbers are sequential, so we do MAX(current) + 1 for each new ID. 
        '''
    
        id_col = self.index2A1(self.columns.index('ID'))
        if 'country' in self.columns:
            country_col = self.index2A1(self.columns.index('country'))

        else:
            country_col = 'F'
    
        id_range = f'{self.name}!{id_col}:{id_col}'
        IDS = self.read_values(id_range)[1:]
    
        country_range = f'{Sheet.name}!{country_col}:{country_col}'
        countries = self.read_values(country_range)
    
        diff = len(countries) - len(IDS)
        
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
        if self.name in ['Hubei', 'outside_Hubei']:
            new_values = [[str(x)] for x in new_ids]
        else:
            new_values =[[f'{self.ID}-{x}'] for x in new_ids]
    
        start = len(IDS) + 1
        end   = start + len(new_values)
        new_range = f'{self.name}!{id_col}2:{id_col}{end}'
        body = {
            'range': new_range,
            'majorDimension': 'ROWS',
            'values': new_values[:-1]
        }
        return self.insert_values(body, inputoption='RAW')


    def index2A1(self, num: int) -> str:
        '''
        Converts column index to A1 notation. 
    
        Args: 
            num (int) : column index
        Returns :
            A1 notation (str)
    
        '''
        alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        if 0 <= num <= 25:
            return alpha[num]
        elif 26 <= num <= 51:
            return 'A{}'.format(alpha[num%26])
        elif 52 <= num <= 77:
            return 'B{}'.format(alpha[num%26])
        else:
            raise ValueError('Could not convert index "{}" to A1 notation'.format(num))
