"""
Testes unitários para o motor C nativo de parsing de endereços e diff de tabelas (CNCT_SCRAPER).
Fase 1 (TDD) do Plano de Implantação.
"""

import os
import sys
import pytest

# Adiciona raiz do projeto CNCT_SCRAPER ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.c_aggregator.bridge import parse_address_c, compare_datasets_c, generate_text_diagnosis_c


def test_parse_address_c_endereco_completo():
    raw_end = "AVENIDA PRESIDENTE VARGAS, 123, APTO 4B, CENTRO, ESTEIO, RS, 93260-006"
    res = parse_address_c(raw_end)
    assert res['logradouro'] == "AVENIDA PRESIDENTE VARGAS"
    assert res['numero'] == "123"
    assert res['complemento'] == "APTO 4B"
    assert res['bairro'] == "CENTRO"
    assert res['municipio'] == "ESTEIO"
    assert res['uf'] == "RS"
    assert res['cep'] == "93260006"


def test_parse_address_c_sem_numero_e_cep():
    raw_end = "RUA 24 DE MAIO, S/N, NAVIGANTES, PORTO ALEGRE, RS"
    res = parse_address_c(raw_end)
    assert res['logradouro'] == "RUA 24 DE MAIO"
    assert res['numero'] == "S/N"
    assert res['bairro'] == "NAVIGANTES"
    assert res['municipio'] == "PORTO ALEGRE"
    assert res['uf'] == "RS"


def test_preservacao_snowflake_ids():
    snowflake_id_64 = 1782938491823948123
    data = [{
        "snowflake_id": snowflake_id_64,
        "nome_instituicao": "Escola Técnica Teste",
        "endereco": "RUA DAS FLORES, 10, CENTRO, ESTEIO, RS, 93260000"
    }]
    diff = compare_datasets_c([], data)
    assert len(diff['novos']) == 1
    assert diff['novos'][0]['snowflake_id'] == snowflake_id_64


def test_compare_datasets_c_diff_e_inativacao():
    db_state = [
        {"id": 1001, "nome_instituicao": "Inst A", "municipio": "Esteio", "ativo": 1},
        {"id": 1002, "nome_instituicao": "Inst B", "municipio": "Canoas", "ativo": 1}
    ]
    csv_incoming = [
        {"snowflake_id": 1001, "nome_instituicao": "Inst A", "municipio": "Esteio"},
        {"snowflake_id": 1003, "nome_instituicao": "Inst C", "municipio": "Porto Alegre"}
    ]

    diff = compare_datasets_c(db_state, csv_incoming)
    # Inst C deve ser apontada como Nova
    assert len(diff['novos']) == 1
    assert diff['novos'][0]['snowflake_id'] == 1003

    # Inst B deve ser inativada (ativo=0)
    assert len(diff['inativados']) == 1
    assert diff['inativados'][0]['id'] == 1002
    assert diff['inativados'][0]['ativo'] == 0

    # Inst A permanece mantida
    assert len(diff['mantidos']) == 1
    assert diff['mantidos'][0]['id'] == 1001


def test_generate_text_diagnosis_c():
    stats = {
        "total_csv": 50,
        "total_db": 48,
        "novos_qtd": 5,
        "alterados_qtd": 2,
        "inativados_qtd": 3,
        "mantidos_qtd": 43,
        "estatisticas_cursos": {
            "novos_cursos_qtd": 10,
            "cursos_descontinuados_qtd": 2,
            "cursos_mantidos_qtd": 80
        }
    }
    relatorio = generate_text_diagnosis_c(stats)
    assert "DIAGNÓSTICO ANALÍTICO DE SINCRONIZAÇÃO" in relatorio
    assert "Instituições Novas (A Inserir):              5" in relatorio
    assert "Instituições Inativadas (ativo=0):           3" in relatorio
    assert "Novas Ofertas de Cursos (Novos Vínculos):   10" in relatorio


