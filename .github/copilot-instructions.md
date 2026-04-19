# Instruções do Projeto Energia

## Arquitetura
- Seguir Clean Architecture:
  - domain: regras de negócio e modelos
  - application: casos de uso e portas
  - infrastructure: integração com APSystem
  - interfaces: entrada/saída (CLI)

## Estratégia de Testes (ordem obrigatória)
1. Rodar testes unitários:
   - make test-unit
2. Rodar integração sem API real:
   - make test-integration
3. Rodar integração real somente quando necessário (opt-in):
   - make test-real

## Regras de Execução de Testes
- Não chamar API real em todo commit.
- Testes integration_real só com RUN_APSYSTEM_INTEGRATION=true.
- Antes de merge em develop: unit + integration devem estar verdes.
- Antes de release: considerar rodada de integration_real.

## Convenção de Branches
- main: produção
- develop: integração contínua
- feature/*: desenvolvimento de funcionalidades

## Commits
- Preferir commits atômicos por responsabilidade:
  - refactor
  - test
  - docs
  - chore
