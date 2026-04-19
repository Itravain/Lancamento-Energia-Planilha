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


def test_run_hourly_mode_wires_hourly_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida wiring do modo horário com cache e saída específica."""
    captured: dict[str, object] = {}

    class FakeProvider:
        pass

    class FakeRepo:
        def __init__(self, db_path: str) -> None:
            captured["db_path"] = db_path

    class FakeHourlyUseCase:
        def __init__(self, provider: object, repository: object) -> None:
            captured["provider"] = provider
            captured["repository"] = repository

        def execute(self, system_id: str, start_at: object, end_at: object) -> dict[object, float]:
            captured["system_id"] = system_id
            captured["start_at"] = start_at
            captured["end_at"] = end_at
            return {}

    def fake_print_hourly(result: dict[object, float]) -> None:
        captured["printed"] = result

    monkeypatch.setenv("ENERGY_MODE", "hourly")
    monkeypatch.setenv("HOURLY_START_AT", "2026-04-19 10:00")
    monkeypatch.setenv("HOURLY_END_AT", "2026-04-19 12:00")
    monkeypatch.setenv("SYSTEM_ID", "sys-1")
    monkeypatch.setenv("ENERGY_DB_PATH", "/tmp/energy.db")

    monkeypatch.setattr("src.main.APSystemEnergyProvider", FakeProvider)
    monkeypatch.setattr("src.main.SQLiteHourlyEnergyRepository", FakeRepo)
    monkeypatch.setattr("src.main.GetHourlyEnergyRange", FakeHourlyUseCase)
    monkeypatch.setattr("src.main.print_hourly_report", fake_print_hourly)

    run()

    assert isinstance(captured["provider"], FakeProvider)
    assert captured["db_path"] == "/tmp/energy.db"
    assert captured["system_id"] == "sys-1"
    assert captured["printed"] == {}
