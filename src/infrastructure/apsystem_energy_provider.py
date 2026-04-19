import base64
import hmac
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any

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

    def fetch_hourly_generation(
        self,
        system_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[datetime, float]:
        """Busca geração horária no intervalo e converte para mapa datetime -> kWh."""
        response_data = self._request_hourly_data(system_id, start_at, end_at)
        if not response_data:
            return {}

        # Formato 1: lista sequencial de valores por hora.
        if isinstance(response_data, list) and all(
            item is None or isinstance(item, (int, float, str)) for item in response_data
        ):
            current = start_at
            result: dict[datetime, float] = {}
            for value in response_data:
                if current > end_at:
                    break
                if value is not None:
                    result[current] = float(value)
                current += timedelta(hours=1)
            return result

        # Formato 2: lista de objetos com data/hora e energia.
        if isinstance(response_data, list):
            result: dict[datetime, float] = {}
            for item in response_data:
                if not isinstance(item, dict):
                    continue
                dt = self._extract_datetime(item)
                value = self._extract_energy(item)
                if dt is None or value is None:
                    continue
                if start_at <= dt <= end_at:
                    result[dt] = value
            return result

        # Formato 3: dicionário com datetime como chave e energia como valor.
        if isinstance(response_data, dict):
            result: dict[datetime, float] = {}
            for raw_dt, raw_value in response_data.items():
                dt = self._parse_datetime(str(raw_dt))
                if dt is None:
                    continue
                try:
                    value = float(raw_value)
                except (TypeError, ValueError):
                    continue
                if start_at <= dt <= end_at:
                    result[dt] = value
            return result

        return {}

    def _request_month_data(self, month: int, year: int) -> list[float | None]:
        """Realiza a chamada autenticada para obter dados mensais."""
        url = f"{self.base_url}/{self.system_id}"
        params = {
            "sid": self.system_id,
            "energy_level": "daily",
            "date_range": f"{year}-{month:02d}",
        }
        data = self._request_data(url, params)
        if isinstance(data, list):
            return data
        return []

    def _request_hourly_data(
        self,
        system_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[datetime, float]:
        """Realiza chamadas diárias para obter geração horária em um intervalo."""
        url = f"{self.base_url}/{system_id}"
        day_cursor = start_at.replace(hour=0, minute=0, second=0, microsecond=0)
        last_day = end_at.replace(hour=0, minute=0, second=0, microsecond=0)
        aggregated: dict[datetime, float] = {}

        while day_cursor <= last_day:
            params = {
                "sid": system_id,
                "energy_level": "hourly",
                # A API aceita granularidade horária com date_range de dia único.
                "date_range": day_cursor.strftime("%Y-%m-%d"),
            }
            raw_day_data = self._request_data(url, params)
            day_result = self._normalize_hourly_payload(raw_day_data, day_cursor)
            aggregated.update(day_result)
            day_cursor += timedelta(days=1)

        return aggregated

    def _normalize_hourly_payload(
        self,
        payload: Any,
        day_base: datetime,
    ) -> dict[datetime, float]:
        """Normaliza payload horário em mapa datetime -> energia."""
        # Formato sequencial com 24 valores horários (00:00 ... 23:00).
        if isinstance(payload, list) and all(
            item is None or isinstance(item, (int, float, str)) for item in payload
        ):
            result: dict[datetime, float] = {}
            for hour_index, item in enumerate(payload):
                if item is None:
                    continue
                try:
                    value = float(item)
                except (TypeError, ValueError):
                    continue
                result[day_base + timedelta(hours=hour_index)] = value
            return result

        # Formato lista de objetos com datetime + energia.
        if isinstance(payload, list):
            result: dict[datetime, float] = {}
            for item in payload:
                if not isinstance(item, dict):
                    continue
                dt = self._extract_datetime(item)
                value = self._extract_energy(item)
                if dt is None or value is None:
                    continue
                result[dt] = value
            return result

        # Formato dict de chaves datetime para energia.
        if isinstance(payload, dict):
            result: dict[datetime, float] = {}
            for raw_dt, raw_value in payload.items():
                dt = self._parse_datetime(str(raw_dt))
                if dt is None:
                    continue
                try:
                    value = float(raw_value)
                except (TypeError, ValueError):
                    continue
                result[dt] = value
            return result

        return {}

    def _request_data(self, url: str, params: dict[str, str]) -> Any:
        """Executa request autenticado e retorna campo data quando disponível."""
        if not self.app_id or not self.app_secret or not self.system_id:
            print("Variaveis APP_ID, APP_SECRET e SYSTEM_ID devem estar definidas.", file=sys.stderr)
            return []

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

        return payload.get("data", [])

    def _extract_datetime(self, payload: dict[str, Any]) -> datetime | None:
        """Extrai e converte campo de data/hora de formatos comuns da API."""
        for key in ("datetime", "timestamp", "time", "hour", "date"):
            raw_value = payload.get(key)
            if raw_value is None:
                continue
            parsed = self._parse_datetime(str(raw_value))
            if parsed is not None:
                return parsed
        return None

    def _extract_energy(self, payload: dict[str, Any]) -> float | None:
        """Extrai energia de formatos comuns do payload horário."""
        for key in ("energy", "value", "kwh"):
            raw_value = payload.get(key)
            if raw_value is None:
                continue
            try:
                return float(raw_value)
            except (TypeError, ValueError):
                return None
        return None

    def _parse_datetime(self, raw_value: str) -> datetime | None:
        """Converte string de data/hora em datetime para múltiplos formatos."""
        sanitized = raw_value.replace("T", " ").replace("Z", "")
        formats = (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
        )
        for fmt in formats:
            try:
                return datetime.strptime(sanitized, fmt)
            except ValueError:
                continue
        return None

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
