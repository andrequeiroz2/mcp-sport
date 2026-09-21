# Task 07 — Publicar o servidor no MCP Registry

> **Status:** Em andamento — metadado pronto; falta o publish (PyPI e registry)
> **Criada em:** 2026-09-21
> **Documentos relacionados:** `docs/Technical_Reference.md`,
> `README.md`, `pyproject.toml`
> **Fontes oficiais:**
> [Quickstart](https://modelcontextprotocol.io/registry/quickstart),
> [Package Types (PyPI)](https://modelcontextprotocol.io/registry/package-types),
> [Authentication](https://modelcontextprotocol.io/registry/authentication),
> [Versioning](https://modelcontextprotocol.io/registry/versioning),
> [About](https://modelcontextprotocol.io/registry/about)

## 1. Contexto

O catálogo oficial para a comunidade é o
[MCP Registry](https://registry.modelcontextprotocol.io/). Ele está em
**preview**: a doc avisa que pode haver breaking change ou reset dos dados.

O registry guarda **só metadado** (`server.json`). O artefato fica num
registro público de pacotes. O quickstart mostra o caminho npm/TypeScript;
para pacote que não é npm o fluxo é o mesmo, e a verificação de dono muda
conforme o [guia de package types](https://modelcontextprotocol.io/registry/package-types).

Este projeto é Python. O tipo documentado é **PyPI** (`registryType: "pypi"`),
registro `https://pypi.org` apenas. Transporte de instalação: **stdio**.
Servidor remoto (URL pública) fica fora desta task.

Nome proposto, com autenticação GitHub:

`io.github.andrequeiroz2/mcp-sport`

O prefixo tem de ser o usuário ou a org do GitHub que autenticar. O
repositório já é `github.com/andrequeiroz2/mcp-sport`.

## 2. O que o quickstart pede, adaptado a PyPI

| Passo do quickstart | Neste projeto |
|---|---|
| 1. Marca de dono no pacote | Comentário no README: `<!-- mcp-name: io.github.andrequeiroz2/mcp-sport -->`. O README é o que o PyPI publica (`readme` no `pyproject.toml`). O texto `mcp-name:` tem de ser igual ao `name` do `server.json`. Comentário HTML vale para PyPI. |
| 2. Publicar o artefato | Publicar `mcp-sport` no PyPI **antes** do registry. Conferir se o nome está livre em `https://pypi.org/project/mcp-sport`. |
| 3. Instalar `mcp-publisher` | Binário do [registry](https://github.com/modelcontextprotocol/registry/releases/latest) ou `brew install mcp-publisher`. |
| 4. `server.json` | `mcp-publisher init` e ajustar para o exemplo PyPI da doc: `registryType` `pypi`, `identifier` `mcp-sport`, `transport.type` `stdio`. Sem `environmentVariables`: a OpenF1 histórica não pede chave. `name` igual à marca do README. `version` igual à versão publicada no PyPI. Repositório `https://github.com/andrequeiroz2/mcp-sport`. |
| 5. Login | `mcp-publisher login github` (device code no browser). |
| 6. Publicar | `mcp-publisher validate` e depois `mcp-publisher publish`. Conferir com `curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.andrequeiroz2/mcp-sport"`. |

A versão publicada no registry é **imutável**. Corrigir descrição, entrypoint
e README antes do primeiro `publish`. Uma versão já enviada não se reescreve;
o próximo envio precisa de outra versão (`docs` de
[versioning](https://modelcontextprotocol.io/registry/versioning)).

## 3. Bloqueios no código atual

Nenhum bloqueio de código. O que falta é conta: token do PyPI e
`mcp-publisher login github` (device code no browser). A versão `0.1.0`
ainda não existe no PyPI (`/pypi/mcp-sport/json` retornou 404).

## 4. Fora de escopo

- Hospedar um servidor HTTP público (`remotes` no `server.json`)
- Automatizar o `mcp-publisher` com GitHub Actions (próximo passo do quickstart do registry, não desta task). O upload ao PyPI usa trusted publisher; isso é separado.
- Autenticação por DNS/domínio próprio
- Publicar de novo a pasta `ext-apps` (é o basic-host, não este servidor)

## 5. Critérios de aceite

- [x] `docs/Technical_Reference.md` aponta o MCP Registry, o guia de package
      types e o PyPI
- [x] `description` do `pyproject.toml` descreve o servidor
- [x] O script `mcp-sport` sobe o servidor FastMCP em stdio
- [x] README contém `<!-- mcp-name: io.github.andrequeiroz2/mcp-sport -->`
- [ ] Pacote publicado no PyPI com essa mesma versão
- [x] `server.json` validado (`mcp-publisher validate`) com `registryType`
      `pypi` e transporte `stdio`
- [ ] `mcp-publisher publish` concluído e o nome aparece na API do registry

## 6. Log de execução

### 2026-09-21 — entrypoint e descrição

- `pyproject.toml`: description deixa de ser o placeholder.
- `src/mcp_sport/__init__.py`: `main()` chama `mcp.run()` (stdio), o mesmo
  entrypoint de `server.py`. O import do servidor fica dentro de `main`
  para `import mcp_sport` não registrar as tools à toa.

### 2026-09-21 — metadado do registry

- `docs/Technical_Reference.md`: seção 9 com o MCP Registry e o PyPI.
- README: `<!-- mcp-name: io.github.andrequeiroz2/mcp-sport -->`.
- `server.json` versão `0.1.0`, pacote PyPI, transporte stdio, `runtimeHint`
  `uvx` (o schema lista `uvx` como hint de runtime). `mcp-publisher validate`
  aceitou o arquivo.
- Nome `mcp-sport` livre no PyPI (HTTP 404). Sem token PyPI nem login do
  registry nesta máquina; o publish fica para quem tem a conta.
