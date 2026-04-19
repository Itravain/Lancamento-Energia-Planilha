from datetime import datetime

import pytest

from src.application.get_hourly_energy_range import GetHourlyEnergyRange
from src.infrastructure.sqlite_hourly_energy_repository import SQLiteHourlyEnergyRepository


pytestmark = pytest.mark.integration


class FakeHourlyProvider:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_hourly_generation(
        self,
        system_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[datetime, float]:
        self.calls += 1
        return {
            datetime(2026, 4, 19, 10): 1.1,
            datetime(2026, 4, 19, 11): 1.2,
        }


def test_second_execution_reads_from_sqlite_cache(tmp_path: pytest.TempPathFactory) -> None:
    repository = SQLiteHourlyEnergyRepository(str(tmp_path / "energy.db"))
    provider = FakeHourlyProvider()
    use_case = GetHourlyEnergyRange(provider, repository)
    start = datetime(2026, 4, 19, 10)
    end = datetime(2026, 4, 19, 11)

    first = use_case.execute("sys-1", start, end)
    second = use_case.execute("sys-1", start, end)

    assert first == second
    assert provider.calls == 1
