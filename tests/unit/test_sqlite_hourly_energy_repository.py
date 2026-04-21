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


def test_list_hierarchical_levels(tmp_path: pytest.TempPathFactory) -> None:
    db_path = tmp_path / "energy.db"
    repository = SQLiteHourlyEnergyRepository(str(db_path))

    repository.upsert_many(
        [
            HourlyEnergyRecord("sys-1", datetime(2026, 1, 2, 10), 1.0),
            HourlyEnergyRecord("sys-1", datetime(2026, 1, 2, 11), 2.0),
            HourlyEnergyRecord("sys-1", datetime(2026, 2, 3, 9), 3.0),
            HourlyEnergyRecord("sys-1", datetime(2027, 1, 1, 8), 4.0),
        ]
    )

    years = repository.list_years("sys-1")
    months_2026 = repository.list_months("sys-1", 2026)
    days_feb_2026 = repository.list_days("sys-1", 2026, 2)
    hours_day = repository.list_hours("sys-1", 2026, 1, 2)

    assert years == [(2026, 6.0), (2027, 4.0)]
    assert months_2026 == [(1, 3.0), (2, 3.0)]
    assert days_feb_2026 == [(3, 3.0)]
    assert hours_day == [(10, 1.0), (11, 2.0)]


def test_month_day_bounds_returns_full_month_range(tmp_path: pytest.TempPathFactory) -> None:
    db_path = tmp_path / "energy.db"
    repository = SQLiteHourlyEnergyRepository(str(db_path))

    start_at, end_at = repository.month_day_bounds(2026, 2)

    assert start_at == datetime(2026, 2, 1, 0, 0)
    assert end_at == datetime(2026, 2, 28, 23, 0)


def test_delete_month_removes_only_target_month(tmp_path: pytest.TempPathFactory) -> None:
    db_path = tmp_path / "energy.db"
    repository = SQLiteHourlyEnergyRepository(str(db_path))

    repository.upsert_many(
        [
            HourlyEnergyRecord("sys-1", datetime(2026, 1, 2, 10), 1.0),
            HourlyEnergyRecord("sys-1", datetime(2026, 2, 3, 9), 3.0),
            HourlyEnergyRecord("sys-1", datetime(2026, 2, 3, 10), 4.0),
        ]
    )

    deleted = repository.delete_month("sys-1", 2026, 2)

    january_rows = repository.list_days("sys-1", 2026, 1)
    february_rows = repository.list_days("sys-1", 2026, 2)
    assert deleted == 2
    assert january_rows == [(2, 1.0)]
    assert february_rows == []


def test_delete_day_removes_only_target_day(tmp_path: pytest.TempPathFactory) -> None:
    db_path = tmp_path / "energy.db"
    repository = SQLiteHourlyEnergyRepository(str(db_path))

    repository.upsert_many(
        [
            HourlyEnergyRecord("sys-1", datetime(2026, 2, 3, 9), 3.0),
            HourlyEnergyRecord("sys-1", datetime(2026, 2, 4, 10), 4.0),
        ]
    )

    deleted = repository.delete_day("sys-1", 2026, 2, 3)

    days = repository.list_days("sys-1", 2026, 2)
    assert deleted == 1
    assert days == [(4, 4.0)]
