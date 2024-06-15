from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1R4Wo4gQG-zopWZvrpGz5WJtKkkSr9ULrwTUmRg9X29Y'

class SaveMetrics():
    def __init__(self, range='A:AZ') -> None:
        self.creds = self._set_creds()
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.range = range

    def _set_creds(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret.json', SCOPES)
                creds = flow.run_local_server(port=0)
        return creds

    def append_metrics(self, type_of_metric, data):
        range = f"{type_of_metric}!{self.range}"
        sheet = self.service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range
        ).execute()
        values = result.get('values', [])

        for row in data:
            values.append(row)
        result = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range, 
            valueInputOption="RAW",
            body={"values": values}
        ).execute()

