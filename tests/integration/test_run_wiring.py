import pytest

from src.domain.energy_report import MonthlyEnergyReport
from src.main import run, run_hourly, run_hybrid_interface, run_hierarchical_navigation, run_terminal


pytestmark = pytest.mark.integration


def test_run_wires_dependencies_and_calls_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida composicao entre provider, caso de uso e interface CLI."""
    captured: dict[str, object] = {}

    class FakeProvider:
        pass

    class FakeUseCase:
        def __init__(self, provider: object) -> None:
            captured["provider"] = provider

        def execute(self) -> MonthlyEnergyReport:
            report = MonthlyEnergyReport(
                month=4,
                year=2026,
                daily_generation={"01/04/2026": 10.0},
            )
            captured["report"] = report
            return report

    def fake_print(report: MonthlyEnergyReport) -> None:
        captured["printed"] = report

    monkeypatch.setattr("src.main.APSystemEnergyProvider", FakeProvider)
    monkeypatch.setattr("src.main.GetCurrentMonthGeneration", FakeUseCase)
    monkeypatch.setattr("src.main.print_monthly_report", fake_print)

    run()

    assert isinstance(captured["provider"], FakeProvider)
    assert captured["printed"] == captured["report"]


def test_run_hourly_mode_wires_hourly_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida wiring do modo horário com cache e saída específica."""
    captured: dict[str, object] = {}

    class FakeProvider:
        pass

    class FakeRepo:
        def __init__(self, db_path: str) -> None:
            captured["db_path"] = db_path

    class FakeHourlyUseCase:
        def __init__(self, provider: object, repository: object) -> None:
            captured["provider"] = provider
            captured["repository"] = repository

        def execute(self, system_id: str, start_at: object, end_at: object) -> dict[object, float]:
            captured["system_id"] = system_id
            captured["start_at"] = start_at
            captured["end_at"] = end_at
            return {}

    def fake_print_hourly(result: dict[object, float]) -> None:
        captured["printed"] = result

    monkeypatch.setenv("ENERGY_MODE", "hourly")
    monkeypatch.setenv("HOURLY_START_AT", "2026-04-19 10:00")
    monkeypatch.setenv("HOURLY_END_AT", "2026-04-19 12:00")
    monkeypatch.setenv("SYSTEM_ID", "sys-1")
    monkeypatch.setenv("ENERGY_DB_PATH", "/tmp/energy.db")

    monkeypatch.setattr("src.main.APSystemEnergyProvider", FakeProvider)
    monkeypatch.setattr("src.main.SQLiteHourlyEnergyRepository", FakeRepo)
    monkeypatch.setattr("src.main.GetHourlyEnergyRange", FakeHourlyUseCase)
    monkeypatch.setattr("src.main.print_hourly_report", fake_print_hourly)

    run()

    assert isinstance(captured["provider"], FakeProvider)
    assert captured["db_path"] == "/tmp/energy.db"
    assert captured["system_id"] == "sys-1"
    assert captured["printed"] == {}


def test_run_hourly_raises_when_system_id_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida erro explícito quando SYSTEM_ID não está configurado."""
    monkeypatch.setenv("HOURLY_START_AT", "2026-04-19 10:00")
    monkeypatch.setenv("HOURLY_END_AT", "2026-04-19 12:00")
    monkeypatch.delenv("SYSTEM_ID", raising=False)

    with pytest.raises(ValueError):
        run_hourly()


def test_run_terminal_dispatches_daily(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida roteamento do subcomando diário."""
    captured: dict[str, object] = {}

    def fake_daily(command_args: object) -> None:
        captured["command_args"] = command_args

    monkeypatch.setattr("src.main.run_daily_command", fake_daily)

    run_terminal(["daily"])

    assert captured["command_args"].command == "daily"


