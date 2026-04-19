import pytest

from src.domain.energy_report import MonthlyEnergyReport
from src.interfaces.cli import print_monthly_report


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
