# CNCT Scraper & Engine de Sincronização

## Visão Geral do Sistema

O **CNCT Scraper** é uma solução completa de engenharia de dados, extração REST e sincronização cadastral desenvolvida para extrair, estruturar, higienizar e sincronizar informações sobre cursos técnicos e instituições de ensino ofertantes a partir do Catálogo Nacional de Cursos Técnicos (CNCT) do MEC com o banco de dados MySQL da VPS.

O sistema resolve desafios de alta volumetria e contaminação de dados geográficos por meio de uma arquitetura modular em Python e C:
1. **Pipeline de Raspagem Ultrarrápido**: Cliente HTTP REST nativo desacoplado que consome as APIs públicas do MEC sem dependência de navegadores pesados.
2. **Módulo de Agregação, Sanitização e Diff em POO (`src/c_aggregator/`)**: Engenharia de higienização de endereços, extrator de CEPs, proteção dinâmica de numerais romanos e pareamento determinístico em O(1).
3. **Engine de Migração e Sincronização MySQL**: Sincronização segura via túnel SSH, classificação em 4 categorias de registros e streaming de progresso em tempo real (SSE).
4. **Interface Dual & Console Terminal**: Interface web moderna em CSS puro com Tabulator.js para comparação lado a lado entre o banco MySQL e a raspagem.

---

## Estrutura do Projeto

```text
CNCT_SCRAPER/
├── README.md                           # Especificações completas da arquitetura e execução
├── Dockerfile                          # Build otimizado para deploy automático no Coolify (ARM64 / x86_64)
├── requirements.txt                    # Dependências Python essenciais (FastAPI, uvicorn, PyJWT, etc.)
├── Makefile                            # Automação de compilação dos módulos C nativos
├── .env                                # Variáveis de ambiente (Túnel SSH/MySQL, JWT, CORS)
├── .gitignore                          # Exclusão de arquivos temporários, logs e binários locais
├── DOCS/                               # Documentação e relatórios de auditoria de dados
│   ├── estado_atual_projeto.md         # Estado atual detalhado do projeto
│   └── analises/                       # CSVs e diagnósticos de diff e validação
├── src/
│   ├── main.py                         # Ponto de entrada e testes de execução
│   ├── backend/
│   │   ├── app.py                      # Aplicação FastAPI (JWT, Cookie HttpOnly, iFrame CSP)
│   │   ├── config.py                   # Carregamento de configurações (.env)
│   │   ├── auth.py                     # Autenticação JWT e proteção de rotas
│   │   ├── database.py                 # Conexão MySQL (VPS via SSH) com conn.cursor(dictionary=True)
│   │   ├── websocket_manager.py        # Streaming thread-safe de logs do terminal
│   │   └── routes/
│   │       ├── scraper_routes.py       # Controle de disparo da raspagem
│   │       ├── data_routes.py          # Download e visualização de CSVs
│   │       └── migracao_enderecos.py   # Fluxo de sincronização e gravação SSE no MySQL
│   ├── scraper/
│   │   ├── client.py                   # Cliente HTTP REST para as rotas do MEC
│   │   ├── parser.py                   # Sanitização e extração de JSON/HTML
│   │   └── pipeline.py                 # Orquestrador da raspagem em thread secundária
│   ├── utils/
│   │   └── snowflake.py                # Gerador Snowflake ID de 64-bits thread-safe
│   └── c_aggregator/
│       ├── numerais_romanos.py         # Submódulo POO RomanNumeralProtector (Proteção I-XX)
│       ├── ceps.py                     # Submódulo POO CepExtractor (Extração/Formatação 5-8 dígitos)
│       ├── address_parser.py           # Submódulo POO AddressParser (Parsing e extract_muni_uf_cep)
│       ├── text_normalizer.py          # Submódulo POO TextNormalizer (Normalização e Chaves Naturais)
│       ├── diff_matching.py            # Submódulo POO DiffEngine (Motor de Comparação Determinístico O(1))
│       ├── post_diff_audit.py          # Submódulo POO PostDiffAuditor (Esteira Double Net Audit)
│       ├── csv_exporter.py             # Submódulo POO DiffExporter (Geração dos 4 Relatórios CSV)
│       ├── bridge.py                   # Fachada POO BridgeFacade e delegadores retrocompatíveis
│       ├── aggregator.c                # Agregador de IDs em C (uint64_t)
│       └── address_parser.c            # Parser nativo de endereços em C
├── frontend/
│   ├── index.html                      # Terminal interativo e amostra de dados
│   ├── migracao.html                   # Interface Dual de Sincronização Lado a Lado (Tabulator.js)
│   ├── css/ (styles.css, terminal.css) # Interface Dark/Modern em CSS puro
│   └── js/ (main.js, migracao.js)      # Conexão WebSocket, SSE e manipulação de tabelas
└── tests/                              # Suíte de testes unitários (TDD)
```

