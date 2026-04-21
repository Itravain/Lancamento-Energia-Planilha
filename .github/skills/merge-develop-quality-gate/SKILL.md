---
name: merge-develop-quality-gate
description: 'Valida e executa merge para develop com gate de qualidade. Use quando for integrar feature branch em develop, garantir commits atomicos (um objetivo por commit), validar testes e checar se o README foi atualizado quando houver mudanca funcional/comportamental.'
argument-hint: 'Branch de origem e resumo das mudancas'
user-invocable: true
disable-model-invocation: false
---

# Merge To Develop Quality Gate

## Quando Usar
- Antes de fazer merge de uma branch de feature para `develop`.
- Quando houver risco de commits misturando responsabilidades.
- Quando for necessario confirmar se o `README.md` acompanha mudancas de uso/comportamento.

## Resultado Esperado
- Branch integrada em `develop` com historico limpo.
- Commits atomicos e com prefixos obrigatorios por responsabilidade (`refactor`, `test`, `docs`, `chore`).
- Testes relevantes verdes.
- `README.md` revisado e atualizado quando aplicavel.

## Procedimento
1. Coletar contexto do merge.
- Identificar branch atual e branch de destino.
- Levantar arquivos alterados e diffs principais.

2. Validar estado antes de commitar.
- Garantir que nao ha conflitos pendentes.
- Separar mudancas por responsabilidade tecnica.

3. Aplicar criterio de commit atomico.
- Cada commit deve ter um unico objetivo verificavel.
- Nao misturar codigo de producao, testes e docs no mesmo commit, exceto quando inseparavel.
- Reagrupar staging por lotes logicos antes de commitar.
- Prefixos de commit sao obrigatorios: `refactor`, `test`, `docs`, `chore`.

4. Checar README com logica de decisao.
- Atualizar `README.md` se houve:
- Novo comando, flag, fluxo interativo ou comportamento visivel para usuario.
- Nova regra de negocio relevante para operacao da CLI.
- Nao atualizar README apenas para refactors internos sem impacto de uso.
- Se nao atualizar, registrar justificativa curta na descricao do merge/PR.

5. Executar verificacoes.
- Rodar no minimo:
- `make test-unit`
- `make test-integration`
- Se solicitado: `make test`

6. Integrar em `develop`.
- Fazer `squash merge` da branch de origem em `develop`.
- Publicar `develop` no remoto.

7. Confirmar saida final.
- Reportar:
- Commits criados (hash + mensagem)
- Resultado de testes
- Status do README (atualizado ou justificativa)
- Hash final do merge em `develop`

## Regras de Decisao
- Se testes falharem: bloquear merge, corrigir e revalidar.
- Se commits nao forem atomicos: reorganizar antes do merge.
- Se houver mudanca de uso e README desatualizado: atualizar README antes do merge.
- Estrategia de integracao padrao: `squash merge`.

## Checklist Rapido
- [ ] Commits atomicos por responsabilidade
- [ ] `make test-unit` verde
- [ ] `make test-integration` verde
- [ ] README revisado (atualizado ou justificativa)
- [ ] Merge em `develop` concluido
- [ ] Push de `develop` realizado
