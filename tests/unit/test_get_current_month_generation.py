from datetime import date

import pytest

from src.application.get_current_month_generation import GetCurrentMonthGeneration


pytestmark = pytest.mark.unit


class FakeEnergyProvider:
    """Dublê de teste para simular retorno de geração mensal."""

    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def fetch_month_generation(self, month: int, year: int) -> dict[str, float]:
        """Retorna dados fixos e registra parametros recebidos."""
        self.calls.append((month, year))
        return {
            "01/04/2026": 10.5,
            "02/04/2026": 12.0,
        }


def test_execute_uses_current_month_and_builds_report() -> None:
    """Garante que o caso de uso consulta o mês atual e monta o relatório."""
    provider = FakeEnergyProvider()
    use_case = GetCurrentMonthGeneration(provider)

    report = use_case.execute(today=date(2026, 4, 19))

    assert provider.calls == [(4, 2026)]
    assert report.month == 4
    assert report.year == 2026
    assert report.daily_generation == {
        "01/04/2026": 10.5,
        "02/04/2026": 12.0,
    }
    assert report.total_generation == 22.5


def test_execute_uses_date_today_when_today_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Garante uso de date.today quando o parametro today nao e informado."""

    class FakeDate:
        @classmethod
        def today(cls) -> date:
            return date(2027, 1, 15)

    provider = FakeEnergyProvider()
    use_case = GetCurrentMonthGeneration(provider)

    monkeypatch.setattr("src.application.get_current_month_generation.date", FakeDate)

    report = use_case.execute()

    assert provider.calls == [(1, 2027)]
    assert report.month == 1
    assert report.year == 2027


def test_execute_handles_empty_generation() -> None:
    """Valida retorno vazio do provider sem quebrar o caso de uso."""

    class EmptyEnergyProvider:
        def fetch_month_generation(self, month: int, year: int) -> dict[str, float]:
            return {}

    use_case = GetCurrentMonthGeneration(EmptyEnergyProvider())

    report = use_case.execute(today=date(2026, 4, 19))

    assert report.daily_generation == {}
    assert report.total_generation == 0
