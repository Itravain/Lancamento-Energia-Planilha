import argparse
import os
import shlex
from datetime import date, datetime

from dotenv import load_dotenv

from src.application.get_current_month_generation import GetCurrentMonthGeneration
from src.application.get_day_generation import GetDayGeneration
from src.application.get_hourly_energy_range import GetHourlyEnergyRange
from src.application.get_month_generation import GetMonthGeneration
from src.application.get_year_generation import GetYearGeneration
from src.domain.energy_report import HourlyEnergyRecord
from src.infrastructure.apsystem_energy_provider import APSystemEnergyProvider
from src.infrastructure.sqlite_hourly_energy_repository import SQLiteHourlyEnergyRepository
from src.interfaces.cli import (
    print_daily_report,
    print_hourly_report,
    print_monthly_report,
    print_yearly_report,
)


# Carrega .env automaticamente para CLI funcionar sem export manual.
load_dotenv()


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


def run_hybrid_interface() -> None:
    """Exibe menu inicial com modo comandos legado ou modo interativo hierárquico."""
    while True:
        print("Modo de entrada")
        print("1) Modo comandos (legado)")
        print("2) Modo interativo (hierárquico)")
        print("q) Sair")

        choice = input("Opcao: ").strip().lower()
        if choice == "q":
            return
        if choice == "1":
            command_line = input("Digite o comando (ex: monthly --month 4 --year 2026): ").strip()
            if not command_line:
                print("Comando vazio. Retornando ao menu inicial.")
                continue
            try:
                run_terminal(shlex.split(command_line))
            except (ValueError, SystemExit) as error:
                print(f"Erro no modo comandos: {error}")
            continue
        if choice == "2":
            try:
                run_hierarchical_navigation()
            except ValueError as error:
                print(f"Erro no modo interativo: {error}")
            continue

        print("Opcao inválida.")


def run_hierarchical_navigation() -> None:
    """Navega por ano -> mês -> dia -> hora usando somente dados já no banco."""
    system_id = os.getenv("SYSTEM_ID", "").strip()
    if not system_id:
        system_id = input("SYSTEM_ID não definido. Informe o System ID (ou q para voltar): ").strip()
        if not system_id or system_id.lower() == "q":
            print("Modo interativo cancelado: SYSTEM_ID não informado.")
            return

    db_path = os.getenv("ENERGY_DB_PATH", "energy.db")
    repository = SQLiteHourlyEnergyRepository(db_path)
    provider = APSystemEnergyProvider()

    selected_year: int | None = None
    selected_month: int | None = None
    selected_day: int | None = None

    while True:
        if selected_year is None:
            year_rows = repository.list_years(system_id)
            print("\nNível Ano")
            for index, (year, total) in enumerate(year_rows, start=1):
                print(f"{index}) {year} - total: {total:.2f}")
            print("Use o índice para entrar em um ano.")
            print("Use add:<ano> para navegar para um novo ano (ex: add:2021).")
            print("0) Voltar")
            print("q) Sair")
            raw = input("Opcao: ").strip().lower()
            if raw == "q":
                return
            if raw == "0":
                continue
            if raw.startswith("add:"):
                add_year = _parse_add_year(raw)
                max_year = date.today().year + 1
                if add_year is None or add_year < 1900 or add_year > max_year:
                    print(f"Ano inválido. Use add:AAAA entre 1900 e {max_year}.")
                    continue
                selected_year = add_year
                continue
            if raw.isdigit() and 1 <= int(raw) <= len(year_rows):
                selected_year = year_rows[int(raw) - 1][0]
                continue
            print("Opcao inválida.")
            continue

        if selected_month is None:
            month_rows = repository.list_months(system_id, selected_year)
            print(f"\nNível Mês - Ano {selected_year}")
            for index, (month, total) in enumerate(month_rows, start=1):
                print(f"{index}) {month:02d} - total: {total:.2f}")
            print("Use o índice para entrar em um mês.")
            print("Use api:<mes> para buscar novo mês (ex: api:05).")
            print("Use rm:<indice> para remover um mês listado (ex: rm:2).")
            print("0) Voltar")
            print("q) Sair")
            raw = input("Opcao: ").strip().lower()
            if raw == "q":
                return
            if raw == "0":
                selected_year = None
                continue
            if raw.startswith("api:"):
                api_value = _parse_api_index(raw)
                if api_value is None or api_value < 1 or api_value > 12:
                    print("Indice de API inválido para mês. Use 1..12.")
                    continue
                print(f"Puxando mês {api_value:02d}/{selected_year} da API...")
                inserted = _fetch_month_to_cache(provider, repository, system_id, selected_year, api_value)
                print(f"Mês {api_value:02d}/{selected_year} concluído.")
                if inserted:
                    print("Dados do mês persistidos com sucesso.")
                else:
                    print("Nenhum dado retornado pela API para o mês solicitado.")
                continue
            if raw.startswith("rm:"):
                remove_index = _parse_rm_index(raw)
                if remove_index is None or remove_index < 1 or remove_index > len(month_rows):
                    print("Indice de remoção inválido para mês. Use 1..N da lista.")
                    continue
                target_month = month_rows[remove_index - 1][0]
                deleted = repository.delete_month(system_id, selected_year, target_month)
                print(
                    f"Mês {target_month:02d}/{selected_year} removido. "
                    f"Registros apagados: {deleted}."
                )
                continue
            if raw.isdigit() and 1 <= int(raw) <= len(month_rows):
                selected_month = month_rows[int(raw) - 1][0]
                continue
            print("Opcao inválida.")
            continue

        if selected_day is None:
            day_rows = repository.list_days(system_id, selected_year, selected_month)
            print(f"\nNível Dia - {selected_month:02d}/{selected_year}")
            for index, (day, total) in enumerate(day_rows, start=1):
                print(f"{index}) {day:02d} - total: {total:.2f}")
            print("Use o índice para entrar em um dia.")
            print("Use api:<dia> para buscar novo dia (ex: api:19).")
            print("Use rm:<indice> para remover um dia listado (ex: rm:2).")
            print("0) Voltar")
            print("q) Sair")
            raw = input("Opcao: ").strip().lower()
            if raw == "q":
                return
            if raw == "0":
                selected_month = None
                continue
            if raw.startswith("api:"):
                api_value = _parse_api_index(raw)
                if api_value is None or api_value < 1 or api_value > 31:
                    print("Indice de API inválido para dia. Use 1..31.")
                    continue
                _fetch_day_to_cache(provider, repository, system_id, selected_year, selected_month, api_value)
                print("Dados do dia persistidos com sucesso.")
                continue
            if raw.startswith("rm:"):
                remove_index = _parse_rm_index(raw)
                if remove_index is None or remove_index < 1 or remove_index > len(day_rows):
                    print("Indice de remoção inválido para dia. Use 1..N da lista.")
                    continue
                target_day = day_rows[remove_index - 1][0]
                deleted = repository.delete_day(system_id, selected_year, selected_month, target_day)
                print(
                    f"Dia {target_day:02d}/{selected_month:02d}/{selected_year} removido. "
                    f"Registros apagados: {deleted}."
                )
                continue
            if raw.isdigit() and 1 <= int(raw) <= len(day_rows):
                selected_day = day_rows[int(raw) - 1][0]
                continue
            print("Opcao inválida.")
            continue

        hour_rows = repository.list_hours(system_id, selected_year, selected_month, selected_day)
        print(f"\nNível Hora - {selected_day:02d}/{selected_month:02d}/{selected_year}")
        for hour, energy in hour_rows:
            print(f"{hour:02d}:00 -> {energy}")
        print("Comando api:indice não permitido neste nível.")
        print("0) Voltar")
        print("q) Sair")
        raw = input("Opcao: ").strip().lower()
        if raw == "q":
            return
        if raw == "0":
            selected_day = None
            continue
        print("Opcao inválida.")


