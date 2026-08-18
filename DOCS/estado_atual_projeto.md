# Estado Atual do Projeto CNCT Scraper

## 1. Visão Geral da Arquitetura

O **CNCT Scraper** é uma solução de engenharia de dados desacoplada e robusta projetada para extrair, normalizar, agregar, higienizar e sincronizar informações sobre cursos técnicos e instituições de ensino ofertantes a partir do Catálogo Nacional de Cursos Técnicos (CNCT) do MEC com o banco de dados MySQL da VPS.

### Estrutura do Diretório do Projeto

```text
CNCT_SCRAPER/
├── README.md                           # Documentação e especificações de arquitetura
├── requirements.txt                    # Dependências Python (FastAPI, PyJWT, mysql-connector-python, etc.)
├── Makefile                            # Automação de compilação dos módulos C nativos
├── .env                                # Configurações de ambiente (Túnel SSH/MySQL, JWT, CORS)
├── DOCS/                               # Relatórios de auditoria, schema MySQL e diagnósticos
│   ├── estado_atual_projeto.md         # Estado atual e documentação da arquitetura do sistema
│   └── analises/                       # CSVs e relatórios de auditoria e validações de diff
├── contexto_agent/                     # Especificações de microsserviço, iFrame e chave natural
├── src/
│   ├── main.py                         # Ponto de entrada e teste de execução
│   ├── backend/
│   │   ├── app.py                      # Aplicação principal FastAPI (JWT, Cookie HttpOnly, iFrame CSP)
│   │   ├── config.py                   # Carregamento de variáveis de ambiente (.env)
│   │   ├── auth.py                     # Autenticação JWT, validação de sessão e proteção de rotas
│   │   ├── database.py                 # Conexão MySQL (VPS via túnel SSH) e tabela de auditoria
│   │   ├── websocket_manager.py        # Transmissão thread-safe de logs do terminal em tempo real
│   │   └── routes/
│   │       ├── scraper_routes.py       # Rotas de controle do pipeline de raspagem
│   │       ├── data_routes.py          # Rotas de download e amostragem dos arquivos CSV
│   │       └── migracao_enderecos.py   # Fluxo de sincronização, diff de tabelas e SSE de gravação
│   ├── scraper/
│   │   ├── client.py                   # Cliente HTTP (urllib/httpx) para a API REST interna do MEC
│   │   ├── parser.py                   # Parsing e sanitização de atributos HTML/JSON
│   │   └── pipeline.py                 # Orquestrador da raspagem e exportação temporária
│   ├── utils/
│   │   └── snowflake.py                # Gerador Snowflake ID de 64-bits thread-safe (threading.Lock)
│   └── c_aggregator/
│       ├── numerais_romanos.py         # Submódulo POO RomanNumeralProtector (Proteção I-XX)
│       ├── ceps.py                     # Submódulo POO CepExtractor (Extração/Formatação 5-8 dígitos)
│       ├── address_parser.py           # Submódulo POO AddressParser (Parsing e extract_muni_uf_cep)
│       ├── text_normalizer.py          # Submódulo POO TextNormalizer (Normalização e Chaves Naturais)
│       ├── diff_matching.py            # Submódulo POO DiffEngine (Motor de Comparação Determinístico O(1))
│       ├── post_diff_audit.py          # Submódulo POO PostDiffAuditor (Esteira Double Net Audit em 3 passos)
│       ├── csv_exporter.py             # Submódulo POO DiffExporter (Geração dos 4 Relatórios CSV)
│       ├── bridge.py                   # Fachada POO BridgeFacade e delegadores retrocompatíveis
│       ├── aggregator.c                # Agregador de IDs em C (uint64_t)
│       └── address_parser.c            # Parser nativo de endereços em C
├── frontend/
│   ├── index.html                      # Interface principal do Console Terminal do Scraper
│   ├── migracao.html                   # Interface Dual de Sincronização, Busca e Tabulator.js
│   ├── css/ (styles.css, terminal.css) # Estilização Dark/Modern em CSS puro
│   └── js/ (main.js, migracao.js, terminal.js) # Conexão WebSocket, SSE e manipulação de tabelas
└── tests/                              # Suíte de testes unitários (TDD) e scripts de verificação
```

---

## 2. Componentes e Módulos do Sistema

### A. Pipeline de Raspagem (`src/scraper/`)
- **CNCTApiClient (`src/scraper/client.py`)**: Cliente HTTP nativo com retentativas e tratamento de resiliência, consultando as rotas públicas da API REST do MEC (`/cnct-api/home/`, `/cnct-api/cursos/{id}`, `/cnct-api/instituicao/buscaPorNomeCurso`).
- **ScraperPipeline (`src/scraper/pipeline.py`)**: Executa a raspagem em uma thread secundária desacoplada para evitar bloqueios no event loop principal do FastAPI. Atribui Snowflake IDs de 64-bits aos cursos e instituições.

### B. Módulo de Agregação, Sanitização e Diff POO (`src/c_aggregator/`)
O módulo foi inteiramente refatorado em arquitetura Orientada a Objetos (POO), desacoplando responsabilidades em arquivos físicos especializados:

1. **`RomanNumeralProtector` (`numerais_romanos.py`)**:
   - Classe dedicada exclusivamente para a detecção, validação e preservação imune de numerais romanos de `I` a `XX` em nomes de instituições e municípios (ex: `Pedro II`, `Pio IX`, `Jardim de Piranhas`).
   - Algoritmo 100% dinâmico baseado em conjunto sintático e regras de contorno de palavra.

