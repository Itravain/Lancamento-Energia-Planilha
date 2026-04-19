from src.application.get_current_month_generation import GetCurrentMonthGeneration
from src.infrastructure.apsystem_energy_provider import APSystemEnergyProvider
from src.interfaces.cli import print_monthly_report


def run() -> None:
    """Compõe as dependências e executa o fluxo principal."""
    use_case = GetCurrentMonthGeneration(APSystemEnergyProvider())
    report = use_case.execute()
    print_monthly_report(report)


if __name__ == "__main__":
    run()
