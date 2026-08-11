"""
Orquestrador principal do pipeline de raspagem do CNCT.
"""

import os
import csv
import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Any
from src.scraper.client import CNCTApiClient
from src.scraper.parser import parse_course_record, parse_institution_record
from src.utils.snowflake import SnowflakeGenerator
from src.c_aggregator.bridge import run_c_aggregation
from src.backend.websocket_manager import ws_manager

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

SRC_OUTPUT_DIR = Path(__file__).parent.parent / "output"
SRC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_CURSOS = OUTPUT_DIR / "csv_cursos.csv"
CSV_INSTITUICOES = OUTPUT_DIR / "csv_instituicoes.csv"
SRC_CSV_CURSOS = SRC_OUTPUT_DIR / "csv_cursos.csv"
SRC_CSV_INSTITUICOES = SRC_OUTPUT_DIR / "csv_instituicoes.csv"

TEMP_INST_CSV = OUTPUT_DIR / "temp_instituicoes_raw.csv"
TEMP_REL_CSV = OUTPUT_DIR / "temp_relacoes_raw.csv"


class ScraperPipeline:
    def __init__(self):
        self.snowflake_gen = SnowflakeGenerator(datacenter_id=1, worker_id=1)
        self.client = CNCTApiClient(log_callback=self.log)

    def log(self, message: str, level: str = "INFO"):
        """
        Emite logs no terminal do sistema e transmite via WebSocket thread-safe.
        """
        print(f"[{level}] {message}")
        ws_manager.send_log_threadsafe(message, level)

    def run(self, max_courses: int = 215) -> Dict[str, Any]:
        """
        Executa a raspagem de cursos e instituicoes ofertantes.
        Itera buscando IDs de cursos validos ate atingir o limite max_courses.
        """
        self.log(f"Iniciando pipeline de raspagem para extrair ate {max_courses} cursos validos...")
        self.client.start_session()

        courses_data = []
        institutions_map = {}
        relations = []

        try:
            # 1. Carregar catalogo inicial
            self.log("Consultando catalogo oficial no servidor do MEC...")
            catalog = self.client.get_home_catalog()
            if catalog and "catalogo" in catalog:
                total_cat = catalog["catalogo"].get("quantidadeCursos", 215)
                self.log(f"Catalogo oficial do MEC informado: {total_cat} cursos cadastrados.", "SUCESSO")

            # 2. Iterar buscando IDs validos (intervalo de 1 ate 260)
            current_id = 1
            max_search_id = 260

            while len(courses_data) < max_courses and current_id <= max_search_id:
                self.log(f"Consultando Curso ID original: {current_id} (Progresso: {len(courses_data)}/{max_courses})...")
                start_t = time.time()
                raw_course = self.client.get_course_details(current_id)
                elapsed = time.time() - start_t

                if not raw_course or "nome" not in raw_course or not raw_course["nome"]:
                    self.log(f"Curso ID {current_id} nao encontrado (Tempo: {elapsed:.2f}s). Avancando...", "AVISO")
                    current_id += 1
                    continue

                # Gerar Snowflake ID para o curso valido encontrado
                course_sf_id = self.snowflake_gen.generate_id()
                parsed_course = parse_course_record(raw_course, original_id=current_id, snowflake_id=course_sf_id)
                courses_data.append(parsed_course)

                course_name = parsed_course["nome_curso"]
                self.log(f"SUCESSO! Curso #{len(courses_data)} extraído em {elapsed:.2f}s: '{course_name}' (ID Original: {current_id}, Snowflake ID: {course_sf_id})", "SUCESSO")

                # Buscar instituicoes ofertantes para o curso
                self.log(f"-> Buscando instituicoes ofertantes para '{course_name}'...")
                inst_start_t = time.time()
                raw_insts = self.client.get_institutions_by_course_name(course_name)
                inst_elapsed = time.time() - inst_start_t

                self.log(f"-> {len(raw_insts)} instituicoes ofertantes encontradas em {inst_elapsed:.2f}s para '{course_name}'", "SUCESSO" if len(raw_insts) > 0 else "INFO")

                for raw_i in raw_insts:
                    inst_nome = raw_i.get("nome", "").strip()
                    if not inst_nome:
                        continue

                    # Atribuicao de Snowflake ID unico para cada instituicao
                    if inst_nome not in institutions_map:
                        inst_sf_id = self.snowflake_gen.generate_id()
                        parsed_inst = parse_institution_record(raw_i, snowflake_id=inst_sf_id)
                        institutions_map[inst_nome] = parsed_inst
                    else:
                        inst_sf_id = institutions_map[inst_nome]["snowflake_id"]

                    # Registrar associacao N:N
                    relations.append((inst_sf_id, course_sf_id))

                current_id += 1

            # Gerar timestamp para preservação de histórico sem sobreposição
            import shutil
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            timestamped_cursos = OUTPUT_DIR / f"csv_cursos_{timestamp}.csv"
            timestamped_inst = OUTPUT_DIR / f"csv_instituicoes_{timestamp}.csv"

            # 3. Exportar csv_cursos_{timestamp}.csv e atualizar csv_cursos.csv em ambos os caminhos
            self.log(f"Exportando {len(courses_data)} cursos coletados para '{timestamped_cursos.name}'...")
            self._save_courses_csv(courses_data, timestamped_cursos)
            shutil.copy2(timestamped_cursos, CSV_CURSOS)
            try:
                shutil.copy2(timestamped_cursos, SRC_CSV_CURSOS)
            except Exception:
                pass

            # 4. Preparar arquivos temporarios para o Agregador em C
            self.log("Preparando arquivos temporarios de instituicoes para o Agregador C...")
            self._save_temp_institutions_csv(list(institutions_map.values()))
            self._save_temp_relations_csv(relations)

            # 5. Executar Agregador C de alta performance
            self.log("Invocando modulo em C para agregacao de Snowflake IDs em uint64_t...")
            c_success = run_c_aggregation(str(TEMP_INST_CSV), str(TEMP_REL_CSV), str(timestamped_inst))

            if c_success:
                shutil.copy2(timestamped_inst, CSV_INSTITUICOES)
                try:
                    shutil.copy2(timestamped_inst, SRC_CSV_INSTITUICOES)
                except Exception:
                    pass
                self.log(f"Sucesso! Arquivos finais gerados com timestamp '{timestamped_inst.name}' e 'csv_instituicoes.csv'.", "SUCESSO")

            summary = {
                "total_cursos": len(courses_data),
                "total_instituicoes": len(institutions_map),
                "total_relacoes": len(relations),
                "csv_cursos_timestamp": str(timestamped_cursos.resolve()),
                "csv_instituicoes_timestamp": str(timestamped_inst.resolve()),
                "csv_cursos_latest": str(CSV_CURSOS.resolve()),
                "csv_instituicoes_latest": str(CSV_INSTITUICOES.resolve())
            }

            self.log(f"Pipeline concluido com sucesso! Resumo final: {summary}", "SUCESSO")
            return summary

        finally:
            self.client.close_session()

    def _save_courses_csv(self, courses: List[Dict[str, Any]], target_path: Path = CSV_CURSOS):
        fieldnames = [
            "id_original", "snowflake_id", "nome_curso", "eixo_tecnologico",
            "carga_horaria", "pre_requisito", "perfil_profissional",
            "itinerarios", "campo_atuacao", "ocupacoes_cbo", "infraestrutura_minima"
        ]
        with open(target_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            writer.writerows(courses)

    def _save_temp_institutions_csv(self, institutions: List[Dict[str, Any]]):
        fieldnames = ["snowflake_id", "nome_instituicao", "dependencia_adm", "endereco", "telefone", "email", "homepage"]
        with open(TEMP_INST_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(fieldnames)
            for inst in institutions:
                writer.writerow([
                    inst["snowflake_id"],
                    inst["nome_instituicao"],
                    inst["dependencia_adm"],
                    inst["endereco"],
                    inst["telefone"],
                    inst["email"],
                    inst["homepage"]
                ])

    def _save_temp_relations_csv(self, relations: List[tuple]):
        with open(TEMP_REL_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["inst_snowflake_id", "course_snowflake_id"])
            for inst_id, course_id in relations:
                writer.writerow([inst_id, course_id])
