from datetime import date

from api_energia import req_energia


def main() -> None:
    """Consulta a API e imprime a geração diária e total do mês atual."""
    today = date.today()
    month_generation = req_energia(today.month, today.year)
    total_generation = sum(month_generation.values())

    print(f"Geracao de energia - {today.month:02d}/{today.year}")
    print(f"Total no mes: {total_generation:.2f}")
    print("Detalhamento diario:")
    for day, value in month_generation.items():
        print(f"{day}: {value}")


if __name__ == "__main__":
    main()