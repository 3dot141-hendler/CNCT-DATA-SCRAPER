"""
Rotas FastAPI para download e visualizacao dos arquivos CSV de Cursos e Instituicoes.
"""

import os
import csv
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/data", tags=["Data"])
OUTPUT_DIR = Path("output")

@router.get("/cursos")
def get_cursos_sample(limit: int = 10):
    """
    Retorna uma amostragem dos cursos raspados.
    """
    csv_file = OUTPUT_DIR / "csv_cursos.csv"
    if not csv_file.exists():
        return {"total": 0, "cursos": []}

    rows = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for i, row in enumerate(reader):
            if i >= limit:
                break
            rows.append(row)

    return {"total": len(rows), "cursos": rows}

@router.get("/instituicoes")
def get_instituicoes_sample(limit: int = 10):
    """
    Retorna uma amostragem das instituicoes agregadas.
    """
    csv_file = OUTPUT_DIR / "csv_instituicoes.csv"
    if not csv_file.exists():
        return {"total": 0, "instituicoes": []}

    rows = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for i, row in enumerate(reader):
            if i >= limit:
                break
            rows.append(row)

    return {"total": len(rows), "instituicoes": rows}

@router.get("/download/{filename}")
def download_csv(filename: str):
    """
    Permite o download direto dos arquivos CSV gerados (padrão ou com timestamp).
    """
    if not filename.endswith(".csv") or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")

    file_path = OUTPUT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"O arquivo {filename} não foi encontrado.")

    return FileResponse(path=file_path, filename=filename, media_type="text/csv")
