from dataclasses import dataclass
from datetime import date, datetime


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


@dataclass(frozen=True)
class DailyEnergyReport:
    """Representa o resultado de geração diária detalhada por hora."""

    day: date
    hourly_generation: dict[datetime, float]

    @property
    def total_generation(self) -> float:
        """Soma os valores horários de geração do dia."""
        return sum(self.hourly_generation.values())


@dataclass(frozen=True)
class YearlyEnergyReport:
    """Representa o resultado de geração anual agregada por mês."""

    year: int
    monthly_generation: dict[str, float]

    @property
    def total_generation(self) -> float:
        """Soma os valores mensais de geração do ano."""
        return sum(self.monthly_generation.values())