---

## Módulos Principais e Arquitetura POO

### 1. Submódulo de Sanitização e Diff (`src/c_aggregator/`)
- **`RomanNumeralProtector`**: Proteção dinâmica contra a truncação indesejada de numerais romanos de `I` a `XX` em nomes de municípios e instituições (ex: `Pedro II`, `Pio IX`).
- **`CepExtractor`**: Identificação e extração de CEPs de 5 a 8 dígitos, higienizando formatos pontuados (ex: `65.72500` ➔ `6572500`) e sufixos residuais.
- **`AddressParser`**: Decomposição estruturada de endereços em `logradouro`, `numero`, `complemento`, `bairro`, `municipio`, `uf` e `cep`. Inclui o extrator `extract_muni_uf_cep` para desinfecção de municípios sujos no MySQL (`'Pinheiro MA - 65200'` ➔ `('Pinheiro', 'MA', '65200')`).
- **`DiffEngine`**: Motor de pareamento determinístico em O(1). Incorpora a trava `and diferencas`, impedindo a inserção de falsas atualizações de CEP/UF em registros idênticos (~16.350 mantidos em `MANTIDOS`).
- **`PostDiffAuditor`**: Esteira de auditoria de dupla camada em 3 passos para reclassificar candidatos a novos antes de permitir a inserção de duplicatas.

### 2. Regras de Sincronização Cadastral
O motor classifica todas as instituições em 4 categorias estritas:
- **NOVOS (INSERT)**: Registros sem correspondente na VPS (recebem novos Snowflake IDs).
- **ALTERADOS / REATIVADOS (UPDATE)**: Registros com alteração de atributos ou reativação de instituições (`ativo = 0` ➔ `ativo = 1`).
- **INATIVADOS (Soft Delete)**: Registros existentes no banco ausentes na raspagem completa (`ativo = 1` ➔ `ativo = 0`). Exclusão física `DELETE` é proibida.
- **MANTIDOS**: Registros idênticos preservados sem alteração.

---

## Requisitos e Instalação Local

### Dependências Básicas

```bash
pip install -r requirements.txt
```

### Compilação do Módulo C (Opcional no ambiente local)

```bash
make build
```

---

## Deploy Automático no Coolify (VPS ARM64)

O projeto está preparado para deploy automático no **Coolify** utilizando o `Dockerfile` otimizado:
- **Arquitetura**: Multi-arch com suporte nativo a `linux/arm64`.
- **Tamanho Otimizado**: Imagem Docker de apenas **~150MB**.
- **Compilação C Automática**: O container compila o agregador nativo em C (`gcc -O3`) durante a etapa de build.
- **Healthcheck Integrado**: Validação de saúde nativa na rota `/api/migracao/status`.

### Execução via Docker Local

```bash
docker build -t cnct-scraper .
docker run -p 8000:8000 cnct-scraper
```

---

## Execução da Aplicação FastAPI

```bash
uvicorn src.backend.app:app --host 0.0.0.0 --port 8000 --reload
```

Acesse o painel web em `http://localhost:8000/`.
