from datetime import date, datetime

from src.domain.energy_report import DailyEnergyReport


class GetDayGeneration:
    """Caso de uso para obter geração detalhada de um dia."""

    def __init__(self, hourly_range_use_case: object) -> None:
        """Recebe um caso de uso compatível com consulta horária por intervalo."""
        self.hourly_range_use_case = hourly_range_use_case

    def execute(self, system_id: str, day: date) -> DailyEnergyReport:
        """Consulta geração horária do dia e retorna relatório diário."""
        start_at = datetime(day.year, day.month, day.day, 0, 0)
        end_at = datetime(day.year, day.month, day.day, 23, 0)
        hourly_generation = self.hourly_range_use_case.execute(system_id, start_at, end_at)
        return DailyEnergyReport(day=day, hourly_generation=hourly_generation)
