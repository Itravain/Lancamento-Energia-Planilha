import pytest

from src.application.get_year_generation import GetYearGeneration


pytestmark = pytest.mark.unit


class FakeEnergyProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def fetch_month_generation(self, month: int, year: int) -> dict[str, float]:
        self.calls.append((month, year))
        return {
            f"01/{month:02d}/{year}": float(month),
        }


def test_execute_aggregates_all_months() -> None:
    provider = FakeEnergyProvider()
    use_case = GetYearGeneration(provider)

    report = use_case.execute(2026)

    assert len(provider.calls) == 12
    assert provider.calls[0] == (1, 2026)
    assert provider.calls[-1] == (12, 2026)
    assert report.year == 2026
    assert report.monthly_generation["01/2026"] == 1.0
    assert report.monthly_generation["12/2026"] == 12.0
    assert report.total_generation == 78.0
