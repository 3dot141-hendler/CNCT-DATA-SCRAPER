"""
Testes unitarios para o parser de dados de cursos e instituicoes.
"""

import pytest
from src.scraper.parser import parse_course_record, parse_institution_record, clean_text


def test_clean_text():
    assert clean_text(None) == "não informado"
    assert clean_text("") == "não informado"
    assert clean_text("  Engenharia  ") == "Engenharia"


def test_parse_course_record():
    raw_course = {
        "nome": "Técnico em Informática",
        "cargaHoraria": "1200 horas",
        "preRequisito": "Ensino Médio",
        "perfilProfissional": "Desenvolve software",
        "campoAtuacao": "Empresas de TI",
        "ocupacoesCbo": "3171-10",
        "infraestruturaMinima": "Laboratório de informatica",
        "areasTecnologicas": [{"nome": "Informação e Comunicação"}]
    }

    parsed = parse_course_record(raw_course, original_id=10, snowflake_id=1704067200000)

    assert parsed["id_original"] == 10
    assert parsed["snowflake_id"] == 1704067200000
    assert parsed["nome_curso"] == "Técnico em Informática"
    assert parsed["eixo_tecnologico"] == "Informação e Comunicação"
    assert parsed["carga_horaria"] == "1200 horas"


def test_parse_institution_record():
    raw_inst = {
        "nome": "Instituto Federal de SP",
        "tipo": "Pública",
        "endereco": "Rua A, 123",
        "telefone": "(11) 1234-5678",
        "email": "contato@ifsp.edu.br",
        "site": "www.ifsp.edu.br",
        "uf": "SP",
        "cidade": "São Paulo"
    }

    parsed = parse_institution_record(raw_inst, snowflake_id=1704067200001)

    assert parsed["snowflake_id"] == 1704067200001
    assert parsed["nome_instituicao"] == "Instituto Federal de SP"
    assert parsed["dependencia_adm"] == "Pública"
    assert parsed["email"] == "contato@ifsp.edu.br"
