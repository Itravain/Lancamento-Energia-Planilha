# API de Energia Solar

Projeto em Python com Clean Architecture e TDD para consultar geração de energia na APSystem, com cache local em SQLite e interface de terminal (modo comando e modo interativo hierárquico).

## O que o projeto faz

- Consulta geração mensal e anual na API.
- Consulta geração diária e horária com cache-first em SQLite.
- Permite navegação interativa por ano -> mês -> dia -> hora.
- Permite completar períodos sob demanda com comandos contextuais no modo interativo.

## Estrutura do projeto

```text
Energia/
|- src/
|  |- application/
|  |  |- get_current_month_generation.py
|  |  |- get_day_generation.py
|  |  |- get_hourly_energy_range.py
|  |  |- get_month_generation.py
|  |  |- get_year_generation.py
|  |  |- ports.py
|  |- domain/
|  |  |- energy_report.py
|  |- infrastructure/
|  |  |- apsystem_energy_provider.py
|  |  |- sqlite_hourly_energy_repository.py
|  |- interfaces/
|  |  |- cli.py
|  |- main.py
|- tests/
|  |- unit/
|  |- integration/
|- main.py
|- Makefile
|- pytest.ini
|- requirements.txt
|- README.md
```

## Requisitos

- Python 3.13+
- Dependências em [requirements.txt](requirements.txt)

Instalação:

```bash
python -m pip install -r requirements.txt
```

## Configuração (.env)

Crie um arquivo `.env` na raiz:

```env
APP_ID=seu_app_id
APP_SECRET=seu_app_secret
SYSTEM_ID=seu_system_id
ENERGY_DB_PATH=energy.db
```

Notas:

- O projeto carrega `.env` automaticamente no startup.
- Se `SYSTEM_ID` não estiver definido, o modo interativo pede o valor no terminal.

## Como executar

### 1. Entrada principal (recomendado)

```bash
python main.py
```

Sem argumentos, abre o menu híbrido:

- `1`: modo comandos (legado)
- `2`: modo interativo hierárquico
- `q`: sair

### 2. Rodar subcomando diretamente

```bash
python main.py <subcomando> [opcoes]
```

Subcomandos disponíveis:

- `hourly`
- `daily`
- `monthly`
- `yearly`
- `menu`

### 3. Atalho via Makefile

```bash
make run
```

## Uso por subcomando (modo comandos)

### hourly

Busca geração horária em intervalo fechado e usa cache SQLite.

```bash
python main.py hourly \
  --system-id E20D723008093142 \
  --start "2026-04-19 00:00" \
  --end "2026-04-19 23:00" \
  --db-path energy.db
```

### daily

Por padrão usa dia atual e `SYSTEM_ID` do ambiente.

```bash
python main.py daily
python main.py daily --date 2026-04-19
python main.py daily --system-id E20D723008093142 --date 2026-04-19
```

### monthly

```bash
python main.py monthly
python main.py monthly --month 4 --year 2026
```

### yearly

```bash
python main.py yearly
python main.py yearly --year 2026
```

### menu

Menu legado simples para escolher horário/diário/mensal/anual.

```bash
python main.py menu
```

## Modo interativo hierárquico

Fluxo: ano -> mês -> dia -> hora.

Controles globais:

- `0`: voltar um nível
- `q`: sair

Comandos contextuais:

- Nível ano: `add:AAAA`
  - Exemplo: `add:2021`
  - Permite navegar para ano ainda não listado.
- Nível mês: `api:MM`
  - Exemplo: `api:05`
  - Busca o mês na API, persiste no SQLite e atualiza menu.
  - Exibe progresso interativo de início/fim da carga do mês.
- Nível dia: `api:DD`
  - Exemplo: `api:19`
  - Busca o dia na API e persiste no SQLite.
- Nível hora:
  - `api:*` não é permitido.

## Cache SQLite

- Banco padrão: `energy.db`
- Tabela principal: `energy_hourly`
- Chave única: `(system_id, generation_at)`
- Estratégia de escrita: upsert

Isso evita duplicação e permite completar períodos sob demanda pela interface.

## Testes

Comandos no [Makefile](Makefile):

```bash
make test-unit
make test-integration
make test-real
make test
```

Ordem recomendada:

1. `make test-unit`
2. `make test-integration`
3. `make test-real` (somente quando necessário)

Observações:

- O [pytest.ini](pytest.ini) exclui `integration_real` por padrão.
- `make test-real` depende de `RUN_APSYSTEM_INTEGRATION=true`.

## Vistoria atual

Estado validado nesta atualização:

- Unitários: 37 passed
- Integração: 17 passed

## Solução de problemas

### "Defina --system-id ou SYSTEM_ID"

- Defina no `.env` ou passe `--system-id` no comando.

### Não aparece ano/mês no menu interativo

- O menu lista o que já existe no banco local.
- Use `add:AAAA` (nível ano) e `api:MM` (nível mês) para preencher dados.

### Banco diferente do esperado

- Ajuste `ENERGY_DB_PATH` no `.env`.

## Convenção de branches

- `main`: produção
- `develop`: integração contínua
- `feature/*`: novas funcionalidades
