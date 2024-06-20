'''
Classe para salvar os dados no Google Sheets
'''

import os.path
import pandas as pd
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

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
        # Carregar credenciais da conta de serviço
        creds = Credentials.from_service_account_file(
            'client_secret.json', scopes=SCOPES)
        return creds

    def append_metrics(self, type_of_metric:str, data:pd.DataFrame) -> None:
        '''
        Função para adicionar uma linha de dados no Google Sheets

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

    def set_metric_of_query_and_model(
            self, 
            type_of_metric:str, 
            query:str, 
            model_name:str, 
            result:float
        ) -> None:
        '''
        Função para salvar o resultado da métrica de uma query e modelo no Google Sheets.
        Esse método depende da tabela estar preparada com o id das queries na
        primeira coluna (A2 em diante) e o nome dos modelos na 
        primeira linha (B2 em diante).

        Parâmetros
        ----------
        type_of_metric : str
            Tipo de métrica que será salva no Google Sheets
        query : str
            Query que foi utilizada para fazer o search com o modelo
        model_name : str
            Nome do modelo
        result : float
            Resultado da métrica para a query e modelo especificados

        Retorna
        ----------
        range : str
            Localização do resultado no Google Sheets
        '''
        # Pega os valores atuais da primeira linha do sheet
        first_row = self.sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{type_of_metric}!"+":".join([re.sub(r'\d+', '', col) + "1" for col in self.range.split(':')])
        ).execute()
        models = first_row.get('values', [])[0]
        
        # Pega os valores atuais da primeira coluna do sheet
        first_column = self.sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{type_of_metric}!A:A"
        ).execute()
        queries = [l[0] for l in first_column.get('values', [])]

        print(models)
        print(queries)

        # Obtém a posição da célula referente à query e ao modelo
        row = queries.index(query) + 1
        col = models.index(model_name) + 1
        
        # Define a página e o range
        range = f"{type_of_metric}!{convert_number_to_column_name(col)}{row}"

        # Atualiza o sheet
        self.sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range,
            valueInputOption="RAW",
            body={"values": [[result]]}
        ).execute()

        # Retorna a localização do resultado
        return range

def convert_number_to_column_name(number):
        '''
        Função para converter um número em uma coluna do Google Sheets (Notação A1).

        Parâmetros
        ----------
        number : int
            Número da coluna (inicia em 1)

        Retorna
        ----------
        col : str
            Coluna do Google Sheets
        '''
        col = ''
        while number > 0:
            number -= 1
            letter = number % 26
            number = number // 26 
            letter = chr(65 + letter)
            col = letter + col
        return col
