from src.domain.energy_report import MonthlyEnergyReport


def print_monthly_report(report: MonthlyEnergyReport) -> None:
    """Imprime o relatório de geração no console."""
    print(f"Geracao de energia - {report.month:02d}/{report.year}")
    print(f"Total no mes: {report.total_generation:.2f}")
    print("Detalhamento diario:")
    for day, value in report.daily_generation.items():
        print(f"{day}: {value}")
