-- MySQL dump 10.13  Distrib 8.4.10, for Linux (aarch64)
--
-- Host: localhost    Database: default
-- ------------------------------------------------------
-- Server version	8.4.10

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `ANEXOS`
--

DROP TABLE IF EXISTS `ANEXOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ANEXOS` (
  `id` bigint NOT NULL,
  `usuario_id` bigint DEFAULT NULL,
  `tipo_entidade` varchar(255) DEFAULT NULL COMMENT 'Polimorfismo (VAGA, CURRICULO, COMPROVANTE)',
  `entidade_id` bigint DEFAULT NULL,
  `tipo_arquivo` varchar(255) DEFAULT NULL,
  `nome_arquivo` varchar(255) DEFAULT NULL,
  `caminho_arquivo` varchar(255) DEFAULT NULL COMMENT 'URI S3',
  `mime_type` varchar(255) DEFAULT NULL,
  `tamanho_bytes` bigint DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  KEY `idx_anexos_polimorfo` (`tipo_entidade`,`entidade_id`),
  CONSTRAINT `ANEXOS_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `AREAS_PROFISSIONAIS`
--

DROP TABLE IF EXISTS `AREAS_PROFISSIONAIS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `AREAS_PROFISSIONAIS` (
  `id` bigint NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `AUDITORIA_EVENTOS`
--

DROP TABLE IF EXISTS `AUDITORIA_EVENTOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `AUDITORIA_EVENTOS` (
  `id` bigint NOT NULL COMMENT 'Tabela de conformidade LGPD',
  `usuario_id` bigint DEFAULT NULL,
  `origem` varchar(255) DEFAULT NULL,
  `recurso` varchar(255) DEFAULT NULL,
  `acao` varchar(255) DEFAULT NULL,
  `metodo_http` varchar(255) DEFAULT NULL,
  `payload_resumo` text,
  `ip` varchar(255) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `status_http` int DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `AUDITORIA_EVENTOS_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CANDIDATOS`
--

DROP TABLE IF EXISTS `CANDIDATOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CANDIDATOS` (
  `id` bigint NOT NULL,
  `usuario_id` bigint DEFAULT NULL,
  `endereco_id` bigint DEFAULT NULL,
  `resumo_profissional` text,
  `pretensao_salarial` decimal(12,2) DEFAULT NULL,
  `possui_deficiencia` tinyint(1) DEFAULT NULL,
  `tipo_deficiencia` varchar(255) DEFAULT NULL,
  `detalhes_deficiencia` text,
  `perfil_completo` tinyint(1) DEFAULT NULL,
  `status_perfil` varchar(255) DEFAULT NULL,
  `momento_carreira` varchar(50) DEFAULT NULL COMMENT 'DESEMPREGADO, BUSCANDO_MELHORIA, PRIMEIRA_OPORTUNIDADE, TRANSICAO_CARREIRA',
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario_id` (`usuario_id`),
  KEY `idx_candidatos_localizacao` (`endereco_id`,`perfil_completo`),
  CONSTRAINT `CANDIDATOS_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`),
  CONSTRAINT `CANDIDATOS_ibfk_2` FOREIGN KEY (`endereco_id`) REFERENCES `ENDERECOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CANDIDATO_COMPETENCIAS_DIGITAIS`
--

DROP TABLE IF EXISTS `CANDIDATO_COMPETENCIAS_DIGITAIS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CANDIDATO_COMPETENCIAS_DIGITAIS` (
  `id` bigint NOT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `competencia_id` bigint DEFAULT NULL,
  `nivel` tinyint NOT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `candidato_id` (`candidato_id`),
  KEY `competencia_id` (`competencia_id`),
  CONSTRAINT `CANDIDATO_COMPETENCIAS_DIGITAIS_ibfk_1` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`),
  CONSTRAINT `CANDIDATO_COMPETENCIAS_DIGITAIS_ibfk_2` FOREIGN KEY (`competencia_id`) REFERENCES `COMPETENCIAS_DIGITAIS` (`id`),
  CONSTRAINT `chk_candidato_comp_nivel` CHECK ((`nivel` between 1 and 5))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CANDIDATO_EXPERIENCIAS`
--

DROP TABLE IF EXISTS `CANDIDATO_EXPERIENCIAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CANDIDATO_EXPERIENCIAS` (
  `id` bigint NOT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `empresa_nome` varchar(255) DEFAULT NULL,
  `cargo` varchar(255) DEFAULT NULL,
  `atividades` text,
  `ultimo_salario` decimal(12,2) DEFAULT NULL,
  `data_inicio` date DEFAULT NULL,
  `data_fim` date DEFAULT NULL,
  `emprego_atual` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `candidato_id` (`candidato_id`),
  CONSTRAINT `CANDIDATO_EXPERIENCIAS_ibfk_1` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CANDIDATO_FORMACOES`
--

DROP TABLE IF EXISTS `CANDIDATO_FORMACOES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CANDIDATO_FORMACOES` (
  `id` bigint NOT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `instituicao_id` bigint DEFAULT NULL,
  `curso_id` bigint DEFAULT NULL,
  `nivel_formacao` varchar(255) DEFAULT NULL,
  `status_formacao` varchar(255) DEFAULT NULL,
  `data_inicio` date DEFAULT NULL,
  `data_conclusao` date DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `candidato_id` (`candidato_id`),
  KEY `instituicao_id` (`instituicao_id`),
  KEY `curso_id` (`curso_id`),
  CONSTRAINT `CANDIDATO_FORMACOES_ibfk_1` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`),
  CONSTRAINT `CANDIDATO_FORMACOES_ibfk_2` FOREIGN KEY (`instituicao_id`) REFERENCES `INSTITUICOES_ENSINO` (`id`),
  CONSTRAINT `CANDIDATO_FORMACOES_ibfk_3` FOREIGN KEY (`curso_id`) REFERENCES `CURSOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CANDIDATO_FORMACOES_TECNICAS`
--

DROP TABLE IF EXISTS `CANDIDATO_FORMACOES_TECNICAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CANDIDATO_FORMACOES_TECNICAS` (
  `id` bigint NOT NULL COMMENT 'ID Snowflake único do registro de formação técnica (64-bit)',
  `candidato_id` bigint NOT NULL COMMENT 'FK do candidato na tabela CANDIDATOS',
  `instituicao_tecnica_id` bigint DEFAULT NULL COMMENT 'FK da instituição técnica',
  `curso_tecnico_id` bigint DEFAULT NULL COMMENT 'FK do curso técnico',
  `status_formacao` varchar(100) DEFAULT NULL COMMENT 'CONCLUIDO, EM_ANDAMENTO, TRANCADO, INTERROMPIDO',
  `data_inicio` date DEFAULT NULL,
  `data_conclusao` date DEFAULT NULL,
  `criado_em` datetime DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_cand_form_tec_candidato` (`candidato_id`),
  KEY `idx_cand_form_tec_inst` (`instituicao_tecnica_id`),
  KEY `idx_cand_form_tec_curso` (`curso_tecnico_id`),
  CONSTRAINT `fk_cand_form_tec_candidato` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_cand_form_tec_curso` FOREIGN KEY (`curso_tecnico_id`) REFERENCES `CURSOS_TECNICOS` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_cand_form_tec_inst` FOREIGN KEY (`instituicao_tecnica_id`) REFERENCES `INSTITUICOES_ENSINO_TECNICO` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CANDIDATO_HABILIDADES`
--

DROP TABLE IF EXISTS `CANDIDATO_HABILIDADES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CANDIDATO_HABILIDADES` (
  `id` bigint NOT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `categoria` varchar(255) DEFAULT NULL,
  `nivel` varchar(255) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `candidato_id` (`candidato_id`),
  CONSTRAINT `CANDIDATO_HABILIDADES_ibfk_1` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CANDIDATO_IDIOMAS`
--

DROP TABLE IF EXISTS `CANDIDATO_IDIOMAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CANDIDATO_IDIOMAS` (
  `id` bigint NOT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `idioma_id` bigint DEFAULT NULL,
  `leitura_nivel` int DEFAULT NULL,
  `escrita_nivel` int DEFAULT NULL,
  `fala_nivel` int DEFAULT NULL,
  `compreensao_nivel` int DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `candidato_id` (`candidato_id`),
  KEY `idioma_id` (`idioma_id`),
  CONSTRAINT `CANDIDATO_IDIOMAS_ibfk_1` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`),
  CONSTRAINT `CANDIDATO_IDIOMAS_ibfk_2` FOREIGN KEY (`idioma_id`) REFERENCES `IDIOMAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CANDIDATO_INTERESSES`
--

DROP TABLE IF EXISTS `CANDIDATO_INTERESSES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CANDIDATO_INTERESSES` (
  `id` bigint NOT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `hobbies` text,
  `esportes` text,
  `paixoes` text,
  `informacoes_extras` text,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `candidato_id` (`candidato_id`),
  CONSTRAINT `CANDIDATO_INTERESSES_ibfk_1` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CANDIDATO_LACUNAS`
--

DROP TABLE IF EXISTS `CANDIDATO_LACUNAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CANDIDATO_LACUNAS` (
  `id` bigint NOT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `tipo_competencia` varchar(255) DEFAULT NULL,
  `nome_competencia` varchar(255) DEFAULT NULL,
  `nivel_exigido_mercado` varchar(255) DEFAULT NULL,
  `quantidade_vagas_perdidas` int DEFAULT NULL,
  `curso_recomendado_id` bigint DEFAULT NULL,
  `notificado` tinyint(1) DEFAULT NULL,
  `identificado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `candidato_id` (`candidato_id`),
  KEY `curso_recomendado_id` (`curso_recomendado_id`),
  CONSTRAINT `CANDIDATO_LACUNAS_ibfk_1` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`),
  CONSTRAINT `CANDIDATO_LACUNAS_ibfk_2` FOREIGN KEY (`curso_recomendado_id`) REFERENCES `CURSOS_OFERTAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CANDIDATURAS`
--

DROP TABLE IF EXISTS `CANDIDATURAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CANDIDATURAS` (
  `id` bigint NOT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `vaga_id` bigint DEFAULT NULL,
  `status` varchar(255) DEFAULT NULL,
  `observacoes` text,
  `candidatura_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `candidato_id` (`candidato_id`),
  KEY `vaga_id` (`vaga_id`),
  CONSTRAINT `CANDIDATURAS_ibfk_1` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`),
  CONSTRAINT `CANDIDATURAS_ibfk_2` FOREIGN KEY (`vaga_id`) REFERENCES `VAGAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CANDIDATURA_ETAPAS`
--

DROP TABLE IF EXISTS `CANDIDATURA_ETAPAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CANDIDATURA_ETAPAS` (
  `id` bigint NOT NULL,
  `candidatura_id` bigint DEFAULT NULL,
  `etapa_id` bigint DEFAULT NULL,
  `status` varchar(255) DEFAULT NULL,
  `observacao` text,
  `iniciado_em` datetime DEFAULT NULL,
  `concluido_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `candidatura_id` (`candidatura_id`),
  KEY `etapa_id` (`etapa_id`),
  CONSTRAINT `CANDIDATURA_ETAPAS_ibfk_1` FOREIGN KEY (`candidatura_id`) REFERENCES `CANDIDATURAS` (`id`),
  CONSTRAINT `CANDIDATURA_ETAPAS_ibfk_2` FOREIGN KEY (`etapa_id`) REFERENCES `ETAPAS_PROCESSO_SELETIVO` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `COMPETENCIAS_DIGITAIS`
--

DROP TABLE IF EXISTS `COMPETENCIAS_DIGITAIS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMPETENCIAS_DIGITAIS` (
  `id` bigint NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `categoria_id` bigint NOT NULL,
  `descricao` varchar(255) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `COMPETENCIAS_DIGITAIS_ibfk_1` (`categoria_id`),
  CONSTRAINT `COMPETENCIAS_DIGITAIS_ibfk_1` FOREIGN KEY (`categoria_id`) REFERENCES `COMPETENCIA_CATEGORIAS` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `COMPETENCIA_CATEGORIAS`
--

DROP TABLE IF EXISTS `COMPETENCIA_CATEGORIAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `COMPETENCIA_CATEGORIAS` (
  `id` bigint NOT NULL,
  `nome` varchar(100) NOT NULL,
  `descricao` varchar(255) DEFAULT NULL,
  `categoria_pai_id` bigint DEFAULT NULL,
  `ordem` int DEFAULT '0',
  `ativo` tinyint DEFAULT '1',
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_categoria_pai_id` (`categoria_pai_id`),
  CONSTRAINT `COMPETENCIA_CATEGORIAS_ibfk_1` FOREIGN KEY (`categoria_pai_id`) REFERENCES `COMPETENCIA_CATEGORIAS` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CURRICULOS`
--

DROP TABLE IF EXISTS `CURRICULOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CURRICULOS` (
  `id` bigint NOT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `titulo` varchar(255) DEFAULT NULL,
  `carta_apresentacao` text,
  `objetivo_profissional` text,
  `publico` tinyint(1) DEFAULT NULL,
  `status` varchar(255) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `candidato_id` (`candidato_id`),
  CONSTRAINT `CURRICULOS_ibfk_1` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CURRICULOS_GERADOS`
--

DROP TABLE IF EXISTS `CURRICULOS_GERADOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CURRICULOS_GERADOS` (
  `id` bigint NOT NULL,
  `curriculo_id` bigint DEFAULT NULL,
  `template_id` bigint DEFAULT NULL,
  `anexo_id` bigint DEFAULT NULL COMMENT 'Link para o PDF final gerado salvo na tabela ANEXOS',
  `gerado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `curriculo_id` (`curriculo_id`),
  KEY `template_id` (`template_id`),
  KEY `anexo_id` (`anexo_id`),
  CONSTRAINT `CURRICULOS_GERADOS_ibfk_1` FOREIGN KEY (`curriculo_id`) REFERENCES `CURRICULOS` (`id`),
  CONSTRAINT `CURRICULOS_GERADOS_ibfk_2` FOREIGN KEY (`template_id`) REFERENCES `TEMPLATES_CURRICULOS` (`id`),
  CONSTRAINT `CURRICULOS_GERADOS_ibfk_3` FOREIGN KEY (`anexo_id`) REFERENCES `ANEXOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CURSOS`
--

DROP TABLE IF EXISTS `CURSOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CURSOS` (
  `id` bigint NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `area` varchar(255) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CURSOS_OFERTAS`
--

DROP TABLE IF EXISTS `CURSOS_OFERTAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CURSOS_OFERTAS` (
  `id` bigint NOT NULL,
  `curso_id` bigint DEFAULT NULL,
  `instituicao_ensino_id` bigint DEFAULT NULL COMMENT 'Quem vai lecionar',
  `mantenedora_id` bigint DEFAULT NULL COMMENT 'Quem financia',
  `modalidade` varchar(255) DEFAULT NULL COMMENT 'EAD, Presencial, Hibrido',
  `data_inicio` date DEFAULT NULL,
  `carga_horaria` int DEFAULT NULL,
  `vagas_disponiveis` int DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `curso_id` (`curso_id`),
  KEY `instituicao_ensino_id` (`instituicao_ensino_id`),
  KEY `mantenedora_id` (`mantenedora_id`),
  CONSTRAINT `CURSOS_OFERTAS_ibfk_1` FOREIGN KEY (`curso_id`) REFERENCES `CURSOS` (`id`),
  CONSTRAINT `CURSOS_OFERTAS_ibfk_2` FOREIGN KEY (`instituicao_ensino_id`) REFERENCES `INSTITUICOES_ENSINO` (`id`),
  CONSTRAINT `CURSOS_OFERTAS_ibfk_3` FOREIGN KEY (`mantenedora_id`) REFERENCES `MANTENEDORAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CURSOS_TECNICOS`
--

DROP TABLE IF EXISTS `CURSOS_TECNICOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CURSOS_TECNICOS` (
  `id` bigint NOT NULL COMMENT 'ID Snowflake único do curso técnico (64-bit)',
  `id_original` int DEFAULT NULL COMMENT 'ID sequencial original do catálogo CNCT/MEC',
  `nome_curso` varchar(255) NOT NULL COMMENT 'Nome oficial do curso técnico',
  `eixo_tecnologico` varchar(255) DEFAULT NULL COMMENT 'Eixo tecnológico do MEC',
  `carga_horaria` text COMMENT 'Descrição detalhada de carga horária e modalidades',
  `pre_requisito` text COMMENT 'Requisitos de escolaridade para ingresso',
  `perfil_profissional` text COMMENT 'Competências e perfil de conclusão do profissional',
  `itinerarios` text COMMENT 'Itinerários formativos e especializações técnicas',
  `campo_atuacao` text COMMENT 'Locais e setores de atuação no mercado',
  `ocupacoes_cbo` text COMMENT 'Códigos e títulos CBO associados',
  `infraestrutura_minima` text COMMENT 'Infraestrutura e laboratórios exigidos pelo MEC',
  `ativo` tinyint(1) DEFAULT '1',
  `criado_em` datetime DEFAULT CURRENT_TIMESTAMP,
  `atualizado_em` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_cursos_tecnicos_nome` (`nome_curso`),
  KEY `idx_cursos_tecnicos_eixo` (`eixo_tecnologico`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CURSO_AULAS`
--

DROP TABLE IF EXISTS `CURSO_AULAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CURSO_AULAS` (
  `id` bigint NOT NULL,
  `oferta_id` bigint DEFAULT NULL,
  `data_aula` date DEFAULT NULL,
  `conteudo_previsto` text,
  `carga_horaria_aula` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `oferta_id` (`oferta_id`),
  CONSTRAINT `CURSO_AULAS_ibfk_1` FOREIGN KEY (`oferta_id`) REFERENCES `CURSOS_OFERTAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CURSO_FREQUENCIA`
--

DROP TABLE IF EXISTS `CURSO_FREQUENCIA`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CURSO_FREQUENCIA` (
  `id` bigint NOT NULL,
  `aula_id` bigint DEFAULT NULL,
  `matricula_id` bigint DEFAULT NULL,
  `presente` tinyint(1) DEFAULT NULL,
  `justificativa_falta` text,
  PRIMARY KEY (`id`),
  KEY `aula_id` (`aula_id`),
  KEY `matricula_id` (`matricula_id`),
  CONSTRAINT `CURSO_FREQUENCIA_ibfk_1` FOREIGN KEY (`aula_id`) REFERENCES `CURSO_AULAS` (`id`),
  CONSTRAINT `CURSO_FREQUENCIA_ibfk_2` FOREIGN KEY (`matricula_id`) REFERENCES `CURSO_MATRICULAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CURSO_MATRICULAS`
--

DROP TABLE IF EXISTS `CURSO_MATRICULAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CURSO_MATRICULAS` (
  `id` bigint NOT NULL,
  `oferta_id` bigint DEFAULT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `status` varchar(255) DEFAULT NULL COMMENT 'MATRICULADO, LISTA_ESPERA, CONCLUIDO, NAO_COMPARECEU, EVADIDO',
  `nota_final` decimal(5,2) DEFAULT NULL,
  `frequencia_percentual` decimal(5,2) DEFAULT NULL,
  `data_matricula` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `oferta_id` (`oferta_id`),
  KEY `candidato_id` (`candidato_id`),
  CONSTRAINT `CURSO_MATRICULAS_ibfk_1` FOREIGN KEY (`oferta_id`) REFERENCES `CURSOS_OFERTAS` (`id`),
  CONSTRAINT `CURSO_MATRICULAS_ibfk_2` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DASHBOARD_CONFIGURACOES`
--

DROP TABLE IF EXISTS `DASHBOARD_CONFIGURACOES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DASHBOARD_CONFIGURACOES` (
  `id` bigint NOT NULL,
  `servidor_prefeitura_id` bigint DEFAULT NULL,
  `nome_dashboard` varchar(255) DEFAULT NULL,
  `tipo_visualizacao` varchar(255) DEFAULT NULL,
  `filtros_padrao_json` text,
  `widgets_ativos_json` text,
  `publico_orgao` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `servidor_prefeitura_id` (`servidor_prefeitura_id`),
  CONSTRAINT `DASHBOARD_CONFIGURACOES_ibfk_1` FOREIGN KEY (`servidor_prefeitura_id`) REFERENCES `SERVIDORES_PREFEITURA` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DASHBOARD_EXPORTACOES`
--

DROP TABLE IF EXISTS `DASHBOARD_EXPORTACOES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DASHBOARD_EXPORTACOES` (
  `id` bigint NOT NULL,
  `servidor_prefeitura_id` bigint DEFAULT NULL,
  `orgao_id` bigint DEFAULT NULL,
  `tipo_relatorio` varchar(255) DEFAULT NULL,
  `formato_arquivo` varchar(255) DEFAULT NULL,
  `parametros_json` text,
  `caminho_arquivo` varchar(255) DEFAULT NULL,
  `status_geracao` varchar(255) DEFAULT NULL,
  `solicitado_em` datetime DEFAULT NULL,
  `gerado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `servidor_prefeitura_id` (`servidor_prefeitura_id`),
  KEY `orgao_id` (`orgao_id`),
  CONSTRAINT `DASHBOARD_EXPORTACOES_ibfk_1` FOREIGN KEY (`servidor_prefeitura_id`) REFERENCES `SERVIDORES_PREFEITURA` (`id`),
  CONSTRAINT `DASHBOARD_EXPORTACOES_ibfk_2` FOREIGN KEY (`orgao_id`) REFERENCES `PREFEITURA_ORGAOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DASHBOARD_LACUNAS_BAIRRO`
--

DROP TABLE IF EXISTS `DASHBOARD_LACUNAS_BAIRRO`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DASHBOARD_LACUNAS_BAIRRO` (
  `id` bigint NOT NULL,
  `data_referencia` date DEFAULT NULL,
  `bairro` varchar(255) DEFAULT NULL,
  `cidade` varchar(255) DEFAULT NULL,
  `uf` varchar(255) DEFAULT NULL,
  `tipo_competencia` varchar(255) DEFAULT NULL,
  `nome_competencia` varchar(255) DEFAULT NULL,
  `total_candidatos_bairro` int DEFAULT NULL,
  `total_sem_competencia` int DEFAULT NULL COMMENT 'Métrica local para distribuição geográfica de turmas',
  `gerado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DASHBOARD_LACUNAS_CIDADE`
--

DROP TABLE IF EXISTS `DASHBOARD_LACUNAS_CIDADE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DASHBOARD_LACUNAS_CIDADE` (
  `id` bigint NOT NULL,
  `data_referencia` date DEFAULT NULL,
  `cidade` varchar(255) DEFAULT NULL,
  `uf` varchar(255) DEFAULT NULL,
  `tipo_competencia` varchar(255) DEFAULT NULL,
  `nome_competencia` varchar(255) DEFAULT NULL,
  `total_candidatos_cidade` int DEFAULT NULL COMMENT 'Total de candidatos ativos na cidade',
  `total_sem_competencia` int DEFAULT NULL COMMENT 'Total de pessoas na cidade que necessitam da qualificação',
  `gerado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DASHBOARD_LACUNAS_MERCADO`
--

DROP TABLE IF EXISTS `DASHBOARD_LACUNAS_MERCADO`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DASHBOARD_LACUNAS_MERCADO` (
  `id` bigint NOT NULL,
  `data_referencia` date DEFAULT NULL,
  `tipo_competencia` varchar(255) DEFAULT NULL COMMENT 'Ex: IDIOMA, COMPETENCIA_DIGITAL, HABILIDADE_TECNICA',
  `nome_competencia` varchar(255) DEFAULT NULL,
  `total_vagas_exigindo` int DEFAULT NULL COMMENT 'Demanda total do mercado',
  `total_candidatos_possui` int DEFAULT NULL COMMENT 'Oferta total de profissionais',
  `gap_absoluto` int DEFAULT NULL COMMENT 'Vagas exigindo - Candidatos que possuem',
  `indice_escassez` decimal(5,2) DEFAULT NULL,
  `gerado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DASHBOARD_METRICAS_BAIRRO`
--

DROP TABLE IF EXISTS `DASHBOARD_METRICAS_BAIRRO`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DASHBOARD_METRICAS_BAIRRO` (
  `id` bigint NOT NULL,
  `data_referencia` date DEFAULT NULL,
  `bairro` varchar(255) DEFAULT NULL,
  `cidade` varchar(255) DEFAULT NULL,
  `uf` varchar(255) DEFAULT NULL,
  `total_candidatos_desempregados` int DEFAULT NULL,
  `total_candidatos_empregados` int DEFAULT NULL,
  `total_candidatos_buscando` int DEFAULT NULL,
  `total_empresas` int DEFAULT NULL,
  `total_vagas_disponiveis` int DEFAULT NULL,
  `total_intermediacoes` int DEFAULT NULL,
  `latitude_centroide` decimal(10,8) DEFAULT NULL,
  `longitude_centroide` decimal(11,8) DEFAULT NULL,
  `gerado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DASHBOARD_METRICAS_EMPRESA`
--

DROP TABLE IF EXISTS `DASHBOARD_METRICAS_EMPRESA`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DASHBOARD_METRICAS_EMPRESA` (
  `id` bigint NOT NULL,
  `data_referencia` date DEFAULT NULL,
  `empresa_id` bigint DEFAULT NULL,
  `empresa_nome_fantasia` varchar(255) DEFAULT NULL,
  `empresa_bairro` varchar(255) DEFAULT NULL,
  `empresa_cidade` varchar(255) DEFAULT NULL,
  `empresa_uf` varchar(255) DEFAULT NULL,
  `empresa_setor` varchar(255) DEFAULT NULL,
  `empresa_porte` varchar(255) DEFAULT NULL,
  `total_vagas_abertas` int DEFAULT NULL,
  `total_vagas_preenchidas` int DEFAULT NULL,
  `total_vagas_expiradas` int DEFAULT NULL,
  `total_candidaturas_recebidas` int DEFAULT NULL,
  `total_intermediacoes` int DEFAULT NULL,
  `taxa_preenchimento` decimal(5,2) DEFAULT NULL,
  `gerado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `empresa_id` (`empresa_id`),
  CONSTRAINT `DASHBOARD_METRICAS_EMPRESA_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `EMPRESAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DASHBOARD_METRICAS_PERIODO`
--

DROP TABLE IF EXISTS `DASHBOARD_METRICAS_PERIODO`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DASHBOARD_METRICAS_PERIODO` (
  `id` bigint NOT NULL,
  `data_inicio` date DEFAULT NULL,
  `data_fim` date DEFAULT NULL,
  `granularidade` varchar(255) DEFAULT NULL,
  `dimensao` varchar(255) DEFAULT NULL,
  `valor_dimensao` varchar(255) DEFAULT NULL,
  `total_intermediacoes` int DEFAULT NULL,
  `total_candidaturas` int DEFAULT NULL,
  `total_vagas_abertas` int DEFAULT NULL,
  `total_vagas_preenchidas` int DEFAULT NULL,
  `total_usuarios_ativos` int DEFAULT NULL,
  `total_novos_cadastros` int DEFAULT NULL,
  `gerado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DASHBOARD_SNAPSHOTS_DIARIOS`
--

DROP TABLE IF EXISTS `DASHBOARD_SNAPSHOTS_DIARIOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DASHBOARD_SNAPSHOTS_DIARIOS` (
  `id` bigint NOT NULL,
  `data_referencia` date DEFAULT NULL,
  `total_usuarios_ativos` int DEFAULT NULL,
  `total_candidatos_ativos` int DEFAULT NULL,
  `total_empresas_ativas` int DEFAULT NULL,
  `total_empresas_cadastradas` int DEFAULT NULL,
  `total_vagas_abertas` int DEFAULT NULL,
  `total_vagas_preenchidas` int DEFAULT NULL,
  `total_vagas_expiradas` int DEFAULT NULL,
  `total_candidaturas_dia` int DEFAULT NULL,
  `total_intermediacoes_dia` int DEFAULT NULL,
  `total_matchings_dia` int DEFAULT NULL,
  `total_novos_usuarios_dia` int DEFAULT NULL,
  `total_novas_empresas_dia` int DEFAULT NULL,
  `total_novas_vagas_dia` int DEFAULT NULL,
  `taxa_conversao_candidatura` decimal(5,2) DEFAULT NULL,
  `taxa_preenchimento_vagas` decimal(5,2) DEFAULT NULL,
  `gerado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMBEDDINGS`
--

DROP TABLE IF EXISTS `EMBEDDINGS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `EMBEDDINGS` (
  `id` bigint NOT NULL,
  `tipo_entidade` varchar(255) DEFAULT NULL COMMENT 'Ex: VAGA ou CURRICULO',
  `entidade_id` bigint DEFAULT NULL,
  `modelo` varchar(255) DEFAULT NULL,
  `texto_base` text,
  `vetor_serializado` longtext COMMENT 'pgvector / array de floats',
  `hash_texto` varchar(255) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_embeddings_polimorfo` (`tipo_entidade`,`entidade_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMPRESAS`
--

DROP TABLE IF EXISTS `EMPRESAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `EMPRESAS` (
  `id` bigint NOT NULL,
  `razao_social` varchar(255) DEFAULT NULL,
  `nome_fantasia` varchar(255) DEFAULT NULL,
  `cnpj` varchar(255) DEFAULT NULL,
  `email_contato` varchar(255) DEFAULT NULL,
  `telefone` varchar(255) DEFAULT NULL,
  `endereco_id` bigint DEFAULT NULL,
  `setor` varchar(255) DEFAULT NULL,
  `porte` varchar(255) DEFAULT NULL,
  `descricao` text,
  `ativa` tinyint(1) DEFAULT NULL,
  `verificada` tinyint(1) DEFAULT NULL COMMENT 'Validação da Prefeitura',
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  `usuario_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `cnpj` (`cnpj`),
  KEY `endereco_id` (`endereco_id`),
  KEY `fk_empresas_usuario` (`usuario_id`),
  CONSTRAINT `EMPRESAS_ibfk_1` FOREIGN KEY (`endereco_id`) REFERENCES `ENDERECOS` (`id`),
  CONSTRAINT `fk_empresas_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMPRESAS_2`
--

DROP TABLE IF EXISTS `EMPRESAS_2`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `EMPRESAS_2` (
  `id` bigint DEFAULT NULL,
  `razao_social` varchar(255) DEFAULT NULL,
  `nome_fantasia` varchar(255) DEFAULT NULL,
  `cnpj` varchar(255) DEFAULT NULL,
  `email_contato` varchar(255) DEFAULT NULL,
  `telefone` varchar(255) DEFAULT NULL,
  `endereco_id` bigint DEFAULT NULL,
  `setor` varchar(255) DEFAULT NULL,
  `porte` varchar(255) DEFAULT NULL,
  `descricao` text,
  `ativa` tinyint DEFAULT NULL,
  `verificada` tinyint DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  `usuario_id` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ENDERECOS`
--

DROP TABLE IF EXISTS `ENDERECOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ENDERECOS` (
  `id` bigint NOT NULL,
  `cep` varchar(255) DEFAULT NULL,
  `tipo_logradouro` varchar(255) DEFAULT NULL,
  `logradouro` varchar(255) DEFAULT NULL,
  `numero` varchar(255) DEFAULT NULL,
  `complemento` varchar(255) DEFAULT NULL,
  `bairro` varchar(255) DEFAULT NULL,
  `cidade` varchar(255) DEFAULT NULL,
  `uf` varchar(255) DEFAULT NULL,
  `pais` varchar(255) DEFAULT NULL,
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ETAPAS_PROCESSO_SELETIVO`
--

DROP TABLE IF EXISTS `ETAPAS_PROCESSO_SELETIVO`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ETAPAS_PROCESSO_SELETIVO` (
  `id` bigint NOT NULL,
  `vaga_id` bigint DEFAULT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `ordem` int DEFAULT NULL,
  `obrigatoria` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `vaga_id` (`vaga_id`),
  CONSTRAINT `ETAPAS_PROCESSO_SELETIVO_ibfk_1` FOREIGN KEY (`vaga_id`) REFERENCES `VAGAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `FAVORITOS_VAGAS`
--

DROP TABLE IF EXISTS `FAVORITOS_VAGAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `FAVORITOS_VAGAS` (
  `id` bigint NOT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `vaga_id` bigint DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `candidato_id` (`candidato_id`),
  KEY `vaga_id` (`vaga_id`),
  CONSTRAINT `FAVORITOS_VAGAS_ibfk_1` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`),
  CONSTRAINT `FAVORITOS_VAGAS_ibfk_2` FOREIGN KEY (`vaga_id`) REFERENCES `VAGAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `IDIOMAS`
--

DROP TABLE IF EXISTS `IDIOMAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `IDIOMAS` (
  `id` bigint NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `codigo` varchar(255) DEFAULT NULL,
  `ordem_destaque` tinyint DEFAULT '99',
  `ativo` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `IMPORTACOES_CURRICULO`
--

DROP TABLE IF EXISTS `IMPORTACOES_CURRICULO`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `IMPORTACOES_CURRICULO` (
  `id` bigint NOT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `anexo_id` bigint DEFAULT NULL COMMENT 'Link para o arquivo original (Word/PDF) upado na tabela ANEXOS',
  `status` varchar(255) DEFAULT NULL COMMENT 'Ex: PENDENTE, PROCESSANDO, CONCLUIDO, ERRO',
  `dados_extraidos_json` text COMMENT 'Dados brutos extraídos (NLP/IA) aguardando revisão do usuário',
  `log_erro` text,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `candidato_id` (`candidato_id`),
  KEY `anexo_id` (`anexo_id`),
  CONSTRAINT `IMPORTACOES_CURRICULO_ibfk_1` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`),
  CONSTRAINT `IMPORTACOES_CURRICULO_ibfk_2` FOREIGN KEY (`anexo_id`) REFERENCES `ANEXOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `INSTITUICOES_CURSOS_TECNICOS_OFERTADOS`
--

DROP TABLE IF EXISTS `INSTITUICOES_CURSOS_TECNICOS_OFERTADOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `INSTITUICOES_CURSOS_TECNICOS_OFERTADOS` (
  `id` bigint NOT NULL COMMENT 'ID Snowflake único do vínculo de oferta (64-bit)',
  `instituicao_tecnica_id` bigint NOT NULL COMMENT 'FK da instituição de ensino técnico',
  `curso_tecnico_id` bigint NOT NULL COMMENT 'FK do curso técnico ofertado',
  `criado_em` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_inst_curso_tecnico` (`instituicao_tecnica_id`,`curso_tecnico_id`),
  KEY `idx_oferta_curso_tecnico` (`curso_tecnico_id`),
  CONSTRAINT `fk_oferta_curso_tecnico` FOREIGN KEY (`curso_tecnico_id`) REFERENCES `CURSOS_TECNICOS` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_oferta_inst_tecnica` FOREIGN KEY (`instituicao_tecnica_id`) REFERENCES `INSTITUICOES_ENSINO_TECNICO` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `INSTITUICOES_ENSINO`
--

DROP TABLE IF EXISTS `INSTITUICOES_ENSINO`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `INSTITUICOES_ENSINO` (
  `id` bigint NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `sigla` varchar(255) DEFAULT NULL,
  `tipo` varchar(255) DEFAULT NULL,
  `cidade` varchar(255) DEFAULT NULL,
  `uf` varchar(255) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  `id_ies` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_instituicoes_uf_nome` (`uf`,`nome`),
  KEY `idx_instituicoes_id_ies` (`id_ies`),
  FULLTEXT KEY `idx_ft_ies_nome_sigla` (`nome`,`sigla`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `INSTITUICOES_ENSINO_TECNICO`
--

DROP TABLE IF EXISTS `INSTITUICOES_ENSINO_TECNICO`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `INSTITUICOES_ENSINO_TECNICO` (
  `id` bigint NOT NULL COMMENT 'ID Snowflake único da instituição técnica (64-bit)',
  `nome_instituicao` varchar(255) NOT NULL COMMENT 'Nome da instituição de ensino técnico',
  `dependencia_adm` varchar(50) DEFAULT NULL COMMENT 'Dependência administrativa (Pública ou Privada)',
  `endereco` text COMMENT 'Endereço completo da unidade',
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
  KEY `idx_inst_tecnicas_nome` (`nome_instituicao`),
  KEY `idx_inst_tecnicas_dep_adm` (`dependencia_adm`),
  KEY `idx_inst_tec_uf` (`uf`),
  KEY `idx_inst_tec_uf_municipio` (`uf`,`municipio`),
  KEY `idx_inst_tec_uf_nome` (`uf`,`nome_instituicao`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `INTERMEDIACOES`
--

DROP TABLE IF EXISTS `INTERMEDIACOES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `INTERMEDIACOES` (
  `id` bigint NOT NULL,
  `candidatura_id` bigint DEFAULT NULL,
  `servidor_prefeitura_id` bigint DEFAULT NULL,
  `orgao_id` bigint DEFAULT NULL,
  `status_intermediacao` varchar(255) DEFAULT NULL,
  `canal_intermediacao` varchar(255) DEFAULT NULL,
  `observacoes_gestor` text,
  `data_intermediacao` date DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `candidatura_id` (`candidatura_id`),
  KEY `servidor_prefeitura_id` (`servidor_prefeitura_id`),
  KEY `orgao_id` (`orgao_id`),
  CONSTRAINT `INTERMEDIACOES_ibfk_1` FOREIGN KEY (`candidatura_id`) REFERENCES `CANDIDATURAS` (`id`),
  CONSTRAINT `INTERMEDIACOES_ibfk_2` FOREIGN KEY (`servidor_prefeitura_id`) REFERENCES `SERVIDORES_PREFEITURA` (`id`),
  CONSTRAINT `INTERMEDIACOES_ibfk_3` FOREIGN KEY (`orgao_id`) REFERENCES `PREFEITURA_ORGAOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `MANTENEDORAS`
--

DROP TABLE IF EXISTS `MANTENEDORAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MANTENEDORAS` (
  `id` bigint NOT NULL,
  `nome` varchar(255) DEFAULT NULL COMMENT 'Ex: Prefeitura de Esteio, Senac, Governo Estadual',
  `tipo` varchar(255) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `MATCHINGS`
--

DROP TABLE IF EXISTS `MATCHINGS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MATCHINGS` (
  `id` bigint NOT NULL,
  `candidato_id` bigint DEFAULT NULL,
  `vaga_id` bigint DEFAULT NULL,
  `score_final` decimal(5,2) DEFAULT NULL,
  `metodo_score` varchar(255) DEFAULT NULL,
  `justificativa` text,
  `processado_em` datetime DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `candidato_id` (`candidato_id`),
  KEY `vaga_id` (`vaga_id`),
  CONSTRAINT `MATCHINGS_ibfk_1` FOREIGN KEY (`candidato_id`) REFERENCES `CANDIDATOS` (`id`),
  CONSTRAINT `MATCHINGS_ibfk_2` FOREIGN KEY (`vaga_id`) REFERENCES `VAGAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `MENSAGEM_LEITURAS`
--

DROP TABLE IF EXISTS `MENSAGEM_LEITURAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MENSAGEM_LEITURAS` (
  `id` bigint NOT NULL,
  `mensagem_id` bigint DEFAULT NULL,
  `usuario_id` bigint DEFAULT NULL,
  `lida_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `mensagem_id` (`mensagem_id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `MENSAGEM_LEITURAS_ibfk_1` FOREIGN KEY (`mensagem_id`) REFERENCES `MENSAGENS` (`id`),
  CONSTRAINT `MENSAGEM_LEITURAS_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `MENSAGENS`
--

DROP TABLE IF EXISTS `MENSAGENS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MENSAGENS` (
  `id` bigint NOT NULL,
  `conversa_id` bigint DEFAULT NULL,
  `remetente_usuario_id` bigint DEFAULT NULL,
  `conteudo` text,
  `tipo_mensagem` varchar(255) DEFAULT NULL,
  `moderada` tinyint(1) DEFAULT NULL,
  `removida` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `conversa_id` (`conversa_id`),
  KEY `remetente_usuario_id` (`remetente_usuario_id`),
  CONSTRAINT `MENSAGENS_ibfk_1` FOREIGN KEY (`conversa_id`) REFERENCES `MENSAGENS_CONVERSAS` (`id`),
  CONSTRAINT `MENSAGENS_ibfk_2` FOREIGN KEY (`remetente_usuario_id`) REFERENCES `USUARIOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `MENSAGENS_CONVERSAS`
--

DROP TABLE IF EXISTS `MENSAGENS_CONVERSAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MENSAGENS_CONVERSAS` (
  `id` bigint NOT NULL,
  `tipo_conversa` varchar(255) DEFAULT NULL,
  `vaga_id` bigint DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `vaga_id` (`vaga_id`),
  CONSTRAINT `MENSAGENS_CONVERSAS_ibfk_1` FOREIGN KEY (`vaga_id`) REFERENCES `VAGAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `MENSAGENS_PARTICIPANTES`
--

DROP TABLE IF EXISTS `MENSAGENS_PARTICIPANTES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MENSAGENS_PARTICIPANTES` (
  `id` bigint NOT NULL,
  `conversa_id` bigint DEFAULT NULL,
  `usuario_id` bigint DEFAULT NULL,
  `papel_na_conversa` varchar(255) DEFAULT NULL,
  `entrou_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `conversa_id` (`conversa_id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `MENSAGENS_PARTICIPANTES_ibfk_1` FOREIGN KEY (`conversa_id`) REFERENCES `MENSAGENS_CONVERSAS` (`id`),
  CONSTRAINT `MENSAGENS_PARTICIPANTES_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `NOTIFICACOES`
--

DROP TABLE IF EXISTS `NOTIFICACOES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `NOTIFICACOES` (
  `id` bigint NOT NULL,
  `usuario_id` bigint DEFAULT NULL,
  `tipo` varchar(255) DEFAULT NULL,
  `titulo` varchar(255) DEFAULT NULL,
  `conteudo` text,
  `canal` varchar(255) DEFAULT NULL,
  `lida` tinyint(1) DEFAULT NULL,
  `enviada_em` datetime DEFAULT NULL,
  `lida_em` datetime DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `NOTIFICACOES_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `OCUPACOES`
--

DROP TABLE IF EXISTS `OCUPACOES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `OCUPACOES` (
  `id` bigint NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `cbo_codigo` varchar(255) DEFAULT NULL,
  `area_profissional_id` bigint DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `area_profissional_id` (`area_profissional_id`),
  CONSTRAINT `OCUPACOES_ibfk_1` FOREIGN KEY (`area_profissional_id`) REFERENCES `AREAS_PROFISSIONAIS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `PAPEIS`
--

DROP TABLE IF EXISTS `PAPEIS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PAPEIS` (
  `id` bigint NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `descricao` varchar(255) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nome` (`nome`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `PREFEITURA_ORGAOS`
--

DROP TABLE IF EXISTS `PREFEITURA_ORGAOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PREFEITURA_ORGAOS` (
  `id` bigint NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `sigla` varchar(255) DEFAULT NULL,
  `descricao` varchar(255) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RECRUTADORES`
--

DROP TABLE IF EXISTS `RECRUTADORES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RECRUTADORES` (
  `id` bigint NOT NULL,
  `usuario_id` bigint DEFAULT NULL,
  `empresa_id` bigint DEFAULT NULL,
  `cargo` varchar(255) DEFAULT NULL,
  `principal` tinyint(1) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario_id` (`usuario_id`),
  KEY `empresa_id` (`empresa_id`),
  CONSTRAINT `RECRUTADORES_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`),
  CONSTRAINT `RECRUTADORES_ibfk_2` FOREIGN KEY (`empresa_id`) REFERENCES `EMPRESAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SERVIDORES_PREFEITURA`
--

DROP TABLE IF EXISTS `SERVIDORES_PREFEITURA`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SERVIDORES_PREFEITURA` (
  `id` bigint NOT NULL,
  `usuario_id` bigint DEFAULT NULL,
  `orgao_id` bigint DEFAULT NULL,
  `cargo` varchar(255) DEFAULT NULL,
  `matricula` varchar(255) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario_id` (`usuario_id`),
  UNIQUE KEY `matricula` (`matricula`),
  KEY `orgao_id` (`orgao_id`),
  CONSTRAINT `SERVIDORES_PREFEITURA_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`),
  CONSTRAINT `SERVIDORES_PREFEITURA_ibfk_2` FOREIGN KEY (`orgao_id`) REFERENCES `PREFEITURA_ORGAOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SSO_IDENTIDADES`
--

DROP TABLE IF EXISTS `SSO_IDENTIDADES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SSO_IDENTIDADES` (
  `id` bigint NOT NULL,
  `usuario_id` bigint DEFAULT NULL,
  `provider` varchar(255) DEFAULT NULL COMMENT 'Ex: GOOGLE, GOV_BR',
  `provider_user_id` varchar(255) DEFAULT NULL,
  `username` varchar(255) DEFAULT NULL,
  `principal` tinyint(1) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `SSO_IDENTIDADES_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SSO_RESET_SENHAS`
--

DROP TABLE IF EXISTS `SSO_RESET_SENHAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SSO_RESET_SENHAS` (
  `id` bigint NOT NULL,
  `usuario_id` bigint DEFAULT NULL,
  `token_hash` varchar(255) DEFAULT NULL,
  `expira_em` datetime DEFAULT NULL,
  `usado_em` datetime DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `SSO_RESET_SENHAS_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SSO_SESSOES`
--

DROP TABLE IF EXISTS `SSO_SESSOES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SSO_SESSOES` (
  `id` bigint NOT NULL,
  `usuario_id` bigint DEFAULT NULL,
  `access_token_hash` varchar(255) DEFAULT NULL,
  `refresh_token_hash` varchar(255) DEFAULT NULL,
  `ip` varchar(255) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  `expira_em` datetime DEFAULT NULL,
  `revogado_em` datetime DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `SSO_SESSOES_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TEMPLATES_CURRICULOS`
--

DROP TABLE IF EXISTS `TEMPLATES_CURRICULOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `TEMPLATES_CURRICULOS` (
  `id` bigint NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `descricao` varchar(255) DEFAULT NULL,
  `caminho_arquivo_latex` varchar(255) DEFAULT NULL COMMENT 'Caminho no S3/Storage para o arquivo .tex base',
  `caminho_preview_img` varchar(255) DEFAULT NULL COMMENT 'Imagem de thumbnail para o usuário escolher na UI',
  `ativo` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `USUARIOS`
--

DROP TABLE IF EXISTS `USUARIOS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USUARIOS` (
  `id` bigint NOT NULL COMMENT 'Chave primária global',
  `nome` varchar(255) DEFAULT NULL,
  `nome_social` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `email_secundario` varchar(255) DEFAULT NULL,
  `telefone_celular` varchar(255) DEFAULT NULL,
  `telefone_fixo` varchar(255) DEFAULT NULL,
  `cpf` varchar(255) DEFAULT NULL COMMENT 'Chave primária de negócio',
  `rg` varchar(255) DEFAULT NULL,
  `data_nascimento` date DEFAULT NULL,
  `genero` varchar(255) DEFAULT NULL,
  `estado_civil` varchar(255) DEFAULT NULL,
  `estrangeiro` tinyint(1) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT NULL,
  `email_verificado` tinyint(1) DEFAULT NULL,
  `aceitou_termos` tinyint(1) DEFAULT NULL,
  `ultimo_login_em` datetime DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `cpf` (`cpf`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `USUARIO_CREDENCIAIS`
--

DROP TABLE IF EXISTS `USUARIO_CREDENCIAIS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USUARIO_CREDENCIAIS` (
  `id` bigint NOT NULL,
  `usuario_id` bigint DEFAULT NULL,
  `senha_hash` varchar(255) DEFAULT NULL COMMENT 'Isolamento de criptografia',
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `USUARIO_CREDENCIAIS_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `USUARIO_PAPEIS`
--

DROP TABLE IF EXISTS `USUARIO_PAPEIS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `USUARIO_PAPEIS` (
  `id` bigint NOT NULL,
  `usuario_id` bigint DEFAULT NULL,
  `papel_id` bigint DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  KEY `papel_id` (`papel_id`),
  CONSTRAINT `USUARIO_PAPEIS_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `USUARIOS` (`id`),
  CONSTRAINT `USUARIO_PAPEIS_ibfk_2` FOREIGN KEY (`papel_id`) REFERENCES `PAPEIS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `VAGAS`
--

DROP TABLE IF EXISTS `VAGAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `VAGAS` (
  `id` bigint NOT NULL,
  `empresa_id` bigint DEFAULT NULL,
  `recrutador_id` bigint DEFAULT NULL,
  `ocupacao_id` bigint DEFAULT NULL,
  `endereco_id` bigint DEFAULT NULL,
  `titulo` varchar(255) DEFAULT NULL,
  `descricao` text,
  `requisitos` text,
  `beneficios` text,
  `tipo_contrato` varchar(255) DEFAULT NULL,
  `tipo_jornada` varchar(255) DEFAULT NULL,
  `modalidade_trabalho` varchar(255) DEFAULT NULL,
  `salario_min` decimal(12,2) DEFAULT NULL,
  `salario_max` decimal(12,2) DEFAULT NULL,
  `quantidade_posicoes` int DEFAULT NULL,
  `pcd_aceita` tinyint(1) DEFAULT NULL,
  `ativa` tinyint(1) DEFAULT NULL,
  `destaque` tinyint(1) DEFAULT NULL,
  `publicada_em` datetime DEFAULT NULL,
  `expira_em` datetime DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `empresa_id` (`empresa_id`),
  KEY `recrutador_id` (`recrutador_id`),
  KEY `ocupacao_id` (`ocupacao_id`),
  KEY `endereco_id` (`endereco_id`),
  KEY `idx_vagas_busca_ativa` (`ativa`,`destaque`,`publicada_em`),
  CONSTRAINT `VAGAS_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `EMPRESAS` (`id`),
  CONSTRAINT `VAGAS_ibfk_2` FOREIGN KEY (`recrutador_id`) REFERENCES `RECRUTADORES` (`id`),
  CONSTRAINT `VAGAS_ibfk_3` FOREIGN KEY (`ocupacao_id`) REFERENCES `OCUPACOES` (`id`),
  CONSTRAINT `VAGAS_ibfk_4` FOREIGN KEY (`endereco_id`) REFERENCES `ENDERECOS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `VAGA_COMPETENCIAS_DIGITAIS`
--

DROP TABLE IF EXISTS `VAGA_COMPETENCIAS_DIGITAIS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `VAGA_COMPETENCIAS_DIGITAIS` (
  `id` bigint NOT NULL,
  `vaga_id` bigint DEFAULT NULL,
  `competencia_id` bigint DEFAULT NULL,
  `nivel_minimo` varchar(255) DEFAULT NULL,
  `obrigatorio` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `vaga_id` (`vaga_id`),
  KEY `competencia_id` (`competencia_id`),
  CONSTRAINT `VAGA_COMPETENCIAS_DIGITAIS_ibfk_1` FOREIGN KEY (`vaga_id`) REFERENCES `VAGAS` (`id`),
  CONSTRAINT `VAGA_COMPETENCIAS_DIGITAIS_ibfk_2` FOREIGN KEY (`competencia_id`) REFERENCES `COMPETENCIAS_DIGITAIS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `VAGA_HABILIDADES`
--

DROP TABLE IF EXISTS `VAGA_HABILIDADES`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `VAGA_HABILIDADES` (
  `id` bigint NOT NULL,
  `vaga_id` bigint DEFAULT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `obrigatoriedade` varchar(255) DEFAULT NULL,
  `nivel` varchar(255) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `vaga_id` (`vaga_id`),
  CONSTRAINT `VAGA_HABILIDADES_ibfk_1` FOREIGN KEY (`vaga_id`) REFERENCES `VAGAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `VAGA_IDIOMAS`
--

DROP TABLE IF EXISTS `VAGA_IDIOMAS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `VAGA_IDIOMAS` (
  `id` bigint NOT NULL,
  `vaga_id` bigint DEFAULT NULL,
  `idioma_id` bigint DEFAULT NULL,
  `nivel_minimo` varchar(255) DEFAULT NULL,
  `obrigatorio` tinyint(1) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `vaga_id` (`vaga_id`),
  KEY `idioma_id` (`idioma_id`),
  CONSTRAINT `VAGA_IDIOMAS_ibfk_1` FOREIGN KEY (`vaga_id`) REFERENCES `VAGAS` (`id`),
  CONSTRAINT `VAGA_IDIOMAS_ibfk_2` FOREIGN KEY (`idioma_id`) REFERENCES `IDIOMAS` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed
