import pytest

from src.main import parse_terminal_args


pytestmark = pytest.mark.unit


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
