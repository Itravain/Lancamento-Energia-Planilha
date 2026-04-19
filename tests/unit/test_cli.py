from datetime import date, datetime

import pytest

from src.domain.energy_report import DailyEnergyReport, MonthlyEnergyReport, YearlyEnergyReport
from src.interfaces.cli import (
    print_daily_report,
    print_hourly_report,
    print_monthly_report,
    print_yearly_report,
)


pytestmark = pytest.mark.unit


def test_print_monthly_report_format(capsys: pytest.CaptureFixture[str]) -> None:
    """Valida formato textual apresentado no console."""
    report = MonthlyEnergyReport(
        month=4,
        year=2026,
        daily_generation={"01/04/2026": 10.5, "02/04/2026": 12.0},
    )

    print_monthly_report(report)

    captured = capsys.readouterr()
    expected_lines = [
        "Geracao de energia - 04/2026",
        "Total no mes: 22.50",
        "Detalhamento diario:",
        "01/04/2026: 10.5",
        "02/04/2026: 12.0",
    ]
    for line in expected_lines:
        assert line in captured.out


def test_print_hourly_report_format(capsys: pytest.CaptureFixture[str]) -> None:
    """Valida formato textual do relatório horário."""
    generation = {
        datetime(2026, 4, 19, 10): 1.1,
        datetime(2026, 4, 19, 11): 1.2,
    }

    print_hourly_report(generation)

    captured = capsys.readouterr()
    expected_lines = [
        "Geracao horaria",
        "Total no periodo: 2.30",
        "Detalhamento por hora:",
        "19/04/2026 10:00: 1.1",
        "19/04/2026 11:00: 1.2",
    ]
    for line in expected_lines:
        assert line in captured.out


def test_print_daily_report_format(capsys: pytest.CaptureFixture[str]) -> None:
    """Valida formato textual do relatório diário."""
    report = DailyEnergyReport(
        day=date(2026, 4, 19),
        hourly_generation={
            datetime(2026, 4, 19, 10): 1.1,
            datetime(2026, 4, 19, 11): 1.2,
        },
    )

    print_daily_report(report)

    captured = capsys.readouterr()
    expected_lines = [
        "Geracao diaria - 19/04/2026",
        "Total no dia: 2.30",
        "Detalhamento por hora:",
        "19/04/2026 10:00: 1.1",
        "19/04/2026 11:00: 1.2",
    ]
    for line in expected_lines:
        assert line in captured.out


def test_print_yearly_report_format(capsys: pytest.CaptureFixture[str]) -> None:
    """Valida formato textual do relatório anual."""
    report = YearlyEnergyReport(
        year=2026,
        monthly_generation={
            "01/2026": 10.0,
            "02/2026": 20.0,
        },
    )

    print_yearly_report(report)

    captured = capsys.readouterr()
    expected_lines = [
        "Geracao anual - 2026",
        "Total no ano: 30.00",
        "Detalhamento mensal:",
        "01/2026: 10.0",
        "02/2026: 20.0",
    ]
    for line in expected_lines:
        assert line in captured.out
