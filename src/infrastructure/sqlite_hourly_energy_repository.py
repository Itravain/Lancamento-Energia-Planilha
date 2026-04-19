import sqlite3
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
