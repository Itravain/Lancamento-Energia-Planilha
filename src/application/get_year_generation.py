from src.application.ports import EnergyProvider
from src.domain.energy_report import YearlyEnergyReport


class GetYearGeneration:
    """Caso de uso para obter geração de um ano agregada por mês."""

    def __init__(self, energy_provider: EnergyProvider) -> None:
        """Inicializa o caso de uso com o provedor de energia."""
        self.energy_provider = energy_provider

    def execute(self, year: int) -> YearlyEnergyReport:
        """Consulta os 12 meses do ano e agrega por mês."""
        monthly_generation: dict[str, float] = {}
        for month in range(1, 13):
            daily = self.energy_provider.fetch_month_generation(month, year)
            monthly_generation[f"{month:02d}/{year}"] = sum(daily.values())

        return YearlyEnergyReport(
            year=year,
            monthly_generation=monthly_generation,
        )
