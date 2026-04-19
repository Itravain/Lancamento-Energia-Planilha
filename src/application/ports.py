from typing import Protocol


class EnergyProvider(Protocol):
    """Contrato para provedores de dados de geração de energia."""

    def fetch_month_generation(self, month: int, year: int) -> dict[str, float]:
        """Retorna a geração diária de energia de um mês no formato dd/mm/aaaa."""
        ...
