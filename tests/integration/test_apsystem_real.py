import os
from datetime import date, datetime

import pytest

from src.infrastructure.apsystem_energy_provider import APSystemEnergyProvider


pytestmark = pytest.mark.integration_real


def test_fetch_month_generation_real_api_opt_in() -> None:
    """Executa chamada real apenas quando RUN_APSYSTEM_INTEGRATION=true."""
    if os.getenv("RUN_APSYSTEM_INTEGRATION", "").lower() != "true":
        pytest.skip("Teste real desabilitado. Defina RUN_APSYSTEM_INTEGRATION=true.")

    today = date.today()
    provider = APSystemEnergyProvider()
    generation = provider.fetch_month_generation(today.month, today.year)

    assert isinstance(generation, dict)


def test_fetch_hourly_generation_real_api_opt_in() -> None:
    """Executa chamada horária real apenas quando RUN_APSYSTEM_INTEGRATION=true."""
    if os.getenv("RUN_APSYSTEM_INTEGRATION", "").lower() != "true":
        pytest.skip("Teste real desabilitado. Defina RUN_APSYSTEM_INTEGRATION=true.")

    provider = APSystemEnergyProvider()
    start_at = datetime(2026, 4, 19, 10)
    end_at = datetime(2026, 4, 19, 12)
    system_id = os.getenv("SYSTEM_ID", "")

    generation = provider.fetch_hourly_generation(system_id, start_at, end_at)

    assert isinstance(generation, dict)
