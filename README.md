# API de Planilhas - Produção de Energia Solar

Este projeto é responsável por gerenciar e atualizar dados de produção de energia solar diária em planilhas do Google Sheets.

## 📋 Descrição

O sistema realiza:
- Conexão com Google Sheets via API
- Leitura de dados de produção de energia solar
- Verificação do último lançamento realizado
- Listagem de meses para processamento
- Adição de novos dados à planilha automaticamente

## 🔧 Dependências

As seguintes bibliotecas Python são necessárias:

- `gspread` - Interação com Google Sheets
- `google-auth` - Autenticação Google OAuth2
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

1. **Credenciais Google Cloud:**
   - Crie um projeto no [Google Cloud Console](https://console.cloud.google.com/)
   - Ative a API do Google Sheets
   - Crie uma conta de serviço e baixe o arquivo de credenciais JSON
   - Renomeie o arquivo para `credentials.json` e coloque na raiz do projeto

2. **Arquivo `.env`:**
   
   Crie um arquivo `.env` na raiz do projeto com:
   ```
   SHEET_ID=seu_id_da_planilha_aqui
   ```
   
   O `SHEET_ID` pode ser obtido da URL da planilha:
   ```
   https://docs.google.com/spreadsheets/d/SHEET_ID/edit
   ```

3. **Permissões da Planilha:**
   - Compartilhe a planilha do Google Sheets com o email da conta de serviço
   - Dê permissão de Editor

## 🚀 Como Rodar

Execute o script principal:

```bash
python main.py
```

## 📁 Estrutura de Arquivos

```
Energia/
├── api_planilhas.py      # Script principal
├── credentials.json      # Credenciais Google (não versionar!)
├── .env                  # Variáveis de ambiente (não versionar!)
├── .gitignore           # Arquivos a ignorar no Git
└── README.md            # Este arquivo
```

## 👤 Autor

Ícaro Travain
