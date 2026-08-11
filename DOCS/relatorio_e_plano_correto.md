# Relatório de Diagnóstico e Plano de Correção do Banco de Dados (CNCT Scraper)

> **Data do Documento**: 10 de Agosto de 2026  
> **Sistema**: CNCT Scraper - Módulo de Sincronização e Migração MySQL  
> **Status**: Planejamento e Documentação Técnica (Sem execução automática)

---

## 1. 🚨 Relatório de Diagnóstico: O Que Aconteceu e Por Que Ocorreu?

Na recente tentativa de população do banco de dados MySQL na VPS, foram identificados dois grandes problemas estruturais:

1. **Duplicação de Registros (Tabela dobrada para 32.746 linhas)**:
   - **Causa Raiz**: O script de sincronização no backend (`src/backend/routes/migracao_enderecos.py`) percorreu o array de **todos os 16.389 registros raspados** no CSV e executou um comando `INSERT INTO INSTITUICOES_ENSINO_TECNICO (...)` irrestrito para cada item da carga.
   - Em vez de separar os registros estritamente pelo resultado do **Diff** (`novos`, `alterados`, `mantidos`), a rotina gerou novos Snowflake IDs para os itens e inseriu a carga inteira como novas linhas no banco.
   - Como o banco já possuía ~16.364 registros gravados anteriormente com IDs Snowflake mais antigos, os novos inserts resultaram no dobramento da tabela (16.364 + 16.389 ≈ 32.746 registros).

2. **Endereços Não Desagregados nas Colunas Estruturadas**:
   - **Causa Raiz**: O arquivo CSV gerado pelo scraper (`src/output/csv_instituicoes.csv`) foi projetado com apenas uma coluna genérica de texto chamado `endereco`.
   - Na população direta antiga, o script gravava essa string bruta no campo `endereco` da tabela MySQL e deixava os campos estruturados (`logradouro`, `numero`, `complemento`, `bairro`, `municipio`, `uf`, `cep`) como `NULL`.

---

## 2. 🗄️ Mapeamento do Schema SQL (`DOCS/database/schema.sql`)

