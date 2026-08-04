"""
Módulo de ponte entre Python e o compilado em C para agregação de Snowflake IDs.
"""

import os
import sys
import csv
import json
import subprocess
from pathlib import Path

C_DIR = Path(__file__).parent
C_SOURCE = C_DIR / "aggregator.c"
C_HEADER = C_DIR / "aggregator.h"
C_EXECUTABLE = C_DIR / ("aggregator.exe" if sys.platform == "win32" else "aggregator")


def compile_c_aggregator() -> bool:
    """
    Compila o executável C utilizando gcc ou clang se disponível.
    """
    if C_EXECUTABLE.exists():
        return True

    print("[C BRIDGE] Compilando módulo C de alta performance...")
    compilers = ["gcc", "clang"]
    
    for compiler in compilers:
        try:
            cmd = [compiler, "-O3", str(C_SOURCE), "-o", str(C_EXECUTABLE)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0 and C_EXECUTABLE.exists():
                print(f"[C BRIDGE] Sucesso ao compilar com {compiler}: {C_EXECUTABLE}")
                return True
        except Exception:
            continue

    print("[C BRIDGE] Compilador C nao detectado no PATH do sistema.")
    return False


def run_c_aggregation(institutions_csv: str, relations_csv: str, output_csv: str) -> bool:
    """
    Executa a agregação de cursos por instituição.
    Utiliza o binário C nativo em uint64_t se compilado com sucesso,
    ou fallback otimizado em Python garantindo mesmo formato de saída.
    """
    if compile_c_aggregator() and C_EXECUTABLE.exists():
        try:
            cmd = [str(C_EXECUTABLE), str(institutions_csv), str(relations_csv), str(output_csv)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                print(f"[C BRIDGE] Agregação concluída via binário C nativo (uint64_t).")
                return True
        except Exception as e:
            print(f"[C BRIDGE] Erro ao executar binário C: {e}")

    # Fallback em Python mantendo tipagem uint64_t estrita
    print("[C BRIDGE] Executando agregação via motor Python de alta precisao...")
    return _python_fallback_aggregation(institutions_csv, relations_csv, output_csv)


def _python_fallback_aggregation(institutions_csv: str, relations_csv: str, output_csv: str) -> bool:
    """
    Fallback em Python que espelha exatamente o comportamento de 64-bits do C.
    """
    try:
        institutions = {}
        
        # 1. Carregar instituicoes
        with open(institutions_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                sf_id = int(row["snowflake_id"])
                institutions[sf_id] = {
                    "snowflake_id": sf_id,
                    "nome_instituicao": row.get("nome_instituicao", ""),
                    "dependencia_adm": row.get("dependencia_adm", ""),
                    "endereco": row.get("endereco", ""),
                    "telefone": row.get("telefone", ""),
                    "email": row.get("email", ""),
                    "homepage": row.get("homepage", ""),
                    "cursos": []
                }

        # 2. Carregar relacoes de Snowflake IDs (uint64_t -> uint64_t)
        if os.path.exists(relations_csv):
            with open(relations_csv, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    inst_id = int(row["inst_snowflake_id"])
                    course_id = int(row["course_snowflake_id"])
                    if inst_id in institutions:
                        if course_id not in institutions[inst_id]["cursos"]:
                            institutions[inst_id]["cursos"].append(course_id)

        # 3. Escrever CSV de Saida final
        fieldnames = [
            "snowflake_id", "nome_instituicao", "dependencia_adm",
            "endereco", "telefone", "email", "homepage", "cursos_ofertados_ids"
        ]

        with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(fieldnames)

            for inst_id, data in institutions.items():
                cursos_json = json.dumps(data["cursos"])
                writer.writerow([
                    data["snowflake_id"],
                    data["nome_instituicao"],
                    data["dependencia_adm"],
                    data["endereco"],
                    data["telefone"],
                    data["email"],
                    data["homepage"],
                    cursos_json
                ])

        print(f"[C BRIDGE] Arquivo agregado gerado com sucesso: {output_csv}")
        return True
    except Exception as e:
        print(f"[C BRIDGE ERRO]: {e}")
        return False
