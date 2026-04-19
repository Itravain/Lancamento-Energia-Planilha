import argparse
import os
from datetime import date, datetime

from src.application.get_current_month_generation import GetCurrentMonthGeneration
from src.application.get_day_generation import GetDayGeneration
from src.application.get_hourly_energy_range import GetHourlyEnergyRange
from src.application.get_month_generation import GetMonthGeneration
from src.application.get_year_generation import GetYearGeneration
from src.infrastructure.apsystem_energy_provider import APSystemEnergyProvider
from src.infrastructure.sqlite_hourly_energy_repository import SQLiteHourlyEnergyRepository
from src.interfaces.cli import (
    print_daily_report,
    print_hourly_report,
    print_monthly_report,
    print_yearly_report,
)


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
    if not system_id:
        raise ValueError("Defina SYSTEM_ID para executar o modo horário.")

    start_at = datetime.strptime(start_raw, "%Y-%m-%d %H:%M")
    end_at = datetime.strptime(end_raw, "%Y-%m-%d %H:%M")

    use_case = GetHourlyEnergyRange(
        APSystemEnergyProvider(),
        SQLiteHourlyEnergyRepository(db_path),
    )
    generation = use_case.execute(system_id, start_at, end_at)
    print_hourly_report(generation)


def parse_terminal_args(argv: list[str]) -> argparse.Namespace:
    """Parseia argumentos da CLI de monitoramento."""
    parser = argparse.ArgumentParser(prog="energia")
    subparsers = parser.add_subparsers(dest="command", required=True)

    hourly = subparsers.add_parser("hourly")
    hourly.add_argument("--system-id", required=True)
    hourly.add_argument("--start", required=True)
    hourly.add_argument("--end", required=True)
    hourly.add_argument("--db-path", default="energy.db")

    daily = subparsers.add_parser("daily")
    daily.add_argument("--system-id", default=os.getenv("SYSTEM_ID", ""))
    daily.add_argument("--date")
    daily.add_argument("--db-path", default="energy.db")

    monthly = subparsers.add_parser("monthly")
    monthly.add_argument("--month", type=int)
    monthly.add_argument("--year", type=int)

    yearly = subparsers.add_parser("yearly")
    yearly.add_argument("--year", type=int)

    subparsers.add_parser("menu")

    return parser.parse_args(argv)


def run_hourly_command(command_args: argparse.Namespace) -> None:
    """Executa subcomando hourly com argumentos explícitos."""
    start_at = datetime.strptime(command_args.start, "%Y-%m-%d %H:%M")
    end_at = datetime.strptime(command_args.end, "%Y-%m-%d %H:%M")

    use_case = GetHourlyEnergyRange(
        APSystemEnergyProvider(),
        SQLiteHourlyEnergyRepository(command_args.db_path),
    )
    generation = use_case.execute(command_args.system_id, start_at, end_at)
    print_hourly_report(generation)


def run_daily_command(command_args: argparse.Namespace) -> None:
    """Executa subcomando daily com defaults para o dia atual."""
    if not command_args.system_id:
        raise ValueError("Defina --system-id ou SYSTEM_ID para modo daily.")

    target_day = (
        datetime.strptime(command_args.date, "%Y-%m-%d").date()
        if command_args.date
        else date.today()
    )
    hourly_use_case = GetHourlyEnergyRange(
        APSystemEnergyProvider(),
        SQLiteHourlyEnergyRepository(command_args.db_path),
    )
    day_use_case = GetDayGeneration(hourly_use_case)
    report = day_use_case.execute(command_args.system_id, target_day)
    print_daily_report(report)


def run_monthly_command(command_args: argparse.Namespace) -> None:
    """Executa subcomando monthly com defaults para mês/ano atuais."""
    today = date.today()
    month = command_args.month if command_args.month is not None else today.month
    year = command_args.year if command_args.year is not None else today.year

    use_case = GetMonthGeneration(APSystemEnergyProvider())
    report = use_case.execute(month=month, year=year)
    print_monthly_report(report)


def run_yearly_command(command_args: argparse.Namespace) -> None:
    """Executa subcomando yearly com default para ano atual."""
    year = command_args.year if command_args.year is not None else date.today().year
    use_case = GetYearGeneration(APSystemEnergyProvider())
    report = use_case.execute(year)
    print_yearly_report(report)


def run_interactive_menu() -> None:
    """Executa menu simples para seleção de visão de monitoramento."""
    print("Selecione o periodo de monitoramento:")
    print("1) Horario")
    print("2) Diario")
    print("3) Mensal")
    print("4) Anual")
    choice = input("Opcao: ").strip()

    if choice == "1":
        system_id = input("System ID: ").strip()
        start = input("Inicio (YYYY-MM-DD HH:MM): ").strip()
        end = input("Fim (YYYY-MM-DD HH:MM): ").strip()
        args = parse_terminal_args([
            "hourly",
            "--system-id",
            system_id,
            "--start",
            start,
            "--end",
            end,
        ])
        run_hourly_command(args)
        return

    if choice == "2":
        run_daily_command(parse_terminal_args(["daily"]))
        return

    if choice == "3":
        run_monthly_command(parse_terminal_args(["monthly"]))
        return

    if choice == "4":
        run_yearly_command(parse_terminal_args(["yearly"]))
        return

    raise ValueError("Opcao de menu inválida.")


def run_terminal(argv: list[str]) -> None:
    """Roteia subcomandos da CLI para os respectivos handlers."""
    command_args = parse_terminal_args(argv)

    if command_args.command == "hourly":
        run_hourly_command(command_args)
        return
    if command_args.command == "daily":
        run_daily_command(command_args)
        return
    if command_args.command == "monthly":
        run_monthly_command(command_args)
        return
    if command_args.command == "yearly":
        run_yearly_command(command_args)
        return
    if command_args.command == "menu":
        run_interactive_menu()
        return

    raise ValueError("Comando inválido.")


if __name__ == "__main__":
    run()
