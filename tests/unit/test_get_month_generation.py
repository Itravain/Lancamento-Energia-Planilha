import pytest

from src.application.get_month_generation import GetMonthGeneration


pytestmark = pytest.mark.unit


class FakeEnergyProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def fetch_month_generation(self, month: int, year: int) -> dict[str, float]:
        self.calls.append((month, year))
        return {
            "01/04/2026": 10.0,
            "02/04/2026": 12.0,
        }


def test_execute_returns_monthly_report_for_given_period() -> None:
    provider = FakeEnergyProvider()
    use_case = GetMonthGeneration(provider)

    report = use_case.execute(month=4, year=2026)

    assert provider.calls == [(4, 2026)]
    assert report.month == 4
    assert report.year == 2026
    assert report.total_generation == 22.0


def test_execute_raises_for_invalid_month() -> None:
    provider = FakeEnergyProvider()
    use_case = GetMonthGeneration(provider)

    with pytest.raises(ValueError):
        use_case.execute(month=13, year=2026)
