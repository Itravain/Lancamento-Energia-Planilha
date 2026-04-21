from datetime import date, datetime, timedelta

from src.application.ports import HourlyEnergyRepository


class GetMissingDaysInRange:
    """Identifica dias sem qualquer dado horário no intervalo informado."""

    def __init__(self, repository: HourlyEnergyRepository) -> None:
        """Inicializa com repositório de geração horária."""
        self.repository = repository

    def execute(self, system_id: str, start_date: date, end_date: date) -> list[date]:
        """Retorna dias faltantes ordenados no intervalo fechado start_date..end_date."""
        start_at = datetime(start_date.year, start_date.month, start_date.day, 0, 0)
        end_at = datetime(end_date.year, end_date.month, end_date.day, 23, 0)
        generation = self.repository.get_range(system_id, start_at, end_at)

        existing_days = {generation_at.date() for generation_at in generation.keys()}
        missing_days: list[date] = []
        day_cursor = start_date
        while day_cursor <= end_date:
            if day_cursor not in existing_days:
                missing_days.append(day_cursor)
            day_cursor += timedelta(days=1)
        return missing_days
