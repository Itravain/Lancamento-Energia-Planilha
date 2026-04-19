from datetime import datetime

import pytest

from src.application.get_hourly_energy_range import GetHourlyEnergyRange
from src.domain.energy_report import HourlyEnergyRecord


pytestmark = pytest.mark.unit


class FakeHourlyProvider:
    def __init__(self, payload: dict[datetime, float]) -> None:
        self.payload = payload
        self.calls: list[tuple[str, datetime, datetime]] = []

    def fetch_hourly_generation(
        self,
        system_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[datetime, float]:
        self.calls.append((system_id, start_at, end_at))
        return self.payload


class FailingHourlyProvider:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_hourly_generation(
        self,
        system_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[datetime, float]:
        self.calls += 1
        raise RuntimeError("api down")


class FakeHourlyRepository:
    def __init__(self, initial: dict[datetime, float] | None = None) -> None:
        self.data = dict(initial or {})
        self.upserts: list[list[HourlyEnergyRecord]] = []

    def get_range(
        self,
        system_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[datetime, float]:
        return {
            key: value
            for key, value in self.data.items()
            if start_at <= key <= end_at
        }

    def upsert_many(self, records: list[HourlyEnergyRecord]) -> None:
        self.upserts.append(records)
        for item in records:
            self.data[item.generation_at] = item.energy_kwh


def test_execute_returns_cache_without_api_call() -> None:
    start = datetime(2026, 4, 19, 10)
    end = datetime(2026, 4, 19, 12)
    cached = {
        datetime(2026, 4, 19, 10): 1.1,
        datetime(2026, 4, 19, 11): 1.2,
        datetime(2026, 4, 19, 12): 1.3,
    }
    provider = FakeHourlyProvider(payload={})
    repository = FakeHourlyRepository(initial=cached)

    use_case = GetHourlyEnergyRange(provider, repository)
    result = use_case.execute("sys-1", start, end)

    assert result == cached
    assert provider.calls == []
    assert repository.upserts == []


def test_execute_fetches_missing_and_persists() -> None:
    start = datetime(2026, 4, 19, 10)
    end = datetime(2026, 4, 19, 12)
    provider_data = {
        datetime(2026, 4, 19, 10): 1.1,
        datetime(2026, 4, 19, 11): 1.2,
        datetime(2026, 4, 19, 12): 1.3,
    }
    provider = FakeHourlyProvider(payload=provider_data)
    repository = FakeHourlyRepository(initial={})

    use_case = GetHourlyEnergyRange(provider, repository)
    result = use_case.execute("sys-1", start, end)

    assert provider.calls == [("sys-1", start, end)]
    assert len(repository.upserts) == 1
    assert result == provider_data


def test_execute_raises_for_invalid_range() -> None:
    provider = FakeHourlyProvider(payload={})
    repository = FakeHourlyRepository(initial={})
    use_case = GetHourlyEnergyRange(provider, repository)

    with pytest.raises(ValueError):
        use_case.execute(
            "sys-1",
            datetime(2026, 4, 20, 10),
            datetime(2026, 4, 19, 10),
        )


def test_execute_returns_cached_data_when_provider_fails() -> None:
    """Quando a API falha, deve retornar o cache já disponível."""
    start = datetime(2026, 4, 19, 10)
    end = datetime(2026, 4, 19, 12)
    cached = {
        datetime(2026, 4, 19, 10): 1.1,
        datetime(2026, 4, 19, 11): 1.2,
    }
    provider = FailingHourlyProvider()
    repository = FakeHourlyRepository(initial=cached)

    use_case = GetHourlyEnergyRange(provider, repository)
    result = use_case.execute("sys-1", start, end)

    assert provider.calls == 1
    assert result == cached
