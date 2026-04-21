import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from src.application.ports import HourlyEnergyRepository

CsvGranularity = Literal["hour", "day", "month", "year"]


class ExportCsvReport:
    """Exporta geração horária agregada em CSV por granularidade."""

    def __init__(self, repository: HourlyEnergyRepository, output_dir: Path | str = "relatorios") -> None:
        """Inicializa com repositório e diretório de saída.

        Exemplo: ExportCsvReport(repository).execute("sys-1", start_date, end_date, "month")
        """
        self.repository = repository
        self.output_dir = Path(output_dir)

    def execute(
        self,
        system_id: str,
        start_date: date,
        end_date: date,
        granularity: CsvGranularity,
        spreadsheet_compatible: bool = False,
    ) -> Path:
        """Exporta os dados do período informado para um CSV agregado.

        Exemplo: ExportCsvReport(repository).execute("sys-1", date(2026, 2, 5), date(2026, 3, 5), "month")
        """
        if start_date > end_date:
            raise ValueError(
                "Intervalo invalido recebido: "
                f"start_date={start_date!r}, end_date={end_date!r}. "
                "Esperado: start_date <= end_date."
            )
        if granularity not in {"hour", "day", "month", "year"}:
            raise ValueError(
                f"Granularidade invalida recebida: granularity={granularity!r}. "
                "Esperado: hour, day, month ou year."
            )

        start_at = datetime(start_date.year, start_date.month, start_date.day, 0, 0)
        end_at = datetime(end_date.year, end_date.month, end_date.day, 23, 0)
        generation = self.repository.get_range(system_id, start_at, end_at)
        rows = self._build_rows(generation, granularity)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / self._build_filename(start_date, end_date, granularity)

        with output_path.open("w", newline="", encoding="utf-8") as file:
            if spreadsheet_compatible:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(["energy_kwh"])
                writer.writerows([self._format_spreadsheet_row(energy) for _, energy in rows])
            else:
                writer = csv.writer(file)
                writer.writerow(["period", "energy_kwh"])
                writer.writerows(rows)

        return output_path

    def _build_rows(
        self,
        generation: dict[datetime, float],
        granularity: CsvGranularity,
    ) -> list[tuple[str, float]]:
        """Agrupa a geração por granularidade e ordena a saída."""
        grouped: dict[str, float] = defaultdict(float)
        for generation_at, energy in generation.items():
            grouped[self._group_key(generation_at, granularity)] += energy

        return [(period, grouped[period]) for period in sorted(grouped.keys())]

    def _group_key(self, generation_at: datetime, granularity: CsvGranularity) -> str:
        """Converte a data/hora em chave textual estável para agrupamento."""
        if granularity == "hour":
            return generation_at.strftime("%Y-%m-%d %H:00")
        if granularity == "day":
            return generation_at.strftime("%Y-%m-%d")
        if granularity == "month":
            return generation_at.strftime("%Y-%m")
        if granularity == "year":
            return generation_at.strftime("%Y")
        raise ValueError(
            f"Granularidade invalida recebida: granularity={granularity!r}. "
            "Esperado: hour, day, month ou year."
        )

    def _format_spreadsheet_row(self, energy: float) -> list[str]:
        """Formata a energia para colar direto em planilha com separador ';'."""
        return [str(energy).replace(".", ",")]

    def _build_filename(self, start_date: date, end_date: date, granularity: CsvGranularity) -> str:
        """Monta nome estável do arquivo CSV exportado."""
        return (
            f"relat_{start_date.strftime('%d-%m-%Y')}_"
            f"{end_date.strftime('%d-%m-%Y')}_{granularity}.csv"
        )