2. **`CepExtractor` (`ceps.py`)**:
   - Classe especializada na identificação, validação e formatação de CEPs brasileiros de 5 a 8 dígitos.
   - Suporta CEPs com pontuação interna (ex: `65.72500` ➔ `6572500`), sufixos com traço (ex: `78005-` ➔ `78005`) e remoção limpa do corpo do texto.

3. **`AddressParser` (`address_parser.py`)**:
   - Decomposição estruturada do texto de endereço em `logradouro`, `numero`, `complemento`, `bairro`, `municipio`, `uf` e `cep`.
   - Método `extract_muni_uf_cep`: Purificação tríplice de strings contaminadas do banco de dados (ex: `'Pinheiro MA - 65200'` ➔ `('Pinheiro', 'MA', '65200')`).

4. **`TextNormalizer` (`text_normalizer.py`)**:
   - Higienização de acentuação, expansão de abreviações institucionais, cálculo de score de riqueza de nomes e geração de chaves naturais indexadas.

5. **`DiffEngine` (`diff_matching.py`)**:
   - Motor de comparação determinístico em O(1) com pareamento multi-nível.
   - Incorpora a trava de segurança `elif not db_uf_actual and diferencas:` e `elif not cep_db_raw and diferencas:`, garantindo que registros idênticos não sofram falsas atualizações de CEP/UF, mantendo ~16.350 registros em `MANTIDOS` e higienizando completamente os registros contaminados na Seção 2 (**ALTERAÇÕES CADASTRAIS**).

6. **`PostDiffAuditor` (`post_diff_audit.py`)**:
   - Esteira de auditoria de dupla camada (Double Net Audit em 3 passos: CEP+Número, Logradouro+Número+Município e Tokens Distintos de Nome) para evitar a criação de novos registros duplicados.

7. **`DiffExporter` (`csv_exporter.py`)**:
   - Exportação dos 4 relatórios individuais em formato CSV (delimitados por `;`) com preenchimento garantido de colunas de município, UF e CEP.

8. **`BridgeFacade` (`bridge.py`)**:
   - Fachada POO de integração que expõe delegadores de nível de módulo para manutenção de 100% da retrocompatibilidade com o backend FastAPI.

### C. Backend FastAPI (`src/backend/`)
- **Segurança e iFrame**: Injeção do cabeçalho `Content-Security-Policy: frame-ancestors` e remoção de `X-Frame-Options` para execução transparente dentro do iFrame do portal Esteio Conecta.
- **Autenticação e Sessão**: Validação de JWT via query string, cabeçalho `Authorization: Bearer` ou cookie HttpOnly (`scraper_session`).
- **Padrão Estrito de Cursors MySQL**: 100% dos cursores MySQL no backend utilizam obrigatoriamente `conn.cursor(dictionary=True)`.
- **Comunicação em Tempo Real**:
  - WebSocket `/ws/terminal`: Streaming dos logs de execução do terminal.
  - Endpoint `/api/migracao/executar`: Streaming SSE de progresso incremental durante a gravação no MySQL.

### D. Frontend Dual (`frontend/`)
- **`index.html`**: Interface do terminal interativo e visualização de amostras.
- **`migracao.html`**: Painel dual de sincronização lado a lado (MySQL vs Scraper), com filtro simultâneo unificado, renderização performática em Tabulator.js, relatórios de diff e modal de auditoria com IP e timestamp.

---

## 3. Regras de Negócio e Gestão de Estados

1. **Classificação Quadripartida de Registros**:
   - **NOVOS (INSERT)**: Registros presentes no lote raspado sem correspondente no banco. Recebem novos Snowflake IDs de 64-bits.
   - **ALTERADOS / REATIVADOS (UPDATE)**: Registros pareados pela Chave Natural com alteração real de atributos ou registros inativos (`ativo = 0`) que voltaram na raspagem (`ativo = 1`).
   - **INATIVADOS (Soft Delete - `ativo = 0`)**: Registros existentes no MySQL (`ativo = 1`) ausentes na nova raspagem completa. Preservados com a flag `ativo = 0` (proibição absoluta de exclusão física `DELETE`).
   - **MANTIDOS**: Registros idênticos entre o banco e a raspagem (ignorados no commit).

2. **Proteção Contra Falsos CEP/UF Updates**:
   - A atualização de CEP ou UF em branco no MySQL é estritamente vinculada à existência de outras divergências cadastradas (`and diferencas`). Registros idênticos sem alterações de nome ou endereço permanecem na categoria `MANTIDOS`.

3. **Trava de Carga Parcial**:
   - Se o volume raspado for inferior a 80% do total do banco de dados, o sistema sinaliza raspagem parcial e bloqueia a inativação automática de registros.

4. **Regra Absoluta de Emojis**:
   - É estritamente proibido o uso de emojis em qualquer resposta, interface, log, tabela ASCII ou documentação do projeto.

---

## 4. Estado de Auditoria e Validação do Código

- **Integridade de Cursors MySQL**: Auditado e confirmado que 100% dos cursores MySQL em `src/backend/` usam `conn.cursor(dictionary=True)`.
- **Suíte de Testes Unitários**: Testes automatizados cobrindo a proteção de numerais romanos, extrator de CEPs, decomposição de municípios sujos, geração de diffs e trava de carga parcial.
- **Sincronização de Relatórios**: Garantido o registro explícito do texto `uf: '' ➔ 'UF'` no campo `diferencas_detectadas` do console e dos relatórios exportados.
