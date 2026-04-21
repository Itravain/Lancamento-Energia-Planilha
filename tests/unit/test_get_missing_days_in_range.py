from datetime import date, datetime

import pytest

from src.application.get_missing_days_in_range import GetMissingDaysInRange


pytestmark = pytest.mark.unit


class FakeRepository:
    def __init__(self, payload: dict[datetime, float]) -> None:
        self.payload = payload
        self.calls: list[tuple[str, datetime, datetime]] = []

    def get_range(self, system_id: str, start_at: datetime, end_at: datetime) -> dict[datetime, float]:
        self.calls.append((system_id, start_at, end_at))
        return self.payload


def test_execute_returns_missing_days_in_closed_interval() -> None:
    repository = FakeRepository(
        {
            datetime(2026, 4, 20, 10): 1.0,
            datetime(2026, 4, 22, 11): 2.0,
        }
    )
    use_case = GetMissingDaysInRange(repository)

    missing_days = use_case.execute("sys-1", date(2026, 4, 20), date(2026, 4, 22))

    assert missing_days == [date(2026, 4, 21)]
    assert repository.calls == [
        (
            "sys-1",
            datetime(2026, 4, 20, 0, 0),
            datetime(2026, 4, 22, 23, 0),
        )
    ]


def test_execute_returns_empty_when_all_days_have_data() -> None:
    repository = FakeRepository(
        {
            datetime(2026, 4, 20, 10): 1.0,
            datetime(2026, 4, 21, 10): 2.0,
        }
    )
    use_case = GetMissingDaysInRange(repository)

    missing_days = use_case.execute("sys-1", date(2026, 4, 20), date(2026, 4, 21))

    assert missing_days == []
