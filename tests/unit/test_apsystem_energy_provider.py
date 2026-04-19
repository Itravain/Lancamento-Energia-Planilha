import base64
import hmac
from hashlib import sha256

import pytest

from src.infrastructure.apsystem_energy_provider import APSystemEnergyProvider


pytestmark = pytest.mark.unit


class FakeResponse:
    """Resposta fake para simular requests.Response."""

    def __init__(self, ok: bool, status_code: int, payload: object, text: str = "") -> None:
        self.ok = ok
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> object:
        if self._payload == "raise_value_error":
            raise ValueError("invalid json")
        return self._payload


def test_request_month_data_returns_empty_when_env_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Deve retornar vazio quando faltarem variaveis obrigatorias."""
    monkeypatch.setenv("APP_ID", "")
    monkeypatch.setenv("APP_SECRET", "")
    monkeypatch.setenv("SYSTEM_ID", "")

    provider = APSystemEnergyProvider()

    result = provider._request_month_data(4, 2026)

    assert result == []
    captured = capsys.readouterr()
    assert "APP_ID" in captured.err


def test_request_month_data_handles_non_json_response(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Deve retornar vazio quando a API nao responder em JSON."""
    monkeypatch.setenv("APP_ID", "app")
    monkeypatch.setenv("APP_SECRET", "secret")
    monkeypatch.setenv("SYSTEM_ID", "system")

    def fake_get(*args: object, **kwargs: object) -> FakeResponse:
        return FakeResponse(ok=True, status_code=200, payload="raise_value_error", text="html")

    monkeypatch.setattr("src.infrastructure.apsystem_energy_provider.requests.get", fake_get)

    provider = APSystemEnergyProvider()
    result = provider._request_month_data(4, 2026)

    assert result == []
    captured = capsys.readouterr()
    assert "Resposta nao-JSON" in captured.err


def test_request_month_data_handles_http_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Deve retornar vazio para resposta HTTP com erro."""
    monkeypatch.setenv("APP_ID", "app")
    monkeypatch.setenv("APP_SECRET", "secret")
    monkeypatch.setenv("SYSTEM_ID", "system")

    def fake_get(*args: object, **kwargs: object) -> FakeResponse:
        return FakeResponse(ok=False, status_code=401, payload={"message": "unauthorized"})

    monkeypatch.setattr("src.infrastructure.apsystem_energy_provider.requests.get", fake_get)

    provider = APSystemEnergyProvider()
    result = provider._request_month_data(4, 2026)

    assert result == []
    captured = capsys.readouterr()
    assert "Erro da API" in captured.err


def test_request_month_data_returns_empty_when_data_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deve retornar vazio quando payload nao contem campo data."""
    monkeypatch.setenv("APP_ID", "app")
    monkeypatch.setenv("APP_SECRET", "secret")
    monkeypatch.setenv("SYSTEM_ID", "system")

    def fake_get(*args: object, **kwargs: object) -> FakeResponse:
        return FakeResponse(ok=True, status_code=200, payload={"status": "ok"})

    monkeypatch.setattr("src.infrastructure.apsystem_energy_provider.requests.get", fake_get)

    provider = APSystemEnergyProvider()
    result = provider._request_month_data(4, 2026)

    assert result == []


def test_fetch_month_generation_maps_values_and_skips_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Converte lista da API em dicionario por data e ignora valores None."""
    monkeypatch.setenv("APP_ID", "app")
    monkeypatch.setenv("APP_SECRET", "secret")
    monkeypatch.setenv("SYSTEM_ID", "system")

    def fake_get(*args: object, **kwargs: object) -> FakeResponse:
        return FakeResponse(ok=True, status_code=200, payload={"data": [1.0, None, 3.5]})

    monkeypatch.setattr("src.infrastructure.apsystem_energy_provider.requests.get", fake_get)

    provider = APSystemEnergyProvider()
    generation = provider.fetch_month_generation(4, 2026)

    assert generation == {
        "01/04/2026": 1.0,
        "03/04/2026": 3.5,
    }


def test_build_headers_has_expected_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valida assinatura HMAC e campos obrigatorios dos headers."""
    monkeypatch.setenv("APP_ID", "app123")
    monkeypatch.setenv("APP_SECRET", "secret123")
    monkeypatch.setenv("SYSTEM_ID", "system123")
    monkeypatch.setattr("src.infrastructure.apsystem_energy_provider.time.time", lambda: 1710000000)
    monkeypatch.setattr(
        "src.infrastructure.apsystem_energy_provider.uuid.uuid4",
        lambda: "11111111-2222-3333-4444-555555555555",
    )

    provider = APSystemEnergyProvider()
    url = "https://api.apsystemsema.com:9282/user/api/v2/systems/energy/system123"

    headers = provider._build_headers(url)

    nonce = "11111111222233334444555555555555"
    string_to_sign = (
        "1710000000/"
        f"{nonce}/"
        "app123/system123/GET/HmacSHA256"
    )
    expected_signature = base64.b64encode(
        hmac.new(b"secret123", string_to_sign.encode("utf-8"), sha256).digest()
    ).decode("utf-8")

    assert headers["X-CA-AppId"] == "app123"
    assert headers["X-CA-Timestamp"] == "1710000000"
    assert headers["X-CA-Nonce"] == nonce
    assert headers["X-CA-Signature-Method"] == "HmacSHA256"
    assert headers["X-CA-Signature"] == expected_signature
