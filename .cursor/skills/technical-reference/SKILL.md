---
name: technical-reference
description: Enforces the project's canonical technical documentation (docs/Technical_Reference.md) when implementing, reviewing, or planning MCP server features. Use when writing FastMCP tools, resources, or prompts; consuming the OpenF1 API; defining Pydantic models; choosing libraries or versions; or when the user mentions documentation, stack, technical reference, MCP spec, FastMCP, OpenF1, FastAPI, or Pydantic.
---

# Technical Reference

Garante que todo o código e decisão técnica do projeto siga a documentação
canônica em `docs/Technical_Reference.md`.

## Regra principal

Antes de implementar, revisar ou planejar qualquer feature:

1. **Leia `docs/Technical_Reference.md`** (raiz do projeto) para confirmar a
   stack, versões e links oficiais vigentes.
2. **Consulte a documentação oficial linkada** antes de assumir comportamento
   por memória. Ordem de consulta:
   FastMCP (docs) → MCP Python SDK → Especificação MCP → repositórios GitHub.
3. **Não introduza tecnologias, libs ou padrões fora do documento.** Se algo
   novo for necessário, proponha ao usuário a atualização do
   `docs/Technical_Reference.md` **antes** de implementar.

## Stack vigente (Fase 1)

| Camada | Tecnologia | Uso |
|---|---|---|
| Linguagem | Python 3.13+ | Todo o código |
| Framework MCP | FastMCP >= 4.0.5 | Servidor, tools, CLI |
| SDK base | MCP Python SDK | Apenas via FastMCP; consultar para detalhes de protocolo |
| Dados | OpenF1 API (`https://api.openf1.org/v1`) | Fonte de dados de F1 |
| Validação | Pydantic | Modelos de entrada/saída |
| HTTP próprio | FastAPI | **Reservado para fases futuras — não usar na Fase 1** |
| Deps/projeto | uv + pyproject.toml | Gerenciamento de dependências |

## Checklist de conformidade

Ao escrever ou revisar código, verifique:

- [ ] Tools usam `@mcp.tool()` do FastMCP (não o SDK de baixo nível diretamente)
- [ ] Versões respeitam os pins do `docs/Technical_Reference.md` e do `pyproject.toml`
- [ ] Chamadas à OpenF1 usam a base URL documentada
- [ ] Schemas de entrada/saída usam Pydantic quando houver estrutura de dados
- [ ] Nenhuma dependência nova foi adicionada sem atualizar o documento canônico
- [ ] Spec MCP de referência: `2026-07-28`

## Manutenção do documento canônico

- Mudança de versão (FastMCP, SDK, spec MCP) → registrar no
  `docs/Technical_Reference.md` junto com o changelog oficial correspondente.
- Nova tecnologia → só entra no projeto após ser adicionada ao documento com
  suas referências oficiais.
- Conflito entre memória/comportamento observado e a doc oficial → a doc
  oficial vence; sinalizar a divergência ao usuário.
