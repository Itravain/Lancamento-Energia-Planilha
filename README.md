# API de Energia Solar

Projeto estruturado com Clean Architecture e TDD para consultar a API da APSystem
e imprimir no console a geração diária e total do mês atual.

## Estrutura

```
Energia/
├── src/
│   ├── domain/                # Regras e modelos de domínio
│   ├── application/           # Casos de uso e contratos
│   ├── infrastructure/        # Integrações externas (APSystem)
│   ├── interfaces/            # Camada de apresentação (CLI)
│   └── main.py                # Composição da aplicação
├── tests/
│   ├── unit/                  # Testes unitários (TDD)
│   └── integration/           # Testes de integração
├── main.py                    # Launcher da raiz
├── requirements.txt
└── pytest.ini
```

## Dependências

- requests
- python-dotenv
- pytest

## Configuração

Crie o arquivo `.env` na raiz do projeto:

```env
APP_ID=seu_app_id
APP_SECRET=seu_app_secret
SYSTEM_ID=seu_system_id
```

## Execução

```bash
python main.py
```

ou

```bash
python -m src.main
```

## Testes

```bash
pytest
```
