from datetime import datetime

import pytest

from src.domain.energy_report import HourlyEnergyRecord
from src.infrastructure.sqlite_hourly_energy_repository import SQLiteHourlyEnergyRepository


pytestmark = pytest.mark.unit


def test_upsert_and_get_range(tmp_path: pytest.TempPathFactory) -> None:
    db_path = tmp_path / "energy.db"
    repository = SQLiteHourlyEnergyRepository(str(db_path))

    repository.upsert_many(
        [
            HourlyEnergyRecord("sys-1", datetime(2026, 4, 19, 10), 1.1),
            HourlyEnergyRecord("sys-1", datetime(2026, 4, 19, 11), 1.2),
        ]
    )

    result = repository.get_range(
        "sys-1",
        datetime(2026, 4, 19, 10),
        datetime(2026, 4, 19, 11),
    )

    assert result == {
        datetime(2026, 4, 19, 10): 1.1,
        datetime(2026, 4, 19, 11): 1.2,
    }


def test_upsert_is_idempotent(tmp_path: pytest.TempPathFactory) -> None:
    db_path = tmp_path / "energy.db"
    repository = SQLiteHourlyEnergyRepository(str(db_path))

    row = HourlyEnergyRecord("sys-1", datetime(2026, 4, 19, 10), 1.1)
    repository.upsert_many([row])
    repository.upsert_many([row])

    result = repository.get_range(
        "sys-1",
        datetime(2026, 4, 19, 10),
        datetime(2026, 4, 19, 10),
    )

    assert result == {datetime(2026, 4, 19, 10): 1.1}


def test_get_range_is_isolated_by_system_id(tmp_path: pytest.TempPathFactory) -> None:
    db_path = tmp_path / "energy.db"
    repository = SQLiteHourlyEnergyRepository(str(db_path))

    repository.upsert_many(
        [
            HourlyEnergyRecord("sys-1", datetime(2026, 4, 19, 10), 1.1),
            HourlyEnergyRecord("sys-2", datetime(2026, 4, 19, 10), 9.9),
        ]
    )

    result = repository.get_range(
        "sys-1",
        datetime(2026, 4, 19, 10),
        datetime(2026, 4, 19, 10),
    )

    assert result == {datetime(2026, 4, 19, 10): 1.1}
