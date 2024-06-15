import os.path
import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1R4Wo4gQG-zopWZvrpGz5WJtKkkSr9ULrwTUmRg9X29Y'

class SaveMetrics():
    def __init__(self, range:str='A:AZ') -> None:
        self.range = range
        self.sheet = build(
            'sheets', 
            'v4', 
            credentials=self._set_creds()
        ).spreadsheets()

    def _set_creds(self) -> Credentials:
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

    def append_metrics(self, type_of_metric:str, data:pd.DataFrame) -> None:
        # Define a página e o range
        range = f"{type_of_metric}!{self.range}"

        # Pega os valores atuais do sheet
        result = self.sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range
        ).execute()
        values = result.get('values', [])

        if len(values) > 0:
            # Ordena o dataframe pelas colunas do sheet
            data = data.sort_values(by=values[0], axis=0)
            # Converte o dataframe em uma lista de listas
            data = data.values.tolist()
        else:
            # Adiciona o cabeçalho ao sheet
            values = [data.columns.tolist()]
            # Converte o dataframe em uma lista de listas
            data = data.values.tolist()

        # Adiciona os valores ao sheet
        values += data

        # Atualiza o sheet
        result = self.sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range, 
            valueInputOption="RAW",
            body={"values": values}
        ).execute()
