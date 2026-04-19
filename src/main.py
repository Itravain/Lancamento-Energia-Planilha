import os
from datetime import datetime

from src.application.get_current_month_generation import GetCurrentMonthGeneration
from src.application.get_hourly_energy_range import GetHourlyEnergyRange
from src.infrastructure.apsystem_energy_provider import APSystemEnergyProvider
from src.infrastructure.sqlite_hourly_energy_repository import SQLiteHourlyEnergyRepository
from src.interfaces.cli import print_hourly_report, print_monthly_report


def run() -> None:
    """Compõe as dependências e executa o fluxo principal."""
    mode = os.getenv("ENERGY_MODE", "monthly").lower()
    if mode == "hourly":
        run_hourly()
        return

    use_case = GetCurrentMonthGeneration(APSystemEnergyProvider())
    report = use_case.execute()
    print_monthly_report(report)


def run_hourly() -> None:
    """Executa fluxo horário com cache-first em SQLite."""
    start_raw = os.getenv("HOURLY_START_AT")
    end_raw = os.getenv("HOURLY_END_AT")
    system_id = os.getenv("SYSTEM_ID", "")
    db_path = os.getenv("ENERGY_DB_PATH", "energy.db")

    if not start_raw or not end_raw:
        raise ValueError("Defina HOURLY_START_AT e HOURLY_END_AT no formato YYYY-MM-DD HH:MM")

    start_at = datetime.strptime(start_raw, "%Y-%m-%d %H:%M")
    end_at = datetime.strptime(end_raw, "%Y-%m-%d %H:%M")

    use_case = GetHourlyEnergyRange(
        APSystemEnergyProvider(),
        SQLiteHourlyEnergyRepository(db_path),
    )
    generation = use_case.execute(system_id, start_at, end_at)
    print_hourly_report(generation)


if __name__ == "__main__":
    run()
