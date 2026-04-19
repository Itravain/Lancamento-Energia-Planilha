# API de Energia Solar

Projeto estruturado com Clean Architecture e TDD para consultar a API da APSystem e imprimir no console a geração diária e total do mês atual.

## Estrutura do Projeto

Energia/
- src/
  - application/
    - __init__.py
    - get_current_month_generation.py
    - ports.py
  - domain/
    - __init__.py
    - energy_report.py
  - infrastructure/
    - __init__.py
    - apsystem_energy_provider.py
  - interfaces/
    - __init__.py
    - cli.py
  - __init__.py
  - main.py
- tests/
  - unit/
    - test_apsystem_energy_provider.py
    - test_cli.py
    - test_energy_report.py
    - test_get_current_month_generation.py
  - integration/
    - test_run_wiring.py
    - test_apsystem_real.py
- .github/
  - copilot-instructions.md
- main.py
- Makefile
- requirements.txt
- pytest.ini
- README.md

## Dependências

- requests
- python-dotenv
- pytest

## Configuração

Crie o arquivo .env na raiz do projeto com:

APP_ID=seu_app_id  
APP_SECRET=seu_app_secret  
SYSTEM_ID=seu_system_id

## Execução

Opção 1:
python main.py

Opção 2:
python -m src.main

Opção 3 (atalho):
make run

## Testes

Sequência recomendada:
1. Unitários
make test-unit

2. Integração sem API real
make test-integration

3. Integração real (opt-in)
make test-real

Execução padrão:
make test

Observação:
- O [pytest.ini](pytest.ini) já exclui integration_real por padrão.
- O teste real só deve rodar sob demanda para evitar consumo desnecessário da APSystem.

## Convenção de Branches

- main: produção
- develop: integração
- feature/*: novas funcionalidades

## Fluxo de Qualidade

1. Em feature:
- make test-unit
- make test-integration

2. Antes de merge em develop:
- make test

3. Antes de release (quando necessário):
- make test-real
