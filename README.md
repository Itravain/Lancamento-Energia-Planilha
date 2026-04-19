# API de Energia Solar

Este projeto consulta a API da APSystem e retorna a produção diária de energia solar.

## 📋 Descrição

O sistema realiza:
- Autenticação na API da APSystem
- Consulta de geração diária por mês
- Exibição no console da geração diária e total do mês atual

## 🔧 Dependências

As seguintes bibliotecas Python são necessárias:

- `requests` - Requisições HTTP para a API
- `python-dotenv` - Gerenciamento de variáveis de ambiente

## 📦 Instalação

1. Clone o repositório ou baixe os arquivos do projeto

2. Instale as dependências:
```bash
pip install gspread google-auth python-dotenv
```

ou usando um arquivo `requirements.txt`:
```bash
pip install -r requirements.txt
```

## ⚙️ Configuração

1. **Arquivo `.env`:**
   
   Crie um arquivo `.env` na raiz do projeto com:
   ```
   APP_ID=seu_app_id
   APP_SECRET=seu_app_secret
   SYSTEM_ID=seu_system_id
   ```

## 🚀 Como Rodar

Execute o script principal:

```bash
python main.py
```

## 📁 Estrutura de Arquivos

```
Energia/
├── api_energia.py        # Cliente da API APSystem
├── main.py               # Script principal
├── .env                  # Variáveis de ambiente (não versionar)
├── .gitignore            # Arquivos a ignorar no Git
└── README.md             # Este arquivo
```

## 👤 Autor

Ícaro Travain
