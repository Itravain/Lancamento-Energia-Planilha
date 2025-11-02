import gspread
import calendar
from google.oauth2.service_account import Credentials
from datetime import date, datetime
import os
from dotenv import load_dotenv

load_dotenv()

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(creds)

sheet_id = os.getenv("SHEET_ID")
sheet = client.open_by_key(sheet_id)

# Passos para atualizar
pagina = sheet.worksheet("Produção de Energia Solar Diária")
dados = pagina.col_values(1)
ultimo_lancamento = dados[-1]

#Verificar ultimo dia de lançamento
ultimo_data = ultimo_lancamento.split('/')
ultimo_ano = int(ultimo_data[2])
ultimo_mes = int(ultimo_data[1])
ultimo_dia = int(ultimo_data[0])

hoje = date.today()
mes = int(hoje.month)
dia = int(hoje.day)
ano = int(hoje.year)


def listar_meses():
    lista = []
    for i in range(ultimo_ano, ano + 1):
        if(i == ultimo_ano):
            limite_mes = 12
            inicio_mes = ultimo_mes
        elif(i < ano):
            inicio_mes = 1
            limite_mes = 12
        else:
            limite_mes = mes
            inicio_mes = 1
        for j in range(inicio_mes, limite_mes + 1):
            lista.append([j, i])
    return lista

def adicionar_listas_fim(todos_dados_dic):
    #Transforma em lista
    todos_dados_list = [
        [data, valor]
        for data, valor in todos_dados_dic.items()
    ]
    #Remove os dias que já estão na planilha
    del todos_dados_list[0:ultimo_dia]
    #adiciona na planilha
    pagina.append_rows(todos_dados_list, value_input_option="USER_ENTERED")