from datetime import date, datetime

import pytest

from src.application.get_day_generation import GetDayGeneration


pytestmark = pytest.mark.unit


class FakeHourlyRangeUseCase:
    def __init__(self, payload: dict[datetime, float]) -> None:
        self.payload = payload
        self.calls: list[tuple[str, datetime, datetime]] = []

    def execute(
        self,
        system_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[datetime, float]:
        self.calls.append((system_id, start_at, end_at))
        return self.payload


def test_execute_builds_day_range_and_returns_report() -> None:
    hourly = {
        datetime(2026, 4, 19, 10): 1.1,
        datetime(2026, 4, 19, 11): 1.2,
    }
    fake_hourly_use_case = FakeHourlyRangeUseCase(hourly)
    use_case = GetDayGeneration(fake_hourly_use_case)

    report = use_case.execute("sys-1", date(2026, 4, 19))

    assert fake_hourly_use_case.calls == [
        (
            "sys-1",
            datetime(2026, 4, 19, 0, 0),
            datetime(2026, 4, 19, 23, 0),
        )
    ]
    assert report.day == date(2026, 4, 19)
    assert report.hourly_generation == hourly
    assert report.total_generation == 2.3
