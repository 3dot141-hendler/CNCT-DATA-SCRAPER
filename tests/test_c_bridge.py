"""
Testes unitarios e de integracao para o modulo C / Python Bridge de agregacao.
"""

import os
import csv
import json
import pytest
from pathlib import Path
from src.c_aggregator.bridge import run_c_aggregation
from src.utils.snowflake import SnowflakeGenerator


def test_c_bridge_aggregation(tmp_path):
    gen = SnowflakeGenerator()

    # IDs de teste de 64-bits
    inst1_id = gen.generate_id()
    inst2_id = gen.generate_id()
    
    course1_id = gen.generate_id()
    course2_id = gen.generate_id()

    # 1. Arquivo temporario de instituicoes
    inst_csv = tmp_path / "test_institutions.csv"
    with open(inst_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["snowflake_id", "nome_instituicao", "dependencia_adm", "endereco", "telefone", "email", "homepage"])
        writer.writerow([inst1_id, "Instituto Federal de SP", "Pública", "Rua A, 123", "(11) 1234-5678", "ifsp@edu.br", "www.ifsp.edu.br"])
        writer.writerow([inst2_id, "Colegio Tecnico Privado", "Privada", "Av B, 456", "(11) 9876-5432", "contato@privado.com", "www.privado.com"])

    # 2. Arquivo temporario de relacoes
    rel_csv = tmp_path / "test_relations.csv"
    with open(rel_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["inst_snowflake_id", "course_snowflake_id"])
        writer.writerow([inst1_id, course1_id])
        writer.writerow([inst1_id, course2_id])
        writer.writerow([inst2_id, course1_id])

    # 3. Executar agregacao
    out_csv = tmp_path / "test_output_institutions.csv"
    success = run_c_aggregation(str(inst_csv), str(rel_csv), str(out_csv))
    
    assert success is True
    assert out_csv.exists()

    # 4. Validar resultado
    with open(out_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f, delimiter=";"))
        assert len(reader) == 2

        inst1_data = next(r for r in reader if int(r["snowflake_id"]) == inst1_id)
        cursos1 = json.loads(inst1_data["cursos_ofertados_ids"])
        assert len(cursos1) == 2
        assert course1_id in cursos1
        assert course2_id in cursos1

        inst2_data = next(r for r in reader if int(r["snowflake_id"]) == inst2_id)
        cursos2 = json.loads(inst2_data["cursos_ofertados_ids"])
        assert len(cursos2) == 1
        assert course1_id in cursos2
