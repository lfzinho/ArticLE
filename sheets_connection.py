'''
Classe para salvar os dados no Google Sheets
'''

import os.path
import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1R4Wo4gQG-zopWZvrpGz5WJtKkkSr9ULrwTUmRg9X29Y'

class SaveMetrics():
    '''
    Classe para salvar os dados no Google Sheets

    Parâmetros
    ----------
    range : str
        Range do sheet onde os dados serão salvos. O padrão é 'A:AZ'. Utiliza 
        a sintaxe do Google Sheets para definir o range. Exemplo: 'A:AZ' ou 'A1:AZ100'
    '''
    def __init__(self, range:str='A:AZ') -> None:
        self.range = range
        self.sheet = build(
            'sheets', 
            'v4', 
            credentials=self._set_creds()
        ).spreadsheets()

    def _set_creds(self) -> Credentials:
        '''
        Função para setar as credenciais do Google Sheets
        
        Retorna
        -------
        Credentials
            Credenciais do Google Sheets
        '''
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
        '''
        Função para salvar os dados no Google Sheets

        Parâmetros
        ----------
        type_of_metric : str
            Tipo de métrica que será salva no Google Sheets
        data : pd.DataFrame
            DataFrame com os dados que serão salvos no Google Sheets

        Retorna
        ----------
        None
        '''
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
