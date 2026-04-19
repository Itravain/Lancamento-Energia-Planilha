from datetime import datetime
from typing import Protocol

from src.domain.energy_report import HourlyEnergyRecord


class EnergyProvider(Protocol):
    """Contrato para provedores de dados de geração de energia."""

    def fetch_month_generation(self, month: int, year: int) -> dict[str, float]:
        """Retorna a geração diária de energia de um mês no formato dd/mm/aaaa."""
        ...


class HourlyEnergyProvider(Protocol):
    """Contrato para provedor de geração horária."""

    def fetch_hourly_generation(
        self,
        system_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[datetime, float]:
        """Retorna geração por hora no intervalo solicitado."""
        ...


class HourlyEnergyRepository(Protocol):
    """Contrato de persistência para geração por hora."""

    def get_range(
        self,
        system_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[datetime, float]:
        """Busca geração por hora no intervalo solicitado."""
        ...

    def upsert_many(self, records: list[HourlyEnergyRecord]) -> None:
        """Insere ou atualiza uma lista de registros horários."""
        ...
