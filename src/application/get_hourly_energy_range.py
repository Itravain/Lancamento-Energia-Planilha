from datetime import datetime, timedelta

from src.application.ports import HourlyEnergyProvider, HourlyEnergyRepository
from src.domain.energy_report import HourlyEnergyRecord


class GetHourlyEnergyRange:
    """Caso de uso cache-first para geração de energia por hora."""

    def __init__(
        self,
        energy_provider: HourlyEnergyProvider,
        repository: HourlyEnergyRepository,
    ) -> None:
        """Inicializa com provedor de API e repositório de persistência."""
        self.energy_provider = energy_provider
        self.repository = repository

    def execute(
        self,
        system_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[datetime, float]:
        """Retorna energia horária do intervalo consultando cache antes da API."""
        if start_at > end_at:
            raise ValueError("Intervalo inválido: start_at deve ser <= end_at.")

        cached = self.repository.get_range(system_id, start_at, end_at)
        expected_hours = self._build_expected_hours(start_at, end_at)
        missing_hours = [hour for hour in expected_hours if hour not in cached]

        if missing_hours:
            try:
                fetched = self.energy_provider.fetch_hourly_generation(system_id, start_at, end_at)
            except Exception:
                return {hour: cached[hour] for hour in sorted(cached.keys())}
            to_persist = [
                HourlyEnergyRecord(system_id, hour, energy)
                for hour, energy in fetched.items()
                if hour in missing_hours
            ]
            if to_persist:
                self.repository.upsert_many(to_persist)
                cached.update({item.generation_at: item.energy_kwh for item in to_persist})

        return {hour: cached[hour] for hour in sorted(cached.keys())}

    def _build_expected_hours(self, start_at: datetime, end_at: datetime) -> list[datetime]:
        """Monta lista de horas esperadas no intervalo fechado."""
        hours: list[datetime] = []
        current = start_at
        while current <= end_at:
            hours.append(current)
            current += timedelta(hours=1)
        return hours
