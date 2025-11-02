import hmac
import base64
import uuid
import time
import requests
from hashlib import sha256
from hashlib import sha1
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import sys

load_dotenv()

def energia_mes(mes, ano):
    # Related parameter information
    appId = os.getenv("APP_ID")
    appSecret = os.getenv("APP_SECRET")
    systemId = os.getenv("SYSTEM_ID")
    
    url = f"https://api.apsystemsema.com:9282/user/api/v2/systems/energy/{systemId}"

    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4()).replace('-', '')
    signatureMethod = "HmacSHA256"
    requestMethod = "GET"
    requestPath = url.split('/')[-1]

    # Create the string to sign
    stringToSign = f"{timestamp}/{nonce}/{appId}/{requestPath}/{requestMethod}/{signatureMethod}"
    print(stringToSign)

    # Generate the signature
    # HmacSHA256
    signature = base64.b64encode(hmac.new(appSecret.encode('utf-8'), stringToSign.encode('utf-8'), sha256).digest()).decode('utf-8')

    # Request headers
    headers = {
        "X-CA-AppId": appId,
        "X-CA-Timestamp": timestamp,
        "X-CA-Nonce": nonce,
        "X-CA-Signature-Method": signatureMethod,
        "X-CA-Signature": signature
    }

    params ={
        "sid": systemId,
        "energy_level": "daily",
        "date_range": f"{ano}-{mes:02d}"
    }

    data = {
    }

    response = requests.get(url, headers=headers, data=data, params=params)

    try:
        res = response.json()
    except ValueError:
        print(f"Resposta não-JSON (status {response.status_code}): {response.text}", file=sys.stderr)
        return [] 

    # verifica status HTTP
    if not response.ok:
        msg = res.get("message") if isinstance(res, dict) else response.text
        print(f"Erro da API (status {response.status_code}): {msg}", file=sys.stderr)
        return []

    dados = res.get("data")
    if dados is None:
        print(f"Resposta sem campo 'data': {res}", file=sys.stderr)
        return [] 

    return dados

def req_energia(mes, ano):
    data_inicial = datetime(ano, mes, 1)
    energia = energia_mes(mes, ano)
    dados = {
        (data_inicial + timedelta(days=i)).strftime("%d/%m/%Y"): float(v)
        for i, v in enumerate(energia) if v is not None
    }
    return dados


