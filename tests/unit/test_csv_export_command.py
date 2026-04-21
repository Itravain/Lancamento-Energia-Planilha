from datetime import date, datetime

import pytest

from src.application.export_csv_report import ExportCsvReport
from src.main import _parse_add_year, _parse_api_index, _parse_rm_index, parse_terminal_args
from src.interfaces.csv_export_command import handle_csv_export_command, parse_csv_export_command


pytestmark = pytest.mark.unit


def test_parse_csv_export_command_with_valid_value() -> None:
    parsed = parse_csv_export_command("csv-export:-p;05-02-2026;05-03-2026;month")

    assert parsed is not None
    start_date, end_date, granularity, spreadsheet_compatible = parsed
    assert start_date == date(2026, 2, 5)
    assert end_date == date(2026, 3, 5)
    assert granularity == "month"
    assert spreadsheet_compatible is True


def test_parse_csv_export_command_without_flag() -> None:
    parsed = parse_csv_export_command("csv-export:05-02-2026;05-03-2026;month")

    assert parsed is not None
    *_, spreadsheet_compatible = parsed
    assert spreadsheet_compatible is False


def test_parse_csv_export_command_with_single_date() -> None:
    parsed = parse_csv_export_command("csv-export:05-02-2026;month")

    assert parsed is not None
    start_date, end_date, granularity, spreadsheet_compatible = parsed
    assert start_date == date(2026, 2, 5)
    assert end_date is None
    assert granularity == "month"
    assert spreadsheet_compatible is False


def test_parse_csv_export_command_with_invalid_value() -> None:
    assert parse_csv_export_command("csv-export:05-02-2026;05-03-2026;week") is None
    assert parse_csv_export_command("csv-export:05-03-2026;05-02-2026;month") is None
    assert parse_csv_export_command("csv-export") is None


