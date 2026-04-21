# Instruções do Projeto Energia

## Stack e Convenções Gerais
- Linguagem principal: Python 3.13+.
- Saída para usuário: texto simples e legível.
- Logs técnicos: JSON estruturado.
- Sempre preferir soluções simples, explícitas e testáveis.

## Arquitetura
- Seguir Clean Architecture:
  - domain: regras de negócio e modelos puros
  - application: casos de uso e portas
  - infrastructure: integrações externas
  - interfaces: entrada/saída da CLI
- Dependências devem apontar para dentro.
- Wrappers de bibliotecas de terceiros devem ficar em infrastructure.

## Code Style
- Funções: entre 4 e 20 linhas quando possível.
- Arquivos: abaixo de 500 linhas.
- Uma responsabilidade por função e por módulo.
- Nomes específicos e únicos.
- Tipagem explícita em funções públicas e privadas.
- Evitar Any e coleções sem parametrização.
- Preferir early return.
- Evitar ifs aninhados desnecessários.
- Mensagens de erro devem incluir o valor recebido e o esperado.
- Evitar duplicação; extrair helpers quando fizer sentido.

## Comments
- Preservar comentários existentes quando eles carregarem intenção ou contexto.
- Comentários devem explicar por que algo existe, não o que o código faz.
- Docstrings em funções públicas devem incluir intenção e exemplo curto.
- Referencie issue ou commit quando a linha existir por uma restrição específica.

## Tests
- Comando padrão rápido: make test.
- Ordem obrigatória:
  1. make test-unit
  2. make test-integration
  3. make test-real
- Nunca chamar API real por padrão.
- integration_real somente com RUN_APSYSTEM_INTEGRATION=true.
- Toda função nova relevante deve ter teste.
- Toda correção de bug deve ter teste de regressão.
- Use fakes nomeados para I/O externo.
- Testes devem ser F.I.R.S.T.

## Dependencies
- Injetar dependências por construtor ou parâmetro.
- Evitar dependências globais de infraestrutura.
- Portas ficam em application; implementações ficam em infrastructure.

## Structure
- Respeitar a estrutura atual:
  - src/domain
  - src/application
  - src/infrastructure
  - src/interfaces
- Preferir módulos pequenos e focados.
- Evitar arquivos gigantes ou concentradores de lógica.

## Formatting
- Usar o formatador padrão da linguagem.
- Não discutir estilo além das regras automatizáveis.

## Logging
- Structured JSON when logging for debugging / observability.
- Plain text only for user-facing CLI output.

## Regras de Entrega
- Antes de merge em develop:
  - make test-unit verde
  - make test-integration verde
- Antes de release:
  - considerar make test-real com credenciais válidas
- Commits atômicos por responsabilidade:
  - refactor
  - test
  - docs
  - chore

## Branches
- main: produção
- develop: integração contínua
- feature/*: desenvolvimento de funcionalidades