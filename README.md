# CNCT Scraper - Arquitetura do Sistema e Guia de Execucao

## Visao Geral do Projeto

O **CNCT Scraper** e uma solucao de engenharia de dados e raspagem web desenvolvida para extrair, transformar e estruturar informacoes completas sobre cursos tecnicos e instituicoes ofertantes cadastrados no Catologo Nacional de Cursos Tecnicos (CNCT) do MEC.

O projeto resolve o desafio de alta latencia e renderizacao dinamica do portal atraves de uma abordagem em duas fases:
1. **Fase 1**: Mapeamento de rede e captura de APIs REST internas nao documentadas.
2. **Fase 2**: Pipeline de raspagem headless, gerador de Snowflake IDs thread-safe, agregador em C de alta performance e interface WebApp com terminal via WebSockets.

---

## Estrutura de Diretarios Proposta (Fase 2)

```text
CNCT_SCRAPER/
├── README.md
├── discovery_sniffer.py            # Script da Fase 1 (Entregavel Imediato)
├── requirements.txt
├── Makefile                        # Build automation para o modulo C
├── logs/                           # Logs de trafego interceptado da Fase 1
│   ├── network_traffic_*.json
│   └── endpoints_summary_*.json
├── output/                         # Arquivos CSV finais
│   ├── csv_cursos.csv
│   └── csv_instituicoes.csv
├── src/
│   ├── __init__.py
│   ├── main.py                     # Ponto de entrada e orquestrador principal
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── app.py                  # Aplicacao FastAPI com WebSockets / SSE
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── scraper_routes.py   # Controladores de disparo e status
│   │   │   └── data_routes.py      # Download dos arquivos CSV
│   │   └── websocket_manager.py    # Transmissor de logs do terminal em tempo real
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── client.py               # Cliente HTTP / API direta ou Playwright headless
│   │   ├── parser.py               # Extração e normalização de atributos HTML/JSON
│   │   └── pipeline.py             # Orquestracao do fluxo de raspagem
│   ├── utils/
│   │   ├── __init__.py
│   │   └── snowflake.py            # Classe SnowflakeGenerator thread-safe (64-bit)
│   └── c_aggregator/
│       ├── aggregator.c            # Script C de alta performance para associacao de IDs
│       ├── aggregator.h
│       └── bridge.py               # Wrapper Python (ctypes/subprocess) para invocar a C lib
├── frontend/
│   ├── index.html                  # Container HTML puro
│   ├── css/
│   │   ├── styles.css              # Custom Dark/Modern UI styling
│   │   └── terminal.css            # Estilos especificos para simulador de terminal
│   └── js/
│       ├── main.js                 # Scripts de navegacao e alternancia de abas
│       └── terminal.js             # Conexao WebSocket e renderizacao de logs
└── tests/
    ├── __init__.py
    ├── test_snowflake.py           # Testes unitarios do gerador Snowflake
    ├── test_scraper.py             # Testes de extracao e parsing
    ├── test_c_bridge.py            # Testes da integracao Python -> C
    └── test_api.py                 # Testes das rotas FastAPI
```

---

## Fase 1: Script de Descoberta (Sniffer de Rede)

### Descricao
O script [discovery_sniffer.py](file:///c:/Users/ResTIC55/PythonProject/CNCT_SCRAPER/discovery_sniffer.py) utiliza o Playwright em modo headful para interceptar todo o trafego XHR e Fetch durante a navegacao manual no portal do CNCT.

### Como Executar
1. Instalar as dependencias necessarias:
```bash
pip install playwright
playwright install chromium
```
2. Executar o script de inspeção:
```bash
python discovery_sniffer.py
```
3. Navegue manualmente pelas paginas do site. Os dados serao gravados automaticamente no diretorio `logs/`.

---

## Fase 2: Arquitetura Detalhada e Integracao

### 1. Gerador de Snowflake IDs (`src/utils/snowflake.py`)
Utiliza inteiros de 64-bits estruturados da seguinte forma:
- **41 bits**: Timestamp em milissegundos desde o epoch customizado.
- **5 bits**: Identifier de Datacenter.
- **5 bits**: Identifier de Worker.
- **12 bits**: Contador de sequencia incremental.

Garante ordenacao temporal e unicidade em ambientes concorrentes atraves de trava explicita (`threading.Lock`).

### 2. Agregador de Alta Performance em C (`src/c_aggregator/aggregator.c`)
- O processamento de associacao entre instituicoes e cursos oferecidos e delegado a um executavel compilar em C.
- Leitura e gravação de inteiros não assinados de 64-bits utilizando `<stdint.h>` (`uint64_t`) e macros especificas de E/S (`%" SCNu64` e `%" PRIu64` da biblioteca `<inttypes.h>`).
- Reduz o tempo de execucao e consumo de memoria ao processar milhares de relacoes de cursos por instituicao.

### 3. WebApp & Terminal em Tempo Real
- **Backend**: FastAPI com rotas REST e endpoint `/ws/terminal` para streaming de logs.
- **Frontend**: HTML5 sem frameworks pesados, CSS3 estilizado em modo escuro/console e JavaScript Vanilla lidando com WebSockets para transmissao em tempo real dos logs de execucao.

---

## Esquema dos Arquivos CSV de Saida

### `csv_cursos.csv`
| Coluna | Tipo | Descricao |
| :--- | :--- | :--- |
| `id_original` | String / Int | ID original contido na URL ou API do CNCT |
| `snowflake_id` | uint64_t | ID Snowflake de 64-bits gerado no Python |
| `nome_curso` | String | Nome oficial do curso tecnico |
| `eixo_tecnologico` | String | Classificacao do eixo |
| `carga_horaria` | String / Int | Carga horaria minima |
| `perfil_profissional` | String | Descricao do perfil |
| `campo_atuação` | String | Possibilidades de atuacao no mercado |

### `csv_instituicoes.csv`
| Coluna | Tipo | Descricao |
| :--- | :--- | :--- |
| `snowflake_id` | uint64_t | ID Snowflake da instituicao |
| `nome_instituicao` | String | Nome da instituicao ofertante |
| `dependencia_adm` | String | Tipo (Publica, Privada, Federal, etc.) |
| `endereco` | String | Endereco completo |
| `telefone` | String | Numero de contato |
| `email` | String | Endereco de e-mail |
| `homepage` | String | URL do site da instituicao |
| `cursos_ofertados_ids` | JSON / Array | Lista de Snowflake IDs dos cursos oferecidos (gerado pelo script C) |
