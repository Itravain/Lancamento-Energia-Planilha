from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MonthlyEnergyReport:
    """Representa o resultado de geração diária de um mês."""

    month: int
    year: int
    daily_generation: dict[str, float]

    @property
    def total_generation(self) -> float:
        """Soma os valores diários de geração do relatório."""
        return sum(self.daily_generation.values())


@dataclass(frozen=True)
class HourlyEnergyRecord:
    """Representa um registro de geração de energia por hora."""

    system_id: str
    generation_at: datetime
    energy_kwh: float
