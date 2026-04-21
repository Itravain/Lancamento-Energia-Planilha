from src.application.ports import EnergyProvider
from src.domain.energy_report import MonthlyEnergyReport


class GetMonthGeneration:
    """Caso de uso para obter geração de um mês específico."""

    def __init__(self, energy_provider: EnergyProvider) -> None:
        """Inicializa o caso de uso com o provedor de energia."""
        self.energy_provider = energy_provider

    def execute(self, month: int, year: int) -> MonthlyEnergyReport:
        """Executa a consulta de geração de um mês informado."""
        if month < 1 or month > 12:
            raise ValueError("Mes inválido. Informe valor entre 1 e 12.")

        generation = self.energy_provider.fetch_month_generation(month, year)
        return MonthlyEnergyReport(
            month=month,
            year=year,
            daily_generation=generation,
        )
