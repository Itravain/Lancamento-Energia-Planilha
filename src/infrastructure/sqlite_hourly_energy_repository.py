import sqlite3
from calendar import monthrange
from datetime import datetime

from src.domain.energy_report import HourlyEnergyRecord


class SQLiteHourlyEnergyRepository:
    """Repositório SQLite para persistir geração por hora."""

    def __init__(self, db_path: str) -> None:
        """Inicializa conexão e garante criação do schema mínimo."""
        self.db_path = db_path
        self._initialize_schema()

    def get_range(
        self,
        system_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[datetime, float]:
        """Retorna geração por hora no intervalo fechado e ordenado."""
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT generation_at, energy_kwh
                FROM energy_hourly
                WHERE system_id = ?
                  AND generation_at >= ?
                  AND generation_at <= ?
                ORDER BY generation_at ASC
                """,
                (system_id, self._serialize_dt(start_at), self._serialize_dt(end_at)),
            )
            rows = cursor.fetchall()

        return {
            datetime.fromisoformat(generation_at): float(energy_kwh)
            for generation_at, energy_kwh in rows
        }

    def upsert_many(self, records: list[HourlyEnergyRecord]) -> None:
        """Insere ou atualiza registros por chave única de sistema e hora."""
        if not records:
            return

        payload = [
            (record.system_id, self._serialize_dt(record.generation_at), record.energy_kwh)
            for record in records
        ]

        with sqlite3.connect(self.db_path) as connection:
            connection.executemany(
                """
                INSERT INTO energy_hourly (system_id, generation_at, energy_kwh)
                VALUES (?, ?, ?)
                ON CONFLICT(system_id, generation_at)
                DO UPDATE SET energy_kwh = excluded.energy_kwh
                """,
                payload,
            )
            connection.commit()

    def list_years(self, system_id: str) -> list[tuple[int, float]]:
        """Lista anos disponíveis com total de geração por ano."""
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT strftime('%Y', generation_at) AS year_key,
                       SUM(energy_kwh) AS total_kwh
                FROM energy_hourly
                WHERE system_id = ?
                GROUP BY year_key
                ORDER BY year_key ASC
                """,
                (system_id,),
            )
            rows = cursor.fetchall()

        return [(int(year_key), float(total_kwh)) for year_key, total_kwh in rows if year_key]

    def list_months(self, system_id: str, year: int) -> list[tuple[int, float]]:
        """Lista meses do ano com dados e total de geração por mês."""
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT strftime('%m', generation_at) AS month_key,
                       SUM(energy_kwh) AS total_kwh
                FROM energy_hourly
                WHERE system_id = ?
                  AND strftime('%Y', generation_at) = ?
                GROUP BY month_key
                ORDER BY month_key ASC
                """,
                (system_id, f"{year:04d}"),
            )
            rows = cursor.fetchall()

        return [(int(month_key), float(total_kwh)) for month_key, total_kwh in rows if month_key]

    def list_days(self, system_id: str, year: int, month: int) -> list[tuple[int, float]]:
        """Lista dias do mês com dados e total de geração por dia."""
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT strftime('%d', generation_at) AS day_key,
                       SUM(energy_kwh) AS total_kwh
                FROM energy_hourly
                WHERE system_id = ?
                  AND strftime('%Y-%m', generation_at) = ?
                GROUP BY day_key
                ORDER BY day_key ASC
                """,
                (system_id, f"{year:04d}-{month:02d}"),
            )
            rows = cursor.fetchall()

        return [(int(day_key), float(total_kwh)) for day_key, total_kwh in rows if day_key]

    def list_hours(self, system_id: str, year: int, month: int, day: int) -> list[tuple[int, float]]:
        """Lista detalhamento horário de um dia específico."""
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                SELECT strftime('%H', generation_at) AS hour_key,
                       energy_kwh
                FROM energy_hourly
                WHERE system_id = ?
                  AND strftime('%Y-%m-%d', generation_at) = ?
                ORDER BY hour_key ASC
                """,
                (system_id, f"{year:04d}-{month:02d}-{day:02d}"),
            )
            rows = cursor.fetchall()

        return [(int(hour_key), float(energy_kwh)) for hour_key, energy_kwh in rows if hour_key]

    def delete_month(self, system_id: str, year: int, month: int) -> int:
        """Apaga todos os registros de um mês específico e retorna quantidade removida."""
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                DELETE FROM energy_hourly
                WHERE system_id = ?
                  AND strftime('%Y-%m', generation_at) = ?
                """,
                (system_id, f"{year:04d}-{month:02d}"),
            )
            deleted_rows = cursor.rowcount
            connection.commit()
        return deleted_rows

    def delete_day(self, system_id: str, year: int, month: int, day: int) -> int:
        """Apaga todos os registros de um dia específico e retorna quantidade removida."""
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                """
                DELETE FROM energy_hourly
                WHERE system_id = ?
                  AND strftime('%Y-%m-%d', generation_at) = ?
                """,
                (system_id, f"{year:04d}-{month:02d}-{day:02d}"),
            )
            deleted_rows = cursor.rowcount
            connection.commit()
        return deleted_rows

    def month_day_bounds(self, year: int, month: int) -> tuple[datetime, datetime]:
        """Retorna limites de datetime para um mês completo."""
        last_day = monthrange(year, month)[1]
        start_at = datetime(year, month, 1, 0, 0)
        end_at = datetime(year, month, last_day, 23, 0)
        return start_at, end_at

    def _initialize_schema(self) -> None:
        """Cria tabela e índices mínimos para leitura/escrita horária."""
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS energy_hourly (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_id TEXT NOT NULL,
                    generation_at TEXT NOT NULL,
                    energy_kwh REAL NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(system_id, generation_at)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_energy_hourly_system_generation_at
                ON energy_hourly (system_id, generation_at)
                """
            )
            connection.commit()

    def _serialize_dt(self, value: datetime) -> str:
        """Serializa datetime para formato ISO estável em SQLite."""
        return value.isoformat(timespec="seconds")
