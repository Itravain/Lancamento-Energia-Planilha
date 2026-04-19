from datetime import date

from src.application.ports import EnergyProvider
from src.domain.energy_report import MonthlyEnergyReport


class GetCurrentMonthGeneration:
    """Caso de uso para obter a geração do mês atual."""

    def __init__(self, energy_provider: EnergyProvider) -> None:
        """Inicializa o caso de uso com o provedor de energia."""
        self.energy_provider = energy_provider

    def execute(self, today: date | None = None) -> MonthlyEnergyReport:
        """Executa a consulta da geração do mês atual."""
        current_date = today or date.today()
        generation = self.energy_provider.fetch_month_generation(
            current_date.month,
            current_date.year,
        )
        return MonthlyEnergyReport(
            month=current_date.month,
            year=current_date.year,
            daily_generation=generation,
        )