def test_handle_csv_export_command_writes_report(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class FakeRepository:
        def get_range(self, system_id: str, start_at: datetime, end_at: datetime) -> dict[datetime, float]:
            return {datetime(2026, 2, 5, 10): 1.0}

    tmp_dir = tmp_path / "workspace"
    tmp_dir.mkdir()
    monkeypatch.chdir(tmp_dir)

    handled = handle_csv_export_command(
        "csv-export:05-02-2026;05-02-2026;hour",
        FakeRepository(),
        object(),
        "sys-1",
    )

    assert handled is True
    assert (tmp_dir / "relatorios" / "relat_05-02-2026_05-02-2026_hour.csv").exists()
    assert any("CSV exportado com sucesso" in line for line in capsys.readouterr().out.splitlines())


def test_handle_csv_export_command_writes_spreadsheet_report(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRepository:
        def get_range(self, system_id: str, start_at: datetime, end_at: datetime) -> dict[datetime, float]:
            return {
                datetime(2026, 2, 5, 10): 1.0,
                datetime(2026, 2, 6, 10): 2.0,
            }

    tmp_dir = tmp_path / "workspace"
    tmp_dir.mkdir()
    monkeypatch.chdir(tmp_dir)

    handled = handle_csv_export_command(
        "csv-export:-p;05-02-2026;06-02-2026;day",
        FakeRepository(),
        object(),
        "sys-1",
    )

    output_path = tmp_dir / "relatorios" / "relat_05-02-2026_06-02-2026_day.csv"

    assert handled is True
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").splitlines() == [
        "energy_kwh",
        "1,0",
        "2,0",
    ]


def test_handle_csv_export_command_with_single_date_uses_today(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRepository:
        def __init__(self) -> None:
            self.calls: list[tuple[str, datetime, datetime]] = []

        def get_range(self, system_id: str, start_at: datetime, end_at: datetime) -> dict[datetime, float]:
            self.calls.append((system_id, start_at, end_at))
            return {datetime(2026, 2, 5, 10): 1.0}

    class FakeDate(date):
        @classmethod
        def today(cls) -> date:
            return cls(2026, 4, 21)

    tmp_dir = tmp_path / "workspace"
    tmp_dir.mkdir()
    monkeypatch.chdir(tmp_dir)
    monkeypatch.setattr("src.interfaces.csv_export_command.date", FakeDate)
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")

    repository = FakeRepository()
    handled = handle_csv_export_command(
        "csv-export:05-02-2026;month",
        repository,
        object(),
        "sys-1",
    )

    assert handled is True
    assert repository.calls == [
        (
            "sys-1",
            datetime(2026, 2, 5, 0, 0),
            datetime(2026, 4, 19, 23, 0),
        )
    ]


def test_handle_csv_export_command_rejects_invalid_command(capsys: pytest.CaptureFixture[str]) -> None:
    class FakeRepository:
        def get_range(self, system_id: str, start_at: datetime, end_at: datetime) -> dict[datetime, float]:
            return {}

    handled = handle_csv_export_command(
        "csv-export:05-02-2026;05-03-2026;week",
        FakeRepository(),
        object(),
        "sys-1",
    )

    assert handled is True
    assert "Comando csv-export inválido" in capsys.readouterr().out


def test_handle_csv_export_command_ignores_other_commands() -> None:
    class FakeRepository:
        def get_range(self, system_id: str, start_at: datetime, end_at: datetime) -> dict[datetime, float]:
            raise AssertionError("should not be called")

    assert handle_csv_export_command("add:2021", FakeRepository(), object(), "sys-1") is False


def test_handle_csv_export_command_confirms_missing_days_and_fetches_only_missing(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class FakeRepository:
        def __init__(self) -> None:
            self.calls: list[tuple[str, datetime, datetime]] = []
            self.upsert_payload: list[object] = []
            self.current = {datetime(2026, 4, 18, 10): 1.0}

        def get_range(self, system_id: str, start_at: datetime, end_at: datetime) -> dict[datetime, float]:
            self.calls.append((system_id, start_at, end_at))
            return dict(self.current)

        def upsert_many(self, records: list[object]) -> None:
            self.upsert_payload.extend(records)
            self.current.update({record.generation_at: record.energy_kwh for record in records})

    class FakeProvider:
        def __init__(self) -> None:
            self.calls: list[tuple[str, datetime, datetime]] = []

        def fetch_hourly_generation(
            self,
            system_id: str,
            start_at: datetime,
            end_at: datetime,
        ) -> dict[datetime, float]:
            self.calls.append((system_id, start_at, end_at))
            return {datetime(2026, 4, 19, 10): 2.0}

    class FakeDate(date):
        @classmethod
        def today(cls) -> date:
            return cls(2026, 4, 21)

    tmp_dir = tmp_path / "workspace"
    tmp_dir.mkdir()
    monkeypatch.chdir(tmp_dir)
    monkeypatch.setattr("src.interfaces.csv_export_command.date", FakeDate)
    monkeypatch.setattr("builtins.input", lambda _prompt: "s")

    repository = FakeRepository()
    provider = FakeProvider()

    handled = handle_csv_export_command(
        "csv-export:18-04-2026;day",
        repository,
        provider,
        "sys-1",
    )

    assert handled is True
    assert len(provider.calls) == 1
    assert provider.calls[0] == (
        "sys-1",
        datetime(2026, 4, 19, 0, 0),
        datetime(2026, 4, 19, 23, 0),
    )
    assert len(repository.upsert_payload) == 1
    assert any("Dias sem dados no banco" in line for line in capsys.readouterr().out.splitlines())


def test_handle_csv_export_command_cancels_when_missing_days_not_confirmed(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class FakeRepository:
        def get_range(self, system_id: str, start_at: datetime, end_at: datetime) -> dict[datetime, float]:
            return {}

        def upsert_many(self, records: list[object]) -> None:
            raise AssertionError("nao deve persistir sem confirmacao")

    class FakeProvider:
        def fetch_hourly_generation(
            self,
            system_id: str,
            start_at: datetime,
            end_at: datetime,
        ) -> dict[datetime, float]:
            raise AssertionError("nao deve chamar API sem confirmacao")

    class FakeDate(date):
        @classmethod
        def today(cls) -> date:
            return cls(2026, 4, 21)

    tmp_dir = tmp_path / "workspace"
    tmp_dir.mkdir()
    monkeypatch.chdir(tmp_dir)
    monkeypatch.setattr("src.interfaces.csv_export_command.date", FakeDate)
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")

    handled = handle_csv_export_command(
        "csv-export:18-04-2026;day",
        FakeRepository(),
        FakeProvider(),
        "sys-1",
    )

    assert handled is True
    output_lines = capsys.readouterr().out.splitlines()
    assert any("Dias sem dados no banco" in line for line in output_lines)
    assert any("Exportação cancelada pelo usuário." in line for line in output_lines)


def test_handle_csv_export_command_rejects_interval_after_today_cutoff(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class FakeRepository:
        def get_range(self, system_id: str, start_at: datetime, end_at: datetime) -> dict[datetime, float]:
            raise AssertionError("nao deve consultar banco com intervalo invalido")

    class FakeProvider:
        def fetch_hourly_generation(
            self,
            system_id: str,
            start_at: datetime,
            end_at: datetime,
        ) -> dict[datetime, float]:
            raise AssertionError("nao deve chamar API com intervalo invalido")

    class FakeDate(date):
        @classmethod
        def today(cls) -> date:
            return cls(2026, 4, 21)

    monkeypatch.setattr("src.interfaces.csv_export_command.date", FakeDate)

    handled = handle_csv_export_command(
        "csv-export:21-04-2026;day",
        FakeRepository(),
        FakeProvider(),
        "sys-1",
    )

    assert handled is True
    assert "Intervalo de exportação inválido após ajuste de confiabilidade" in capsys.readouterr().out


def test_execute_raises_for_invalid_granularity(tmp_path: pytest.TempPathFactory) -> None:
    class FakeRepository:
        def get_range(self, system_id: str, start_at: datetime, end_at: datetime) -> dict[datetime, float]:
            return {}

    use_case = ExportCsvReport(FakeRepository(), output_dir=tmp_path / "relatorios")

    with pytest.raises(ValueError, match=r"granularity=.*hour, day, month ou year"):
        use_case.execute("sys-1", date(2026, 2, 5), date(2026, 3, 5), "week")


def test_parse_hourly_args_with_explicit_period() -> None:
    args = parse_terminal_args(
        [
            "hourly",
            "--system-id",
            "sys-1",
            "--start",
            "2026-04-19 10:00",
            "--end",
            "2026-04-19 12:00",
            "--db-path",
            "cache.db",
        ]
    )

    assert args.command == "hourly"
    assert args.system_id == "sys-1"
    assert args.start == "2026-04-19 10:00"
    assert args.end == "2026-04-19 12:00"
    assert args.db_path == "cache.db"


def test_parse_daily_defaults() -> None:
    args = parse_terminal_args(["daily"])

    assert args.command == "daily"
    assert args.date is None


def test_parse_monthly_defaults() -> None:
    args = parse_terminal_args(["monthly"])

    assert args.command == "monthly"
    assert args.month is None
    assert args.year is None


def test_parse_yearly_defaults() -> None:
    args = parse_terminal_args(["yearly"])

    assert args.command == "yearly"
    assert args.year is None


def test_parse_menu_command() -> None:
    args = parse_terminal_args(["menu"])

    assert args.command == "menu"


def test_parse_api_index_with_valid_value() -> None:
    assert _parse_api_index("api:05") == 5


def test_parse_api_index_with_invalid_value() -> None:
    assert _parse_api_index("api:xx") is None
    assert _parse_api_index("api") is None


def test_parse_add_year_with_valid_value() -> None:
    assert _parse_add_year("add:2021") == 2021


def test_parse_add_year_with_invalid_value() -> None:
    assert _parse_add_year("add:21") is None
    assert _parse_add_year("add:abcd") is None
    assert _parse_add_year("add") is None


def test_parse_rm_index_with_valid_value() -> None:
    assert _parse_rm_index("rm:2") == 2


def test_parse_rm_index_with_invalid_value() -> None:
    assert _parse_rm_index("rm:xx") is None
    assert _parse_rm_index("rm") is None