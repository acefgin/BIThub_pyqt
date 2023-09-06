from __future__ import print_function

import os.path, gspread

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1l6Knw0hzO0a4EiWoqg36BOtKD0eDbt3EQiR9VzNeDSw'
SAMPLE_RANGE_NAME = 'AutoTest log!B2:L'

class GoogleSheetOps:
    def __init__(self, sheetId = '1l6Knw0hzO0a4EiWoqg36BOtKD0eDbt3EQiR9VzNeDSw'):
        self.creds = None
        self.service = None
        self.sheet = None
        self.values = None
        self.SHEET_ID = sheetId
        self.connect()
    
    def connect(self):
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.sheet = self.service.spreadsheets()
    
    def getValues(self, rangeName):
        self.values = self.sheet.values().get(spreadsheetId=self.SHEET_ID,
                                    range=rangeName).execute().get('values', [])
        return self.values
    
    def batchUpdate(self, body):
        self.sheet.values().batchUpdate(
            spreadsheetId=self.SHEET_ID, body = body).execute()
        
    def append(self, body):
        self.sheet.values().append(
            spreadsheetId=self.SHEET_ID, body = body).execute()
    
    def clear(self, rangeName):
        self.sheet.values().clear(
            spreadsheetId=self.SHEET_ID, range=rangeName).execute()
    
    def search(self, rangeName, query):
        self.values = self.sheet.values().get(spreadsheetId=self.SHEET_ID,
                                    range=rangeName).execute().get('values', [])
        for row in self.values:
            print(row)
            if query in row:
                return row
        return None
    
    def find

def runCsv2Df(csvPath):
    import pandas as pd
    df = pd.read_csv(csvPath)
    return df

if __name__ == '__main__':
    gs = GoogleSheetOps()
    # print(gs.getValues(SAMPLE_RANGE_NAME))
    
    batch_update_values_request_body = {
    "valueInputOption": "USER_ENTERED",
    "data": [
        {
            'range': 'AutoTest log!P66:W',
            'values': [['1', '2', '3', '4', '5', '6', '7']]
        },
        {
            'range': 'AutoTest log!P67:W',
            'values': [['1', '2', '3', '4', '5', '6', '7']]
        },
        {
            'range': 'AutoTest log!P68:W',
            'values': [['1', '2', '3', '4', '5', '6', '7']]
        },
        {
            'range': 'AutoTest log!P69:W',
            'values': [['1', '2', '3', '4', '5', '6', '7']]
        },
        {
            'range': 'AutoTest log!P70:W',
            'values': [['1', '2', '3', '4', '5', '6', '7']]
        },
    ]
}
    testRange = 'AutoTest log!B66'
    # gs.batchUpdate(batch_update_values_request_body)
    targetRow = gs.search('AutoTest log!I:I', 'NCSUPI0019')
    print(targetRow)
    