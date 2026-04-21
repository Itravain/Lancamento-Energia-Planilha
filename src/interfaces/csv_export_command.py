from datetime import date, datetime, timedelta

from src.application.get_missing_days_in_range import GetMissingDaysInRange
from src.application.export_csv_report import CsvGranularity, ExportCsvReport
from src.application.ports import HourlyEnergyProvider, HourlyEnergyRepository
from src.domain.energy_report import HourlyEnergyRecord


def parse_csv_export_command(raw: str) -> tuple[date, date | None, CsvGranularity, bool] | None:
    """Extrai comando csv-export com opcional -p para planilha.

    Exemplo: parse_csv_export_command("csv-export:-p;05-02-2026;05-03-2026;month")
    """
    if not raw.startswith("csv-export:"):
        return None

    payload = raw.split(":", maxsplit=1)[1]
    parts = [item.strip().lower() for item in payload.split(";") if item.strip()]
    spreadsheet_compatible = "-p" in parts
    parts = [item for item in parts if item != "-p"]
    if len(parts) not in {2, 3}:
        return None

    start_raw = parts[0]
    end_raw = parts[1] if len(parts) == 3 else None
    granularity = parts[-1]
    if granularity not in {"hour", "day", "month", "year"}:
        return None

    try:
        start_date = datetime.strptime(start_raw, "%d-%m-%Y").date()
    except ValueError:
        return None

    end_date = None
    if end_raw is not None:
        try:
            end_date = datetime.strptime(end_raw, "%d-%m-%Y").date()
        except ValueError:
            return None
        if start_date > end_date:
            return None

    return start_date, end_date, granularity, spreadsheet_compatible


def handle_csv_export_command(
    raw: str,
    repository: HourlyEnergyRepository,
    provider: HourlyEnergyProvider,
    system_id: str,
) -> bool:
    """Exporta relatórios CSV quando o comando for reconhecido.

    Exemplo: handle_csv_export_command("csv-export:-p;05-02-2026;05-03-2026;month", repo, provider, "sys-1")
    """
    if not raw.startswith("csv-export:"):
        return False

    parsed = parse_csv_export_command(raw)
    if parsed is None:
        print("Comando csv-export inválido. Use csv-export:[-p;]DD-MM-AAAA[;DD-MM-AAAA];hour|day|month|year.")
        return True

    start_date, end_date, granularity, spreadsheet_compatible = parsed
    if end_date is None:
        end_date = date.today()

    effective_end_date = end_date
    if end_date == date.today():
        effective_end_date = end_date - timedelta(days=2)

    if start_date > effective_end_date:
        print(
            "Intervalo de exportação inválido após ajuste de confiabilidade. "
            f"Recebido: start_date={start_date.strftime('%d-%m-%Y')}, "
            f"end_date_efetivo={effective_end_date.strftime('%d-%m-%Y')}."
        )
        return True

    if end_date == date.today():
        missing_days = GetMissingDaysInRange(repository).execute(system_id, start_date, effective_end_date)
        if missing_days:
            print("Dias sem dados no banco:")
            for missing_day in missing_days:
                print(f"- {missing_day.strftime('%d-%m-%Y')}")

            confirmation = input("Deseja buscar apenas os dias faltantes na API? (s/n): ").strip().lower()
            if confirmation not in {"s", "sim"}:
                print("Exportação cancelada pelo usuário.")
                return True

            inserted_records = _fetch_missing_days_to_cache(
                provider,
                repository,
                system_id,
                missing_days,
            )
            print(
                "Busca de dias faltantes concluída. "
                f"Registros persistidos: {inserted_records}."
            )

    exporter = ExportCsvReport(repository)
    output_path = exporter.execute(
        system_id,
        start_date,
        effective_end_date,
        granularity,
        spreadsheet_compatible,
    )
    print(f"CSV exportado com sucesso em {output_path}")
    return True


def _fetch_missing_days_to_cache(
    provider: HourlyEnergyProvider,
    repository: HourlyEnergyRepository,
    system_id: str,
    missing_days: list[date],
) -> int:
    """Busca e persiste dados apenas para os dias faltantes no cache local."""
    inserted_records = 0
    for missing_day in missing_days:
        start_at = datetime(missing_day.year, missing_day.month, missing_day.day, 0, 0)
        end_at = datetime(missing_day.year, missing_day.month, missing_day.day, 23, 0)
        generation = provider.fetch_hourly_generation(system_id, start_at, end_at)
        if not generation:
            continue

        records = [
            HourlyEnergyRecord(system_id, generation_at, energy)
            for generation_at, energy in generation.items()
        ]
        repository.upsert_many(records)
        inserted_records += len(records)

    return inserted_records