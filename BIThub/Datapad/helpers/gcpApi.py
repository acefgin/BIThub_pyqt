from __future__ import print_function
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import google.auth
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
# SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

# The ID and range of a sample spreadsheet.
# SAMPLE_SPREADSHEET_ID = '1l6Knw0hzO0a4EiWoqg36BOtKD0eDbt3EQiR9VzNeDSw'
# SAMPLE_RANGE_NAME = 'AutoTest log!B2:L'

def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)

        # Call the Drive v3 API
        results = service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')
        
def upload_basic():
    """Insert new file.
    Returns : Id's of the file uploaded

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    creds, _ = google.auth.default()

    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {'name': 'download.jpeg'}
        media = MediaFileUpload('download.jpeg',
                                mimetype='image/jpeg')
        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, media_body=media,
                                      fields='id').execute()
        print(F'File ID: {file.get("id")}')

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

    return file.get('id')
        
class GCPClient:
    def __init__(self) -> None:
        self.creds = None
        self.service = None


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

def runCsv2Df(csvPath):
    import pandas as pd
    df = pd.read_csv(csvPath)
    return df

if __name__ == '__main__':

#     gs = GoogleSheetOps()
    
#     batch_update_values_request_body = {
#     "valueInputOption": "USER_ENTERED",
#     "data": [
#         {
#             'range': 'AutoTest log!P66:W',
#             'values': [['1', '2', '3', '4', '5', '6', '7']]
#         },
#         {
#             'range': 'AutoTest log!P67:W',
#             'values': [['1', '2', '3', '4', '5', '6', '7']]
#         },
#         {
#             'range': 'AutoTest log!P68:W',
#             'values': [['1', '2', '3', '4', '5', '6', '7']]
#         },
#         {
#             'range': 'AutoTest log!P69:W',
#             'values': [['1', '2', '3', '4', '5', '6', '7']]
#         },
#         {
#             'range': 'AutoTest log!P70:W',
#             'values': [['1', '2', '3', '4', '5', '6', '7']]
#         },
#     ]
# }
#     testRange = 'AutoTest log!B66'
#     # gs.batchUpdate(batch_update_values_request_body)
#     targetRow = gs.search('AutoTest log!I:I', 'NCSUPI0019')
#     print(targetRow)

    main()