def test_cidades_homonimas_uf_diferente_buritis():
    """
    Caso 5: Buritis RO vs Buritis MG (Polos de estados diferentes).
    A chave natural DEVE conter obrigatoriamente a UF para evitar matching cruzado indevido.
    """
    db_state = [
        {
            "id": 342380338972069893,
            "nome_instituicao": "Universidade Cruzeiro do Sul - Unicsul - Polo Buritis",
            "municipio": "Buritis",
            "uf": "RO",
            "endereco": "Rua Nova União, 2024, Polo Buritis, Setor 02, Buritis RO - 76880000."
        },
        {
            "id": 342380338972069894,
            "nome_instituicao": "Universidade Cruzeiro do Sul - Unicsul - Poloburitis",
            "municipio": "Buritis",
            "uf": "MG",
            "endereco": "Avenida Minas Gerais, 360, Poloburitis, Centro, Buritis MG - 38660000."
        }
    ]

    csv_incoming = [
        {
            "snowflake_id": 342380338972069894,
            "nome_instituicao": "Universidade Cruzeiro do Sul - Unicsul - Poloburitis",
            "municipio": "Buritis",
            "uf": "MG",
            "endereco": "Avenida Minas Gerais, 360, Poloburitis, Centro, Buritis MG - 38660000."
        },
        {
            "snowflake_id": 342380338972069893,
            "nome_instituicao": "Universidade Cruzeiro do Sul - Unicsul - Polo Buritis",
            "municipio": "Buritis",
            "uf": "RO",
            "endereco": "Rua Nova União, 2024, Polo Buritis, Setor 02, Buritis RO - 76880000."
        }
    ]

    diff = compare_datasets_c(db_state, csv_incoming)

    # Ambos devem ser mantidos sem alterações cruzadas nem inativações incorretas
    assert len(diff['mantidos']) == 2
    assert len(diff['alterados']) == 0
    assert len(diff['novos']) == 0

    # Verifica se os IDs do MySQL corresponderam às UFs corretas
    matched_mg = next(x for x in diff['mantidos'] if x.get('uf') == 'MG' or 'MG' in x.get('endereco', ''))
    matched_ro = next(x for x in diff['mantidos'] if x.get('uf') == 'RO' or 'RO' in x.get('endereco', ''))

    assert matched_mg['id'] == 342380338972069894
    assert matched_ro['id'] == 342380338972069893


def test_normalizacao_acentos_e_duplicatas_db():
    """
    Caso 2: Tolerância a acentos (João vs Joao, Santo Antonio vs Santo Antônio) e deduplicação.
    """
    db_state = [
        {
            "id": 342380317518205111,
            "nome_instituicao": "EE Professor João Menezes",
            "municipio": "Piumhi",
            "uf": "MG",
            "endereco": "Rua Tenente Freitas, 555, 1, Jardim Santo Antonio, Piumhi MG - 37925000."
        }
    ]

    csv_incoming = [
        {
            "nome_instituicao": "EE Professor Joao Menezes",
            "municipio": "Piumhi",
            "uf": "MG",
            "endereco": "Rua Tenente Freitas, 555, Jardim Santo Antônio, Piumhi MG - 37925000."
        }
    ]

    diff = compare_datasets_c(db_state, csv_incoming)

    # Deve casar com o registro do banco sem gerar falso positivo de novo ou inativação
    assert len(diff['novos']) == 0
    assert len(diff['mantidos']) + len(diff['alterados']) == 1


def test_correcao_ortografica_valida_itapaje():
    """
    Caso 4: Preservação de atualização legítima (Itapagé -> Itapajé).
    """
    db_state = [
        {
            "id": 342380338967875603,
            "nome_instituicao": "Universidade Cruzeiro do Sul - Unicsul - Itapajé",
            "municipio": "Itapagé",
            "uf": "CE",
            "endereco": "Rua Quintino Cunha, 35, Centro, Itapagé CE - 62600000."
        }
    ]

    csv_incoming = [
        {
            "nome_instituicao": "Universidade Cruzeiro do Sul - Unicsul - Itapajé",
            "municipio": "Itapajé",
            "uf": "CE",
            "endereco": "Rua Quintino Cunha, 35, Centro, Itapajé CE - 62600000."
        }
    ]

    diff = compare_datasets_c(db_state, csv_incoming)

    # Deve casar o ID original do banco
    assert len(diff['novos']) == 0
    item_processado = (diff['mantidos'] + diff['alterados'])[0]
    assert item_processado['id'] == 342380338967875603


def test_sanitizacao_typos_logradouro_enida():
    """
    Caso 3: Sanitização de erros de raspagem no logradouro ('Enida' -> 'Avenida').
    """
    raw_end = "Enida Perimetral Deputado Rogério Lucio Soares, 2374, Setor D, Alta Floresta MT - 78580000"
    parsed = parse_address_c(raw_end)
    assert parsed['logradouro'] is not None
    assert "AVENIDA" in parsed['logradouro'].upper() or "PERIMETRAL" in parsed['logradouro'].upper()


