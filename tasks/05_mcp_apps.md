# Task 05 — MCP Apps: componentes visuais como resultado de tools

> **Status:** Em andamento — spike de validação
> **Criada em:** 2026-09-21
> **Documentos relacionados:** `docs/Technical_Reference.md` (fontes oficiais),
> `docs/Architectural_Design.md`, `tasks/04_cache.md`

## 1. Objetivo

Permitir que tools do mcp-sport retornem **UIs interativas renderizadas na
conversa** (não apenas JSON/texto), usando a extensão **MCP Apps** do
protocolo, implementada pelo FastMCP.

Caso de uso alvo (visão de produto): dashboard de telemetria de uma volta
(velocidade, RPM, marcha, DRS ao longo da pista) — mas antes, validar a
viabilidade técnica com um app simples.

## 2. Pesquisa — os 4 padrões oficiais (FastMCP Apps)

Fonte: <https://gofastmcp.com/apps/overview> (link canônico, seção FastMCP do
`Technical_Reference.md`).

| Padrão | Como funciona | Quando usar |
|---|---|---|
| **Interactive Tools** | `@mcp.tool(app=True)` retornando componente Prefab (`DataTable`, charts...) | Ponto de partida. Interatividade client-side (sort, search, tabs, tooltips) sem round-trips |
| **FastMCPApp** | UI chama de volta o servidor (forms, botões com ação backend) | UI com ações server-side |
| **Generative UI** | LLM escreve código Prefab sob demanda (`mcp.add_provider(GenerativeUI())`) | UI customizada por request |
| **Custom HTML** | HTML/CSS/JS próprios, falando direto com o protocolo MCP Apps | Controle total (imagens externas, mapas, frameworks) |

### Ressalvas oficiais

- Requer extra: `pip install "fastmcp[apps]"` (traz `prefab-ui`)
- **Prefab está em desenvolvimento ativo com breaking changes frequentes** —
  a doc manda pinnar a versão exata no `pyproject.toml`
- A renderização depende de **suporte do host** (Cursor, Claude, Inspector) —
  não basta o servidor emitir a UI

## 3. Decisão de arquitetura (preliminar)

Para o spike: **Custom HTML** — o caso pede fotos externas dos pilotos
(`headshot_url` da OpenF1) e layout livre, e o padrão não adiciona a
dependência `prefab-ui` ao caminho crítico.

Para o dashboard de telemetria (fase seguinte): avaliar **Interactive Tools
(Prefab)** se os componentes de chart cobrirem o caso; senão, Custom HTML com
uma lib de chart (ex.: Chart.js via CDN).

## 4. Spike — app de classificação do campeonato

**Escopo:** ao consultar a classificação do campeonato de pilotos, renderizar
HTML com **foto do piloto** (`headshot_url` da OpenF1 via `get_drivers`) e
**pontos** (`get_drivers_championship`).

### Critérios de aceite do spike

- [ ] `fastmcp[apps]` instalado e versão do `prefab-ui` (se usada) pinada
- [ ] Tool retorna resource HTML válido segundo o protocolo MCP Apps
- [ ] Cursor **renderiza** o HTML na conversa (fator limitante = suporte do host)
- [ ] Fallback: se o host não renderiza, a tool ainda retorna texto/JSON útil
- [ ] Fotos carregam (URLs externas da mídia F1)

### Riscos / perguntas que o spike responde

1. O Cursor (nosso host, transporte stdio) renderiza MCP Apps?
2. Imagens externas (CDN da F1) carregam dentro do sandbox da UI?
3. Qual o formato exato do retorno (mimeType, meta fields) que o FastMCP 4.0.5
   espera para Custom HTML?

## 5. Fases seguintes (após spike aprovado)

- [ ] Task 05b: dashboard de telemetria de volta (car_data + location)
- [ ] Decisão Prefab vs Custom HTML para o dashboard
- [ ] Documentar padrão escolhido no `Architectural_Design.md`
- [ ] Atualizar `Technical_Reference.md` com as libs de UI adotadas

## 6. Log de execução

### 2026-09-21 — Spike implementado

**Decisões:**

- Padrão **Custom HTML** (sem dependência `prefab-ui` — nada a instalar;
  FastMCP 4.0.5 já inclui `fastmcp.apps` com `AppConfig`/`ResourceCSP`)
- SDK JS oficial carregado de CDN no iframe:
  `https://unpkg.com/@modelcontextprotocol/ext-apps@0.4.0/app-with-deps`
  (mesma versão do exemplo oficial `qr-server`; wire protocol compatível
  com hosts 1.x e 2.x — avaliar upgrade para v2 na fase seguinte)