def _parse_api_index(raw: str) -> int | None:
    """Extrai índice numérico de comandos no formato api:<indice>."""
    parts = raw.split(":", maxsplit=1)
    if len(parts) != 2:
        return None
    if not parts[1].isdigit():
        return None
    return int(parts[1])


def _parse_add_year(raw: str) -> int | None:
    """Extrai ano de comandos no formato add:AAAA."""
    parts = raw.split(":", maxsplit=1)
    if len(parts) != 2:
        return None
    if len(parts[1]) != 4 or not parts[1].isdigit():
        return None
    return int(parts[1])


def _parse_rm_index(raw: str) -> int | None:
    """Extrai índice numérico de comandos no formato rm:<indice>."""
    parts = raw.split(":", maxsplit=1)
    if len(parts) != 2:
        return None
    if not parts[1].isdigit():
        return None
    return int(parts[1])


def _fetch_month_to_cache(
    provider: APSystemEnergyProvider,
    repository: SQLiteHourlyEnergyRepository,
    system_id: str,
    year: int,
    month: int,
) -> int:
    """Busca todas as horas de um mês na API e persiste no cache."""
    start_at, end_at = repository.month_day_bounds(year, month)
    generation = provider.fetch_hourly_generation(system_id, start_at, end_at)
    if not generation:
        return 0
    records = [
        HourlyEnergyRecord(
            system_id,
            generation_at,
            energy,
        )
        for generation_at, energy in generation.items()
    ]
    repository.upsert_many(records)
    return len(records)


def _fetch_day_to_cache(
    provider: APSystemEnergyProvider,
    repository: SQLiteHourlyEnergyRepository,
    system_id: str,
    year: int,
    month: int,
    day: int,
) -> None:
    """Busca todas as horas de um dia na API e persiste no cache."""
    start_at = datetime(year, month, day, 0, 0)
    end_at = datetime(year, month, day, 23, 0)
    generation = provider.fetch_hourly_generation(system_id, start_at, end_at)
    if not generation:
        return
    records = [
        HourlyEnergyRecord(
            system_id,
            generation_at,
            energy,
        )
        for generation_at, energy in generation.items()
    ]
    repository.upsert_many(records)


if __name__ == "__main__":
    run()
