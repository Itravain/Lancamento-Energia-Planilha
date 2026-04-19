from dataclasses import FrozenInstanceError

import pytest

from src.domain.energy_report import MonthlyEnergyReport


pytestmark = pytest.mark.unit


def test_total_generation_sums_all_values() -> None:
    """Confere soma correta dos valores diarios."""
    report = MonthlyEnergyReport(
        month=4,
        year=2026,
        daily_generation={"01/04/2026": 10.5, "02/04/2026": 12.0},
    )

    assert report.total_generation == 22.5


def test_total_generation_with_empty_data_is_zero() -> None:
    """Confere total zero quando nao ha geracao diaria."""
    report = MonthlyEnergyReport(month=4, year=2026, daily_generation={})

    assert report.total_generation == 0


def test_report_is_immutable() -> None:
    """Garante imutabilidade do modelo de dominio."""
    report = MonthlyEnergyReport(month=4, year=2026, daily_generation={})

    with pytest.raises(FrozenInstanceError):
        report.month = 5