**Descobertas no código-fonte (FastMCP 4.0.5):**

- `@mcp.tool(app=AppConfig(resource_uri=..., csp=...))` carimba
  `meta.ui.resourceUri` + `meta.ui.csp` na tool
- Resource `ui://...` recebe automaticamente o mime
  `text/html;profile=mcp-app` (`fastmcp.utilities.mime`)
- CSP é **obrigatório** para origens externas: sem declarar
  `resourceDomains`, o iframe sandbox bloqueia o SDK JS e as fotos
  (exemplo oficial qr-server deixa isso explícito)

**Implementação:**

- `src/mcp_sport/tools/championship_view.py` — resource
  `ui://mcp-sport/standings.html` + tool `get_drivers_championship_view`
  que faz merge de `/championship_drivers` (pontos/posição) com
  `/drivers` (foto, nome, equipe, cor) e retorna JSON (fallback textual
  para hosts sem suporte a MCP Apps)
- Registrada em `server.py`

**Validações concluídas:**

- [x] Tool registrada com `meta.ui.resourceUri` e CSP corretos
- [x] Resource servindo com mime `text/html;profile=mcp-app`
- [x] Execução real (session 11307, Barcelona 2026): 22 pilotos, merge
      correto, headshots `media.formula1.com` presentes
- [x] Wire protocol validado via stdio puro: `_meta.ui.resourceUri` na
      tool, resource listado com CSP, 19 tools no handshake
- [x] **Cursor renderiza o HTML?** — **NÃO** (testado 2026-09-21):
      o Cursor consome o resultado como JSON texto e ignora o
      `_meta.ui`. O fallback textual funcionou como projetado — nada quebra.
- [x] **Host de referência renderiza?** — **SIM** ✅ (2026-09-21):
      validado no `basic-host` oficial do repo `modelcontextprotocol/ext-apps`
      (double-iframe sandbox + AppBridge). Board renderizado com fotos
      (`media.formula1.com`), cores de equipe e pontos. **Servidor provado
      100% spec-compliant end-to-end.**
- [x] Fotos externas carregam dentro do iframe sandbox? — **SIM**,
      via CSP `resourceDomains` declarado no resource

### Achados do spike

1. **Cursor (versão atual) não suporta MCP Apps.** VS Code anunciou
   suporte em 2026-01-26; Cursor (fork) ainda não herdou. O padrão
   Custom HTML está correto no servidor — a limitação é do host.
2. **Bug de merge:** standings do campeonato são acumulados da temporada,
   mas `/drivers` foi consultado só na sessão resolvida — pilotos que
   saíram no meio do ano (ex.: #6, P8 com 71 pts) ficam sem nome/foto.
   Correção candidata: buscar `/drivers` sem filtro de sessão.
3. **Cache de tools do chat:** o catálogo de tools do Cursor é congelado
   no início da sessão de chat — tools novas exigem novo chat/reload
   (observado neste spike).
4. **Fallback funciona:** host sem suporte recebe JSON útil — a tool é
   segura para manter registrada mesmo sem renderização.

### Próximos passos possíveis (decisão pendente)

- A. ~~Validar a renderização num host compatível~~ — **FEITO** ✅
- B. Manter a tool como está (fallback JSON) e aguardar suporte do Cursor
- C. Remover o spike e arquivar a task como "adiada até suporte do host"

### Notas da validação em host compatível (2026-09-21)

Ambiente usado (reproduzível):

1. Servidor em modo HTTP com CORS — **dois detalhes obrigatórios**:
   - `CORSMiddleware` com `allow_origins/allow_methods/allow_headers=["*"]`
   - **`expose_headers=["mcp-session-id", "mcp-protocol-version"]`** — sem
     isso o browser não lê o session-id do `initialize` e o handshake
     Streamable HTTP falha (POSTs seguintes retornam 400)
   - Comando: `mcp.http_app(middleware=[Middleware(CORSMiddleware, ...)])`
     + `uvicorn` na porta 8765
2. basic-host: `git clone` do ext-apps → `examples/basic-host` →
   `npm install` → `npm run build` → `SERVERS='["http://127.0.0.1:8765/mcp"]'
   npx tsx serve.ts` (o script `npm start` exige `bun`; `tsx` funciona)
3. Host em `http://localhost:8080`, sandbox em `:8081`

Observação: o mcp-use Inspector v12.0.6 (listado como compatível no README
do ext-apps) **não renderizou** a view — tratou como texto. O basic-host
(implementação de referência da spec) renderizou corretamente.