def test_run_terminal_dispatches_monthly(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida roteamento do subcomando mensal."""
    captured: dict[str, object] = {}

    def fake_monthly(command_args: object) -> None:
        captured["command_args"] = command_args

    monkeypatch.setattr("src.main.run_monthly_command", fake_monthly)

    run_terminal(["monthly", "--month", "4", "--year", "2026"])

    assert captured["command_args"].command == "monthly"
    assert captured["command_args"].month == 4
    assert captured["command_args"].year == 2026


def test_run_terminal_dispatches_yearly(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida roteamento do subcomando anual."""
    captured: dict[str, object] = {}

    def fake_yearly(command_args: object) -> None:
        captured["command_args"] = command_args

    monkeypatch.setattr("src.main.run_yearly_command", fake_yearly)

    run_terminal(["yearly", "--year", "2026"])

    assert captured["command_args"].command == "yearly"
    assert captured["command_args"].year == 2026


def test_run_terminal_dispatches_menu(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida roteamento do subcomando de menu interativo."""
    captured = {"called": False}

    def fake_menu() -> None:
        captured["called"] = True

    monkeypatch.setattr("src.main.run_interactive_menu", fake_menu)

    run_terminal(["menu"])

    assert captured["called"] is True


def test_run_hybrid_interface_dispatches_command_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida opção 1 do menu híbrido com comando legado."""
    captured: dict[str, object] = {}
    prompts = iter(["1", "monthly --month 4 --year 2026", "q"])

    def fake_input(prompt: str) -> str:
        captured["prompt"] = prompt
        return next(prompts)

    def fake_run_terminal(argv: list[str]) -> None:
        captured["argv"] = argv

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("src.main.run_terminal", fake_run_terminal)

    run_hybrid_interface()

    assert captured["argv"] == ["monthly", "--month", "4", "--year", "2026"]


def test_run_hybrid_interface_dispatches_interactive_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida opção 2 do menu híbrido."""
    captured = {"called": False}
    prompts = iter(["2", "q"])

    def fake_input(prompt: str) -> str:
        return next(prompts)

    def fake_navigation() -> None:
        captured["called"] = True

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("src.main.run_hierarchical_navigation", fake_navigation)

    run_hybrid_interface()

    assert captured["called"] is True


def test_run_hybrid_interface_handles_interactive_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que erro no modo 2 é tratado sem traceback."""
    captured: dict[str, object] = {"printed": []}
    prompts = iter(["2", "q"])

    def fake_input(prompt: str) -> str:
        return next(prompts)

    def fake_navigation() -> None:
        raise ValueError("Defina SYSTEM_ID para usar o modo interativo hierárquico.")

    def fake_print(*values: object, **kwargs: object) -> None:
        captured["printed"].append(" ".join(str(v) for v in values))

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("src.main.run_hierarchical_navigation", fake_navigation)
    monkeypatch.setattr("builtins.print", fake_print)

    run_hybrid_interface()

    assert any("Erro no modo interativo" in line for line in captured["printed"])


def test_run_hybrid_interface_handles_invalid_option(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que opção inválida não interrompe o fluxo."""
    captured: dict[str, object] = {"printed": []}
    prompts = iter(["9", "q"])

    def fake_input(prompt: str) -> str:
        return next(prompts)

    def fake_print(*values: object, **kwargs: object) -> None:
        captured["printed"].append(" ".join(str(v) for v in values))

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("builtins.print", fake_print)

    run_hybrid_interface()

    assert any("Opcao inválida." in line for line in captured["printed"])


def test_run_hierarchical_navigation_prompts_system_id_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valida prompt de SYSTEM_ID quando variável não está definida."""
    captured: dict[str, object] = {}
    prompts = iter(["sys-from-input", "q"])

    class FakeRepository:
        def __init__(self, db_path: str) -> None:
            captured["db_path"] = db_path

        def list_years(self, system_id: str) -> list[tuple[int, float]]:
            captured["system_id"] = system_id
            return []

    def fake_input(prompt: str) -> str:
        return next(prompts)

    monkeypatch.delenv("SYSTEM_ID", raising=False)
    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("src.main.SQLiteHourlyEnergyRepository", FakeRepository)

    run_hierarchical_navigation()

    assert captured["system_id"] == "sys-from-input"


def test_run_hierarchical_navigation_can_cancel_without_system_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valida cancelamento do modo hierárquico quando SYSTEM_ID não é informado."""
    captured: dict[str, object] = {"printed": []}

    def fake_input(prompt: str) -> str:
        return "q"

    def fake_print(*values: object, **kwargs: object) -> None:
        captured["printed"].append(" ".join(str(v) for v in values))

    monkeypatch.delenv("SYSTEM_ID", raising=False)
    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("builtins.print", fake_print)

    run_hierarchical_navigation()

    assert any("Modo interativo cancelado" in line for line in captured["printed"])


def test_run_hierarchical_navigation_uses_existing_system_id_without_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valida que SYSTEM_ID já definido é usado sem solicitar nova entrada."""
    captured: dict[str, object] = {"prompts": []}

    class FakeRepository:
        def __init__(self, db_path: str) -> None:
            captured["db_path"] = db_path

        def list_years(self, system_id: str) -> list[tuple[int, float]]:
            captured["system_id"] = system_id
            return []

    def fake_input(prompt: str) -> str:
        captured["prompts"].append(prompt)
        return "q"

    monkeypatch.setenv("SYSTEM_ID", "sys-from-env")
    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("src.main.SQLiteHourlyEnergyRepository", FakeRepository)

    run_hierarchical_navigation()

    assert captured["system_id"] == "sys-from-env"
    assert not any("SYSTEM_ID não definido" in prompt for prompt in captured["prompts"])


def test_run_hierarchical_navigation_add_year_then_persist_month_shows_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valida add:AAAA no nível ano e exibição do ano após persistência de mês."""
    captured: dict[str, object] = {"printed": []}
    prompts = iter(["add:2021", "api:5", "0", "q"])

    class FakeProvider:
        def fetch_hourly_generation(self, system_id: str, start_at: object, end_at: object) -> dict[object, float]:
            from datetime import datetime

            return {datetime(2021, 5, 1, 0, 0): 2.5}

    class FakeRepository:
        def __init__(self, db_path: str) -> None:
            self._rows: list[tuple[str, object, float]] = []

        def list_years(self, system_id: str) -> list[tuple[int, float]]:
            grouped: dict[int, float] = {}
            for row_system_id, generation_at, energy in self._rows:
                if row_system_id != system_id:
                    continue
                grouped[generation_at.year] = grouped.get(generation_at.year, 0.0) + energy
            return sorted(grouped.items())

        def list_months(self, system_id: str, year: int) -> list[tuple[int, float]]:
            grouped: dict[int, float] = {}
            for row_system_id, generation_at, energy in self._rows:
                if row_system_id != system_id or generation_at.year != year:
                    continue
                grouped[generation_at.month] = grouped.get(generation_at.month, 0.0) + energy
            return sorted(grouped.items())

        def list_days(self, system_id: str, year: int, month: int) -> list[tuple[int, float]]:
            return []

        def list_hours(self, system_id: str, year: int, month: int, day: int) -> list[tuple[int, float]]:
            return []

        def month_day_bounds(self, year: int, month: int) -> tuple[object, object]:
            from datetime import datetime

            return datetime(year, month, 1, 0, 0), datetime(year, month, 1, 23, 0)

        def upsert_many(self, records: list[object]) -> None:
            for record in records:
                self._rows.append((record.system_id, record.generation_at, record.energy_kwh))

    def fake_input(prompt: str) -> str:
        return next(prompts)

    def fake_print(*values: object, **kwargs: object) -> None:
        captured["printed"].append(" ".join(str(v) for v in values))

    monkeypatch.setenv("SYSTEM_ID", "sys-1")
    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("builtins.print", fake_print)
    monkeypatch.setattr("src.main.APSystemEnergyProvider", FakeProvider)
    monkeypatch.setattr("src.main.SQLiteHourlyEnergyRepository", FakeRepository)

    run_hierarchical_navigation()

    assert any("Nível Mês - Ano 2021" in line for line in captured["printed"])
    assert any("1) 2021 - total:" in line for line in captured["printed"])


def test_run_hierarchical_navigation_prints_progress_for_api_month(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valida feedback interativo ao puxar mês via api:<mes>."""
    captured: dict[str, object] = {"printed": []}
    prompts = iter(["add:2021", "api:5", "q"])

    class FakeProvider:
        def fetch_hourly_generation(self, system_id: str, start_at: object, end_at: object) -> dict[object, float]:
            from datetime import datetime

            return {datetime(2021, 5, 1, 0, 0): 3.7}

    class FakeRepository:
        def __init__(self, db_path: str) -> None:
            self._rows: list[tuple[str, object, float]] = []

        def list_years(self, system_id: str) -> list[tuple[int, float]]:
            grouped: dict[int, float] = {}
            for row_system_id, generation_at, energy in self._rows:
                if row_system_id != system_id:
                    continue
                grouped[generation_at.year] = grouped.get(generation_at.year, 0.0) + energy
            return sorted(grouped.items())

        def list_months(self, system_id: str, year: int) -> list[tuple[int, float]]:
            grouped: dict[int, float] = {}
            for row_system_id, generation_at, energy in self._rows:
                if row_system_id != system_id or generation_at.year != year:
                    continue
                grouped[generation_at.month] = grouped.get(generation_at.month, 0.0) + energy
            return sorted(grouped.items())

        def list_days(self, system_id: str, year: int, month: int) -> list[tuple[int, float]]:
            return []

        def list_hours(self, system_id: str, year: int, month: int, day: int) -> list[tuple[int, float]]:
            return []

        def month_day_bounds(self, year: int, month: int) -> tuple[object, object]:
            from datetime import datetime

            return datetime(year, month, 1, 0, 0), datetime(year, month, 1, 23, 0)

        def upsert_many(self, records: list[object]) -> None:
            for record in records:
                self._rows.append((record.system_id, record.generation_at, record.energy_kwh))

    def fake_input(prompt: str) -> str:
        return next(prompts)

    def fake_print(*values: object, **kwargs: object) -> None:
        captured["printed"].append(" ".join(str(v) for v in values))

    monkeypatch.setenv("SYSTEM_ID", "sys-1")
    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("builtins.print", fake_print)
    monkeypatch.setattr("src.main.APSystemEnergyProvider", FakeProvider)
    monkeypatch.setattr("src.main.SQLiteHourlyEnergyRepository", FakeRepository)

    run_hierarchical_navigation()

    assert any("Puxando mês 05/2021 da API..." in line for line in captured["printed"])
    assert any("Mês 05/2021 concluído." in line for line in captured["printed"])


def test_run_hierarchical_navigation_supports_remove_month_by_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valida comando rm:<indice> no nível mês."""
    captured: dict[str, object] = {"deleted": None}
    prompts = iter(["1", "rm:1", "q"])

    class FakeProvider:
        pass

    class FakeRepository:
        def __init__(self, db_path: str) -> None:
            return

        def list_years(self, system_id: str) -> list[tuple[int, float]]:
            return [(2026, 10.0)]

        def list_months(self, system_id: str, year: int) -> list[tuple[int, float]]:
            return [(4, 10.0)]

        def delete_month(self, system_id: str, year: int, month: int) -> int:
            captured["deleted"] = (system_id, year, month)
            return 2

    def fake_input(prompt: str) -> str:
        return next(prompts)

    monkeypatch.setenv("SYSTEM_ID", "sys-1")
    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("src.main.APSystemEnergyProvider", FakeProvider)
    monkeypatch.setattr("src.main.SQLiteHourlyEnergyRepository", FakeRepository)

    run_hierarchical_navigation()

    assert captured["deleted"] == ("sys-1", 2026, 4)


def test_run_hierarchical_navigation_supports_remove_day_by_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valida comando rm:<indice> no nível dia."""
    captured: dict[str, object] = {"deleted": None}
    prompts = iter(["1", "1", "rm:1", "q"])

    class FakeProvider:
        pass

    class FakeRepository:
        def __init__(self, db_path: str) -> None:
            return

        def list_years(self, system_id: str) -> list[tuple[int, float]]:
            return [(2026, 10.0)]

        def list_months(self, system_id: str, year: int) -> list[tuple[int, float]]:
            return [(4, 10.0)]

        def list_days(self, system_id: str, year: int, month: int) -> list[tuple[int, float]]:
            return [(19, 10.0)]

        def delete_day(self, system_id: str, year: int, month: int, day: int) -> int:
            captured["deleted"] = (system_id, year, month, day)
            return 3

    def fake_input(prompt: str) -> str:
        return next(prompts)

    monkeypatch.setenv("SYSTEM_ID", "sys-1")
    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr("src.main.APSystemEnergyProvider", FakeProvider)
    monkeypatch.setattr("src.main.SQLiteHourlyEnergyRepository", FakeRepository)

    run_hierarchical_navigation()

    assert captured["deleted"] == ("sys-1", 2026, 4, 19)


