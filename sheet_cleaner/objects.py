'''
GoogleSheet Object
'''
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import pickle
import os
import re

class GoogleSheet(object):
    '''
    Simple object to help added when we started getting multiple sheets.
    Attributes:
    :spreadsheetid:-> str, Google Spreadsheet ID (from url).
    :name: -> list or str, sheet name (list when multiple sheets in 1 spreadsheet).
    :ID: -> str, code for ID column in sheets (specific to region).
    '''

    def __init__(self, spreadsheetid, name, reference_id, token, credentials, is_service_account):
        self.spreadsheetid = spreadsheetid 
        self.name = name
        self.ID = reference_id
        self.token = token
        self.credentials = credentials
        self.is_service_account = is_service_account
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

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
                  'https://www.googleapis.com/auth/drive']
        
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
                if self.is_service_account:
                    creds = service_account.Credentials.from_service_account_file(
                        CREDENTIALS, scopes=SCOPES)
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
    
        service = build('sheets', 'v4', credentials=self.Auth(), cache_discovery=False)
        sheet = service.spreadsheets()
        values  = sheet.values().get(spreadsheetId=self.spreadsheetid, range=range_).execute().get('values', [])	
        if not values:
            raise ValueError("Sheet data not found")
        else:
          return values

    def insert_values(self, body, **kwargs):

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
        columns = self.read_values(r)[0]
        for i, c in enumerate(columns):
                # 'country' column had disappeared
                if c.strip() == '' and columns[i-1] == 'province':
                    columns[i] = 'country'

                # some white space gets added unoticed sometimes 
                columns[i] = c.strip()
        return columns
        
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
        for _, error in error_table.iterrows():    
            row       = error['row']
            a1 = self.column_dict[error['column']] + row 
            range_    = '{}!{}'.format(self.name, a1) 
            
            fetch = self.read_values(f'{self.name}!A{row}') # fetch ID to ensure that it is the same.
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
    
        country_range = f'{self.name}!{country_col}:{country_col}'
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


    def new_sheet(self, config, config_file_name):
        '''
        Make new spreadsheet as copy of itself (columns, no data). 
        + Add new sheet info to config file
        '''

        service = build('sheets', 'v4', credentials=self.Auth(), cache_discovery=False)
        request = service.spreadsheets().get(spreadsheetId=self.spreadsheetid, fields='properties.title')
        response = request.execute()
        title = response['properties']['title']
        spreadsheet = {
            'properties': {'title': title},
            'sheets': {
                'properties': {
                    'sheetId': 0, 
                    'title': self.name
                },
                'data': { 
                    'startRow' : 0,
                    'startColumn' : 0,
                    'rowData': {
                        'values': [{'userEnteredValue': {'stringValue': c}} for c in self.columns]
                    }
                }
            }
        }
        spreadsheet = service.spreadsheets().create(body=spreadsheet,
                                    fields='spreadsheetId,sheets').execute()

        sections = [s for s in config.sections() if s not in ['SHEET0', 'SHEET1'] and re.match(r'^SHEET\d*$', s)] # skip hubei, outside 
        sheet_numbers = [int(re.search(r'SHEET(\d*)', s).group(1)) for s in sections] 
        sheet_IDs = [int(config[s]['ID']) for s in sections]
        SHEET = 'SHEET' + str(max(sheet_numbers) + 1)
        new_ID  = str(max(sheet_IDs) + 1).zfill(3)
    
        config.add_section(SHEET)
        config[SHEET]['NAME'] = self.name
        config[SHEET]['SID'] = spreadsheet['spreadsheetId']
        config[SHEET]['ID'] = new_ID
        with open(config_file_name, 'w') as F:
            config.write(F)
            
        new_sheet = GoogleSheet(spreadsheet['spreadsheetId'], self.name, new_ID, self.token, self.credentials, self.is_service_account)     
        new_sheet.columns = self.columns.copy()
        return new_sheet


class Template(GoogleSheet):
    def __init__(self, spreadsheetid, token, credentials, is_service_account): 
        self.spreadsheetid = spreadsheetid
        self.token = token
        self.credentials = credentials
        self.is_service_account = is_service_account


    def copy(self, copy_title, emailto):
        from apiclient import errors
        """Copy an existing file.

        Args:
            service: Drive API service instance.
            origin_file_id: ID of the origin file to copy.
            copy_title: Title of the copy.

        Returns:
        The copied file if successful, None otherwise.
         """
        service =  build('drive', 'v3', credentials=self.Auth(), cache_discovery=False)
        copied_file = {'name': copy_title, 'title': copy_title, 'writersCanShare': True}
        request = service.files().copy(fileId=self.spreadsheetid, body=copied_file)
        create_response = request.execute()
        
        # {'kind': 'drive#file', 
        #  'id': '1tvcFK22waQCl-uXCb_ZVTBOo94ePpknYcWXvXCM727I', 
        #  'name': 'Copy of Open COVID-19 Sheet Template', 
        #  'mimeType': 'application/vnd.google-apps.spreadsheet'}

 
        permissions = {
            "type": "group", 
            "role": "writer",
            "emailAddress": emailto 
        }
#        permissions = {
#                "type": 'group',
#                "role": 'writer',
#                "emailAddress": "covid19_spreadsheets@googlegroups.com"
#        }
        request = service.permissions().create(
            fileId=create_response['id'],
            body=permissions,
            fields='id' 
        )
        permissions_response = request.execute()
        name_response = self.rename_sheet(create_response['id'],
                            copy_title)

        return {'create': create_response, 
                'permissions': permissions_response,
                'name' : name_response}

    def rename_sheet(self, spreadsheetId, new_name, sheet_id=0):
        
        body = {
            'requests': [
                {
                    'updateSheetProperties': {
                        "properties": {
                            "sheetId": sheet_id,
                            "title": new_name
                        },
                        "fields": "title"
                    }
                }
            ]
        }

        service = build('sheets', 'v4', credentials=self.Auth(),
                        cache_discovery=False).spreadsheets()
        request = service.batchUpdate(spreadsheetId=spreadsheetId, body=body)
        return request.execute()
