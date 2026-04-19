from datetime import datetime

from src.domain.energy_report import MonthlyEnergyReport


def print_monthly_report(report: MonthlyEnergyReport) -> None:
    """Imprime o relatório de geração no console."""
    print(f"Geracao de energia - {report.month:02d}/{report.year}")
    print(f"Total no mes: {report.total_generation:.2f}")
    print("Detalhamento diario:")
    for day, value in report.daily_generation.items():
        print(f"{day}: {value}")


def print_hourly_report(generation: dict[datetime, float]) -> None:
    """Imprime geração horária total e detalhada no console."""
    print("Geracao horaria")
    print(f"Total no periodo: {sum(generation.values()):.2f}")
    print("Detalhamento por hora:")
    for generation_at in sorted(generation.keys()):
        value = generation[generation_at]
        print(f"{generation_at.strftime('%d/%m/%Y %H:%M')}: {value}")
