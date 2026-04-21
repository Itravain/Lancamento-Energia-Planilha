import csv
from datetime import date, datetime

import pytest

from src.application.export_csv_report import ExportCsvReport


pytestmark = pytest.mark.unit


class FakeRepository:
    def __init__(self, payload: dict[datetime, float]) -> None:
        self.payload = payload
        self.calls: list[tuple[str, datetime, datetime]] = []

    def get_range(self, system_id: str, start_at: datetime, end_at: datetime) -> dict[datetime, float]:
        self.calls.append((system_id, start_at, end_at))
        return self.payload


@pytest.mark.parametrize(
    ("granularity", "expected_rows", "expected_filename"),
    [
        (
            "hour",
            [
                ["period", "energy_kwh"],
                ["2026-02-05 10:00", "1.0"],
                ["2026-02-05 11:00", "2.0"],
                ["2026-03-05 10:00", "3.0"],
            ],
            "relat_05-02-2026_05-03-2026_hour.csv",
        ),
        (
            "day",
            [
                ["period", "energy_kwh"],
                ["2026-02-05", "3.0"],
                ["2026-03-05", "3.0"],
            ],
            "relat_05-02-2026_05-03-2026_day.csv",
        ),
        (
            "month",
            [
                ["period", "energy_kwh"],
                ["2026-02", "3.0"],
                ["2026-03", "3.0"],
            ],
            "relat_05-02-2026_05-03-2026_month.csv",
        ),
        (
            "year",
            [
                ["period", "energy_kwh"],
                ["2026", "6.0"],
            ],
            "relat_05-02-2026_05-03-2026_year.csv",
        ),
    ],
)
def test_execute_exports_csv_for_each_granularity(
    tmp_path: pytest.TempPathFactory,
    granularity: str,
    expected_rows: list[list[str]],
    expected_filename: str,
) -> None:
    repository = FakeRepository(
        {
            datetime(2026, 2, 5, 10): 1.0,
            datetime(2026, 2, 5, 11): 2.0,
            datetime(2026, 3, 5, 10): 3.0,
        }
    )
    output_dir = tmp_path / "relatorios"
    use_case = ExportCsvReport(repository, output_dir=output_dir)

    output_path = use_case.execute(
        "sys-1",
        date(2026, 2, 5),
        date(2026, 3, 5),
        granularity,
    )

    assert output_path.name == expected_filename
    assert repository.calls == [
        (
            "sys-1",
            datetime(2026, 2, 5, 0, 0),
            datetime(2026, 3, 5, 23, 0),
        )
    ]

    with output_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.reader(file))

    assert rows == expected_rows


def test_execute_raises_for_invalid_date_range(tmp_path: pytest.TempPathFactory) -> None:
    repository = FakeRepository({})
    use_case = ExportCsvReport(repository, output_dir=tmp_path / "relatorios")

    with pytest.raises(ValueError, match=r"start_date=.*start_date <= end_date"):
        use_case.execute("sys-1", date(2026, 3, 5), date(2026, 2, 5), "month")