Conforme o arquivo oficial [schema.sql](file:///c:/Users/ResTIC55/PythonProject/CNCT_SCRAPER/DOCS/database/schema.sql), a estrutura exata das tabelas envolvidas no ecossistema técnico é a seguinte:

### 2.1. Tabela `INSTITUICOES_ENSINO_TECNICO`
```sql
CREATE TABLE `INSTITUICOES_ENSINO_TECNICO` (
  `id` bigint NOT NULL COMMENT 'ID Snowflake único da instituição técnica (64-bit)',
  `nome_instituicao` varchar(255) NOT NULL COMMENT 'Nome da instituição de ensino técnico',
  `dependencia_adm` varchar(50) DEFAULT NULL COMMENT 'Dependência administrativa (Pública ou Privada)',
  `endereco` text COMMENT 'Endereço completo da unidade (string concatenada)',
  `logradouro` varchar(255) DEFAULT NULL,
  `numero` varchar(255) DEFAULT NULL,
  `complemento` varchar(255) DEFAULT NULL,
  `bairro` varchar(255) DEFAULT NULL,
  `municipio` varchar(255) DEFAULT NULL,
  `uf` varchar(2) DEFAULT NULL,
  `cep` varchar(10) DEFAULT NULL,
  `telefone` varchar(100) DEFAULT NULL COMMENT 'Telefone de contato',
  `email` varchar(255) DEFAULT NULL COMMENT 'E-mail de contato',
  `homepage` varchar(255) DEFAULT NULL COMMENT 'Website oficial da instituição',
  `ativo` tinyint(1) DEFAULT '1',
  `criado_em` datetime DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_unique_inst_id` (`id`),
  KEY `idx_inst_tecnicas_nome` (`nome_instituicao`),
  KEY `idx_inst_tec_uf_municipio` (`uf`,`municipio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### 2.2. Tabela `CURSOS_TECNICOS`
```sql
CREATE TABLE `CURSOS_TECNICOS` (
  `id` bigint NOT NULL COMMENT 'ID Snowflake único do curso técnico (64-bit)',
  `id_original` int DEFAULT NULL COMMENT 'ID sequencial original do catálogo CNCT/MEC',
  `nome_curso` varchar(255) NOT NULL COMMENT 'Nome oficial do curso técnico',
  `eixo_tecnologico` varchar(255) DEFAULT NULL,
  `carga_horaria` text,
  `pre_requisito` text,
  `perfil_profissional` text,
  `itinerarios` text,
  `campo_atuacao` text,
  `ocupacoes_cbo` text,
  `infraestrutura_minima` text,
  `ativo` tinyint(1) DEFAULT '1',
  `criado_em` datetime DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### 2.3. Tabela de Relacionamento `INSTITUICOES_CURSOS_TECNICOS_OFERTADOS`
```sql
CREATE TABLE `INSTITUICOES_CURSOS_TECNICOS_OFERTADOS` (
  `id` bigint NOT NULL COMMENT 'ID Snowflake único do vínculo de oferta (64-bit)',
  `instituicao_tecnica_id` bigint NOT NULL COMMENT 'FK da instituição de ensino técnico',
  `curso_tecnico_id` bigint NOT NULL COMMENT 'FK do curso técnico ofertado',
  `criado_em` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_inst_curso_tecnico` (`instituicao_tecnica_id`,`curso_tecnico_id`),
  CONSTRAINT `fk_oferta_curso_tecnico` FOREIGN KEY (`curso_tecnico_id`) REFERENCES `CURSOS_TECNICOS` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_oferta_inst_tecnica` FOREIGN KEY (`instituicao_tecnica_id`) REFERENCES `INSTITUICOES_ENSINO_TECNICO` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

---

## 3. 📋 Adequação do Algoritmo de Geração do CSV

Para garantir que o arquivo CSV de instituições esteja 100% pronto para o schema do banco de dados, o algoritmo de exportação em `src/c_aggregator/bridge.py` e `src/scraper/` deve ser alterado para incluir os campos desagregados nativamente.

### Novo Cabeçalho do CSV (`src/output/csv_instituicoes.csv`):
```csv
snowflake_id;nome_instituicao;dependencia_adm;endereco_completo;logradouro;numero;complemento;bairro;municipio;uf;cep;telefone;email;homepage;cursos_ofertados_ids
```

#### Alteração no Código de Exportação (Python / C Bridge):
No ato de escrever cada linha do CSV, o motor chamará o parser C de alta velocidade (`parse_address_c`) para preencher as colunas:
```python
parsed = parse_address_c(row["endereco"])
writer.writerow([
    sf_id,
    row["nome_instituicao"],
    row["dependencia_adm"],
    row["endereco"],           # endereco_completo
    parsed["logradouro"],     # logradouro
    parsed["numero"],         # numero
    parsed["complemento"],    # complemento
    parsed["bairro"],         # bairro
    parsed["municipio"],      # municipio
    parsed["uf"],             # uf
    parsed["cep"],            # cep
    row["telefone"],
    row["email"],
    row["homepage"],
    json.dumps(cursos_ids)
])
```

---

## 4. ⚙️ Regras do Script de População do Banco de Dados

A rotina de sincronização no backend (`src/backend/routes/migracao_enderecos.py`) deve ser reestruturada para obedecer **estritamente** aos grupos do resultado da engine de Diff em C (`compare_datasets_c`):

```
                       [ RESULTADO DO DIFF EM C ]
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
   ┌───────────┐             ┌───────────┐             ┌───────────┐
   │   NOVOS   │             │ ALTERADOS │             │ MANTIDOS  │
   └─────┬─────┘             └─────┬─────┘             └─────┬─────┘
         │                         │                         │
         ▼                         ▼                         ▼
   INSERT APENAS             UPDATE APENAS               IGNORAR
   Instituições              Campos alterados            (NENHUMA
   e Cursos novos            no registro existente       AÇÃO NO DB)
```

### 4.0. Regra de Negócio dos Identificadores Snowflake ID (Ciclo de Vida e Pareamento)
- **Desuso de ID Sintético no Diff**: Os dados brutos raspados do portal MEC/CNCT pertencem ao mundo real e **não possuem Snowflake ID interno** (o servidor do MEC desconhece a chave primária da nossa VPS). Portanto, IDs Snowflake **não devem ser gerados previamente nem utilizados para comparar dados raspados no Diff**.
- **Pareamento Exclusivo por Chaves Naturais**: Na comparação entre raspagem e MySQL, o motor de Diff ignora IDs provisórios do CSV e realiza o casamento **estritamente via Chaves Naturais reais**:
  1. *Chave Natural Completa*: `Nome Expandido + Município Normalizado + UF`.
  2. *Chave Core*: `Nome sem Prefixos Genéricos + Município Normalizado + UF`.
  3. *Intersecção de Tokens*: Palavras-chave no mesmo Município e UF.
- **Preservação do ID do Banco**: Quando o Diff encontra a escola no MySQL por Chave Natural, a entidade herda o **ID original do banco de dados**.
- **Geração de ID Exclusiva para Itens NOVOS**: Apenas quando o Diff confirma que a escola é **realmente nova** (`is_novo = True`), o gerador `SnowflakeGenerator` é acionado **no ato da gravação (`INSERT`)** para criar o Snowflake ID de 64-bits.

### 4.1. Grupo NOVOS (`res['novos']`)
- **Ação**: Executar `INSERT INTO INSTITUICOES_ENSINO_TECNICO`.
- **Regra**: Gerar um novo Snowflake ID definitivo. Inserir todas as colunas (incluindo `logradouro`, `numero`, `bairro`, `municipio`, `uf`, `cep`).
- **Cursos**: Para cada curso vinculado que seja novo, criar a oferta em `INSTITUICOES_CURSOS_TECNICOS_OFERTADOS`.

### 4.2. Grupo ALTERADOS (`res['alterados']`)
- **Ação**: Executar `UPDATE INSTITUICOES_ENSINO_TECNICO`.
- **Regra**: Atualizar **apenas** o registro existente com a chave `id` correspondente.
- **SQL de Exemplo**:
  ```sql
  UPDATE INSTITUICOES_ENSINO_TECNICO SET
      logradouro = %s,
      numero = %s,
      complemento = %s,
      bairro = %s,
      municipio = %s,
      uf = %s,
      cep = %s,
      endereco = %s,
      atualizado_em = NOW()
  WHERE id = %s;
  ```
- **Proibição**: Jamais executar `INSERT` para itens alterados!

### 4.3. Grupo MANTIDOS (`res['mantidos']`)
- **Ação**: **NENHUMA**.
- **Regra**: Ignorar completamente estes registros durante a gravação no banco de dados.

### 4.4. Grupo INATIVADOS (`res['inativados']`) - Regra de Negócio Detalhada
- **Ação**: Executar a **Inativação Lógica (*Soft Delete*)**: `UPDATE INSTITUICOES_ENSINO_TECNICO SET ativo = 0, atualizado_em = NOW() WHERE id IN (...)`.
- **Regras de Negócio**:
  1. **Inativação Lógica (Sem `DELETE` físico)**: Registros legados nunca são apagados do banco para preservar o histórico de formações de candidatos e auditorias LGPD.
  2. **Critério de Identificação no Diff**: Um registro do banco de dados (MySQL) entra na lista de inativados **apenas se existir no banco como `ativo = 1` e NÃO for localizado no lote do CSV em nenhum dos 4 níveis de casamento** (Snowflake ID, Chave Natural Completa, Chave Core e Intersecção de Tokens).
  3. **Trava de Segurança para Cargas Parciais (`is_parcial = False`)**: A inativação em massa só é aplicada se a sincronização for do tipo **Total / Completa**. Se o usuário executar uma carga parcial (ex: raspagem filtrada de 1 estado ou poucos cursos), o motor define `is_parcial = True` e a inativação é automaticamente desativada/bloqueada para evitar inativar instituições legitimas por falha de escopo.

---

## 5. 🧹 Script de Limpeza dos Dados Inseridos desde 09/08/2026

O script Python para realizar o expurgo seguro das linhas duplicadas/inseridas incorretamente a partir de **09 de agosto de 2026** foi gerado no arquivo:
👉 [scratch/cleanup_since_aug09.py](file:///c:/Users/ResTIC55/PythonProject/CNCT_SCRAPER/scratch/cleanup_since_aug09.py)

> ⚠️ **Nota**: Este script é um utilitário para ser executado manualmente quando você desejar. Ele **não** foi executado e possui trava de segurança `dry-run` por padrão.