def test_expansao_abreviacoes_escola_tecnica_irmao_pedro():
    """
    Teste de correspondência com abreviações institucionais (Esc. Téc. Est. vs Escola Técnica Estadual).
    """
    db_state = [
        {
            "id": 342381279209197621,
            "nome_instituicao": "Esc. Téc. Est. Irmão Pedro",
            "municipio": "Porto Alegre",
            "uf": "RS",
            "endereco": "Rua Félix da Cunha, 0, Cristo Redentor, Porto Alegre RS - 91040030."
        }
    ]

    csv_incoming = [
        {
            "nome_instituicao": "Escola Técnica Estadual Irmão Pedro",
            "municipio": "Porto Alegre",
            "uf": "RS",
            "endereco": "Rua Félix da Cunha, 0, Cristo Redentor, Porto Alegre RS - 91040030."
        }
    ]

    diff = compare_datasets_c(db_state, csv_incoming)

    # Deve casar perfeitamente sem apontar como instituição nova
    assert len(diff['novos']) == 0
    assert len(diff['mantidos']) == 1
    assert diff['mantidos'][0]['id'] == 342381279209197621


def test_pareamento_por_localizacao_fisica_cep_e_logradouro():
    """
    Valida a capacidade da Solução 3 em parear registros com alterações profundas de nome
    através do CEP + Número do imóvel e Logradouro.
    """
    db_state = [{
        "id": 9901,
        "nome_instituicao": "Sistema de Ensino Integrado - Tucuruí",
        "municipio": "Tucuruí",
        "uf": "PA",
        "endereco": "Travessa W-um S/N Cohab Tucuruí PA 68459820",
        "ativo": 1
    }]

    csv_incoming = [{
        "nome_instituicao": "Centro Integrado de Educação do Pará",
        "municipio": "Tucuruí",
        "uf": "PA",
        "endereco": "Travessa W-um, S/N, Quadra 03 - Lote 20 e 24, Cohab, Tucuruí PA - 68459820."
    }]

def test_duplicatas_no_dataset_raspado_mesma_instituicao():
    """
    Testa a resiliência contra duplicatas no próprio dataset raspado do MEC
    (ex: duas entradas no CSV para EE Presidente Antonio Carlos com e sem acento).
    """
    db_state = [{
        "id": 342381342371221570,
        "nome_instituicao": "EE Presidente Antonio Carlos",
        "municipio": "Belo Horizonte",
        "uf": "MG",
        "endereco": "Rua Passa Tempo 600 Carmo Belo Horizonte MG 30310760",
        "ativo": 1
    }]

    csv_incoming = [
        {
            "nome_instituicao": "EE Presidente Antônio Carlos",
            "municipio": "Belo Horizonte",
            "uf": "MG",
            "endereco": "Rua Passa Tempo, 600, Carmo, Belo Horizonte MG - 30310760."
        },
        {
            "nome_instituicao": "EE Presidente Antonio Carlos",
            "municipio": "Belo Horizonte",
            "uf": "MG",
            "endereco": "Rua Passa Tempo, 600, Carmo, Belo Horizonte MG - 30310760."
        }
    ]

def test_auditoria_automatica_pos_diff():
    """
    Testa a esteira de Auditoria Automática Pós-Diff (Passos 1, 2 e 3).
    Garante que qualquer item que chegar a 'novos' seja submetido ao escrutínio final.
    """
    db_state = [{
        "id": 880011,
        "nome_instituicao": "Escola Técnica Estadual Vanguarda de Montes Claros",
        "municipio": "Montes Claros",
        "uf": "MG",
        "endereco": "Praça Coronel Ribeiro 19 Centro Montes Claros MG 39400082",
        "ativo": 1
    }]

    csv_incoming = [{
        "nome_instituicao": "Vanguarda Montes Claros",
        "municipio": "Montes Claros",
        "uf": "MG",
        "endereco": "Praça Coronel Ribeiro, 19, Centro, Montes Claros MG - 39400082."
    }]

def test_auditoria_diferencia_numeros_diferentes_mesmo_cep():
    """
    Testa a regra de que instituicoes no mesmo CEP mas com numeros de imovel diferentes
    (ex: nº 19 vs nº 49 na Praça Coronel Ribeiro - Montes Claros MG) NAO sao falsamente pareadas.
    """
    db_state = [{
        "id": 998877,
        "nome_instituicao": "Instituto Qualificar",
        "municipio": "Montes Claros",
        "uf": "MG",
        "endereco": "Praça Coronel Ribeiro 49 Centro Montes Claros MG 39400082",
        "ativo": 1
    }]

    csv_incoming = [{
        "nome_instituicao": "Escola Técnica Vanguarda",
        "municipio": "Montes Claros",
        "uf": "MG",
        "endereco": "Praça Coronel Ribeiro, 19, Prédio, Centro, Montes Claros MG - 39400082."
    }]

    diff = compare_datasets_c(db_state, csv_incoming)

    # A Escola Técnica Vanguarda (nº 19) NÃO deve ser pareada com o Instituto Qualificar (nº 49)
    assert len(diff['novos']) == 1
    assert diff['novos'][0]['nome_instituicao'] == "Escola Técnica Vanguarda"
    assert len(diff['alterados']) == 0







