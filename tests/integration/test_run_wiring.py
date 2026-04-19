import pytest

from src.domain.energy_report import MonthlyEnergyReport
from src.main import run


pytestmark = pytest.mark.integration


def test_run_wires_dependencies_and_calls_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida composicao entre provider, caso de uso e interface CLI."""
    captured: dict[str, object] = {}

    class FakeProvider:
        pass

    class FakeUseCase:
        def __init__(self, provider: object) -> None:
            captured["provider"] = provider

        def execute(self) -> MonthlyEnergyReport:
            report = MonthlyEnergyReport(
                month=4,
                year=2026,
                daily_generation={"01/04/2026": 10.0},
            )
            captured["report"] = report
            return report

    def fake_print(report: MonthlyEnergyReport) -> None:
        captured["printed"] = report

    monkeypatch.setattr("src.main.APSystemEnergyProvider", FakeProvider)
    monkeypatch.setattr("src.main.GetCurrentMonthGeneration", FakeUseCase)
    monkeypatch.setattr("src.main.print_monthly_report", fake_print)

    run()

    assert isinstance(captured["provider"], FakeProvider)
    assert captured["printed"] == captured["report"]
