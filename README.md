# API de Energia Solar

Projeto estruturado com Clean Architecture e TDD para consultar a API da APSystem.

O projeto possui dois fluxos principais:
1. Modo mensal: consulta geração diária do mês atual.
2. Modo horário: consulta geração horária por intervalo com estratégia cache-first em SQLite.

## Estrutura do Projeto

Energia/
- src/
  - application/
    - __init__.py
    - get_current_month_generation.py
    - get_hourly_energy_range.py
    - ports.py
  - domain/
    - __init__.py
    - energy_report.py
  - infrastructure/
    - __init__.py
    - apsystem_energy_provider.py
    - sqlite_hourly_energy_repository.py
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
    - test_get_hourly_energy_range.py
    - test_sqlite_hourly_energy_repository.py
  - integration/
    - test_run_wiring.py
    - test_apsystem_real.py
    - test_hourly_cache_flow.py
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

# Opcional para modo horário
ENERGY_MODE=monthly
HOURLY_START_AT=2026-04-19 00:00
HOURLY_END_AT=2026-04-19 23:00
ENERGY_DB_PATH=energy.db

## Execução

Opção 1:
python main.py

Opção 2:
python -m src.main

Opção 3 (atalho):
make run

### Modo mensal (padrão)

```bash
python main.py
```

### Modo horário com cache SQLite

```bash
ENERGY_MODE=hourly \
HOURLY_START_AT="2026-04-19 00:00" \
HOURLY_END_AT="2026-04-19 23:00" \
SYSTEM_ID="seu_system_id" \
ENERGY_DB_PATH="energy.db" \
python main.py
```

No modo horário, o sistema:
1. Busca primeiro no SQLite.
2. Consulta a API apenas para lacunas.
3. Persiste os dados novos.
4. Retorna o consolidado ordenado por hora.

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

### Testes de API real (opt-in)

```bash
RUN_APSYSTEM_INTEGRATION=true make test-real
```

Esse alvo executa os testes marcados como `integration_real`.

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
