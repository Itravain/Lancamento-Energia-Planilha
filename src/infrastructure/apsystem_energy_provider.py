import base64
import hmac
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from hashlib import sha256

import requests
from dotenv import load_dotenv


class APSystemEnergyProvider:
    """Adapter de infraestrutura para consultar a API APSystem."""

    def __init__(self) -> None:
        """Carrega credenciais da API a partir do ambiente."""
        load_dotenv()
        self.app_id = os.getenv("APP_ID")
        self.app_secret = os.getenv("APP_SECRET")
        self.system_id = os.getenv("SYSTEM_ID")
        self.base_url = "https://api.apsystemsema.com:9282/user/api/v2/systems/energy"

    def fetch_month_generation(self, month: int, year: int) -> dict[str, float]:
        """Busca e converte a geração diária para um mapa por data."""
        response_data = self._request_month_data(month, year)
        start_date = datetime(year, month, 1)
        return {
            (start_date + timedelta(days=index)).strftime("%d/%m/%Y"): float(value)
            for index, value in enumerate(response_data)
            if value is not None
        }

    def _request_month_data(self, month: int, year: int) -> list[float | None]:
        """Realiza a chamada autenticada para obter dados mensais."""
        if not self.app_id or not self.app_secret or not self.system_id:
            print("Variaveis APP_ID, APP_SECRET e SYSTEM_ID devem estar definidas.", file=sys.stderr)
            return []

        url = f"{self.base_url}/{self.system_id}"
        params = {
            "sid": self.system_id,
            "energy_level": "daily",
            "date_range": f"{year}-{month:02d}",
        }
        headers = self._build_headers(url)
        response = requests.get(url, headers=headers, params=params, timeout=30)

        try:
            payload = response.json()
        except ValueError:
            print(
                f"Resposta nao-JSON (status {response.status_code}): {response.text}",
                file=sys.stderr,
            )
            return []

        if not response.ok:
            message = payload.get("message") if isinstance(payload, dict) else response.text
            print(f"Erro da API (status {response.status_code}): {message}", file=sys.stderr)
            return []

        if not isinstance(payload, dict):
            return []

        data = payload.get("data")
        if isinstance(data, list):
            return data
        return []

    def _build_headers(self, url: str) -> dict[str, str]:
        """Monta headers com assinatura HMAC da APSystem."""
        timestamp = str(int(time.time()))
        nonce = str(uuid.uuid4()).replace("-", "")
        signature_method = "HmacSHA256"
        request_method = "GET"
        request_path = url.split("/")[-1]
        string_to_sign = (
            f"{timestamp}/{nonce}/{self.app_id}/"
            f"{request_path}/{request_method}/{signature_method}"
        )

        signature = base64.b64encode(
            hmac.new(
                self.app_secret.encode("utf-8"),
                string_to_sign.encode("utf-8"),
                sha256,
            ).digest()
        ).decode("utf-8")

        return {
            "X-CA-AppId": self.app_id,
            "X-CA-Timestamp": timestamp,
            "X-CA-Nonce": nonce,
            "X-CA-Signature-Method": signature_method,
            "X-CA-Signature": signature,
        }
