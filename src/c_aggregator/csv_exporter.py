"""
Submódulo para exportação de relatórios CSV dos 4 tópicos de diff e formatação de diagnóstico ASCII.
Encapsulado na Classe POO DiffExporter.
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.c_aggregator.address_parser import parse_address_c
from src.c_aggregator.excel_exporter import create_pure_python_xlsx


class DiffExporter:
    """
    Classe utilitária para formatação de tabelas de diagnóstico e exportação de CSV / Excel.
    """

    @classmethod
    def export_to_files(cls, stats: Dict[str, Any], target_dir: Path) -> Dict[str, str]:
        """
        Exporta os 4 tópicos do Diff para arquivos CSV individuais e para 1 planilha Excel (.xlsx) com 4 abas.
        """
        target_dir.mkdir(parents=True, exist_ok=True)

        novos_list = stats.get("novos", [])
        alterados_list = stats.get("alterados", [])
        inativados_list = stats.get("inativados", [])
        cursos_detalhes_list = stats.get("cursos_detalhes", [])

        # 1. CSV 1: Instituições Novas
        csv1_path = target_dir / "diff_1_instituicoes_novas.csv"
        fieldnames_novos = [
            "snowflake_id", "nome_instituicao", "dependencia_adm", "endereco",
            "logradouro", "numero", "complemento", "bairro", "municipio", "uf", "cep",
            "telefone", "email", "homepage"
        ]
        sheet1_rows = []
        with open(csv1_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(fieldnames_novos)
            for item in novos_list:
                raw_end = item.get("endereco") or item.get("endereco_original") or ""
                parsed = parse_address_c(raw_end, native_muni=item.get("municipio"), native_uf=item.get("uf"))
                row = [
                    item.get("snowflake_id") or item.get("id") or "NOVO",
                    item.get("nome_instituicao") or item.get("nome") or "",
                    item.get("dependencia_adm") or "",
                    raw_end,
                    item.get("logradouro") or parsed.get("logradouro") or "",
                    item.get("numero") or parsed.get("numero") or "",
                    item.get("complemento") or parsed.get("complemento") or "",
                    item.get("bairro") or parsed.get("bairro") or "",
                    item.get("municipio") or parsed.get("municipio") or "",
                    item.get("uf") or parsed.get("uf") or "",
                    item.get("cep") or parsed.get("cep") or "",
                    item.get("telefone") or "",
                    item.get("email") or "",
                    item.get("homepage") or ""
                ]
                writer.writerow(row)
                sheet1_rows.append(row)

        # 2. CSV 2: Alterações Cadastrais
        csv2_path = target_dir / "diff_2_alteracoes_cadastrais.csv"
        fieldnames_alterados = [
            "snowflake_id", "nome_instituicao", "dependencia_adm", "diferencas_detectadas",
            "endereco_banco", "endereco_scraper", "logradouro", "numero", "complemento",
            "bairro", "municipio", "uf", "cep"
        ]
        sheet2_rows = []
        with open(csv2_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(fieldnames_alterados)
            for item in alterados_list:
                raw_end = item.get("endereco") or ""
                parsed = parse_address_c(raw_end, native_muni=item.get("municipio"), native_uf=item.get("uf"))
                diffs_str = " | ".join(item.get("diferencas_detectadas", []))
                row = [
                    item.get("id") or item.get("snowflake_id") or "",
                    item.get("nome_instituicao") or item.get("nome") or "",
                    item.get("dependencia_adm") or "",
                    diffs_str,
                    item.get("endereco_db") or "",
                    raw_end,
                    item.get("logradouro") or parsed.get("logradouro") or "",
                    item.get("numero") or parsed.get("numero") or "",
                    item.get("complemento") or parsed.get("complemento") or "",
                    item.get("bairro") or parsed.get("bairro") or "",
                    item.get("municipio") or parsed.get("municipio") or "",
                    item.get("uf") or parsed.get("uf") or "",
                    item.get("cep") or parsed.get("cep") or ""
                ]
                writer.writerow(row)
                sheet2_rows.append(row)

        # 3. CSV 3: Instituições Inativadas
        csv3_path = target_dir / "diff_3_instituicoes_inativadas.csv"
        fieldnames_inativados = [
            "snowflake_id", "nome_instituicao", "dependencia_adm", "endereco",
            "logradouro", "numero", "complemento", "bairro", "municipio", "uf", "cep", "status"
        ]
        sheet3_rows = []
        with open(csv3_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(fieldnames_inativados)
            for item in inativados_list:
                raw_end = item.get("endereco") or item.get("endereco_original") or ""
                parsed = parse_address_c(raw_end, native_muni=item.get("municipio"), native_uf=item.get("uf"))
                row = [
                    item.get("id") or item.get("snowflake_id") or "",
                    item.get("nome_instituicao") or item.get("nome") or "",
                    item.get("dependencia_adm") or "",
                    raw_end,
                    item.get("logradouro") or parsed.get("logradouro") or "",
                    item.get("numero") or parsed.get("numero") or "",
                    item.get("complemento") or parsed.get("complemento") or "",
                    item.get("bairro") or parsed.get("bairro") or "",
                    item.get("municipio") or parsed.get("municipio") or "",
                    item.get("uf") or parsed.get("uf") or "",
                    item.get("cep") or parsed.get("cep") or "",
                    "Inativado (ativo=0)"
                ]
                writer.writerow(row)
                sheet3_rows.append(row)

        # 4. CSV 4: Detalhamento de Ofertas de Cursos
        csv4_path = target_dir / "diff_4_detalhamento_cursos_ofertas.csv"
        fieldnames_cursos = ["snowflake_id", "nome_instituicao", "tipo_alteracao", "nome_curso"]
        sheet4_rows = []
        with open(csv4_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(fieldnames_cursos)
            for item in cursos_detalhes_list:
                row = [
                    item.get("id") or item.get("snowflake_id") or "",
                    item.get("nome_instituicao") or item.get("nome") or "",
                    item.get("tipo") or "",
                    item.get("curso") or ""
                ]
                writer.writerow(row)
                sheet4_rows.append(row)

        # 5. Planilha Excel (.xlsx) Consolidada
        excel_path = target_dir / "diff_relatorio_completo.xlsx"
        sheets_payload = [
            ("1. Instituicoes Novas", fieldnames_novos, sheet1_rows),
            ("2. Alteracoes Cadastrais", fieldnames_alterados, sheet2_rows),
            ("3. Instituicoes Inativadas", fieldnames_inativados, sheet3_rows),
            ("4. Detalhamento de Ofertas", fieldnames_cursos, sheet4_rows)
        ]

        try:
            create_pure_python_xlsx(sheets_payload, excel_path)
        except Exception as e:
            print(f"[EXPORT EXCEL ERROR] Falha ao gerar arquivo Excel: {e}")

        return {
            "csv_1": str(csv1_path.resolve()),
            "csv_2": str(csv2_path.resolve()),
            "csv_3": str(csv3_path.resolve()),
            "csv_4": str(csv4_path.resolve()),
            "excel": str(excel_path.resolve())
        }

    @staticmethod
    def format_novas_instituicoes_table(novos: List[Dict[str, Any]]) -> str:
        """
        Gera tabela formatada em texto listando as instituições novas.
        """
        if not novos:
            return "Nenhuma nova instituição identificada no lote importado."

        items_show = novos[:50]
        col_sf = 15
        col_nome = 45
        col_adm = 15
        col_end = 65

        lines = []
        lines.append(f"{'SNOWFLAKE ID':<{col_sf}} | {'NOME DA INSTITUIÇÃO':<{col_nome}} | {'DEP. ADM':<{col_adm}} | {'ENDEREÇO COMPLETO'}")
        lines.append("-" * (col_sf + col_nome + col_adm + col_end + 9))

        for item in items_show:
            sf_id = str(item.get('snowflake_id') or item.get('id') or "NOVO")[:col_sf]
            nome = str(item.get('nome_instituicao') or item.get('nome') or "")[:col_nome]
            adm = str(item.get('dependencia_adm') or "")[:col_adm]
            end = str(item.get('endereco') or item.get('endereco_original') or "")

            lines.append(f"{sf_id:<{col_sf}} | {nome:<{col_nome}} | {adm:<{col_adm}} | {end}")

        if len(novos) > 50:
            lines.append(f"... e mais {len(novos) - 50} instituições novas no lote.")

        return "\n".join(lines)

    @staticmethod
    def format_alterados_table(alterados: List[Dict[str, Any]]) -> str:
        """
        Gera tabela formatada em texto listando as alterações cadastrais.
        """
        if not alterados:
            return "Nenhuma alteração cadastral identificada no lote importado."

        items_show = alterados[:50]
        col_sf = 18
        col_nome = 40
        col_diff = 60

        lines = []
        lines.append(f"{'SNOWFLAKE ID':<{col_sf}} | {'NOME DA INSTITUIÇÃO':<{col_nome}} | {'DIVERGÊNCIAS DETECTADAS'}")
        lines.append("-" * (col_sf + col_nome + col_diff + 6))

        for item in items_show:
            sf_id = str(item.get('id') or item.get('snowflake_id') or "")[:col_sf]
            nome = str(item.get('nome_instituicao') or item.get('nome') or "")[:col_nome]
            diffs = " | ".join(item.get('diferencas_detectadas', []))

            lines.append(f"{sf_id:<{col_sf}} | {nome:<{col_nome}} | {diffs}")

        if len(alterados) > 50:
            lines.append(f"... e mais {len(alterados) - 50} alterações cadastrais no lote.")

        return "\n".join(lines)

    @staticmethod
    def format_inativados_table(inativados: List[Dict[str, Any]]) -> str:
        """
        Gera tabela formatada em texto listando as instituições a serem inativadas.
        """
        if not inativados:
            return "Nenhuma instituição a ser inativada."

        items_show = inativados[:50]
        col_sf = 18
        col_nome = 40
        col_end = 60

        lines = []
        lines.append(f"{'SNOWFLAKE ID':<{col_sf}} | {'NOME DA INSTITUIÇÃO':<{col_nome}} | {'ENDEREÇO BANCO'}")
        lines.append("-" * (col_sf + col_nome + col_end + 6))

        for item in items_show:
            sf_id = str(item.get('id') or item.get('snowflake_id') or "")[:col_sf]
            nome = str(item.get('nome_instituicao') or item.get('nome') or "")[:col_nome]
            end = str(item.get('endereco') or "")

            lines.append(f"{sf_id:<{col_sf}} | {nome:<{col_nome}} | {end}")

        if len(inativados) > 50:
            lines.append(f"... e mais {len(inativados) - 50} instituições a serem inativadas no lote.")

        return "\n".join(lines)

    @staticmethod
    def format_cursos_detalhes_table(cursos_detalhes: List[Dict[str, Any]]) -> str:
        """
        Gera tabela formatada em texto listando as alterações de cursos.
        """
        if not cursos_detalhes:
            return "Nenhuma alteração em ofertas de cursos identificada."

        items_show = cursos_detalhes[:50]
        col_sf = 18
        col_nome = 35
        col_tipo = 15
        col_curso = 45

        lines = []
        lines.append(f"{'SNOWFLAKE ID':<{col_sf}} | {'NOME DA INSTITUIÇÃO':<{col_nome}} | {'TIPO':<{col_tipo}} | {'NOME DO CURSO'}")
        lines.append("-" * (col_sf + col_nome + col_tipo + col_curso + 9))

        for item in items_show:
            sf_id = str(item.get('id') or item.get('snowflake_id') or "")[:col_sf]
            nome = str(item.get('nome_instituicao') or item.get('nome') or "")[:col_nome]
            tipo = str(item.get('tipo') or "")[:col_tipo]
            curso = str(item.get('curso') or "")

            lines.append(f"{sf_id:<{col_sf}} | {nome:<{col_nome}} | {tipo:<{col_tipo}} | {curso}")

        if len(cursos_detalhes) > 50:
            lines.append(f"... e mais {len(cursos_detalhes) - 50} detalhamentos de cursos no lote.")

        return "\n".join(lines)

    @classmethod
    def generate_text_diagnosis(cls, stats: Dict[str, Any]) -> str:
        """
        Gera um relatório descritivo completo em formato texto markdown para o diagnóstico.
        """
        novos = stats.get('novos', [])
        alterados = stats.get('alterados', [])
        inativados = stats.get('inativados', [])
        mantidos = stats.get('mantidos', [])
        reativados = stats.get('reativados', [])
        cursos_detalhes = stats.get('cursos_detalhes', [])
        is_parcial = stats.get('is_parcial', False)

        total_csv = stats.get('total_csv', 0)
        total_db = stats.get('total_db', 0)
        cursos_unicos = stats.get('cursos_unicos_csv_qtd', 0)
        est_cursos = stats.get('estatisticas_cursos', {})

        lines = []
        lines.append("=" * 90)
        lines.append("DIAGNÓSTICO E RELATÓRIO COMPLETO DE MIGRAÇÃO CNCT (C ENGINE)")
        lines.append("=" * 90)
        lines.append(f"Total de Instituições no Banco de Dados (VPS): {total_db}")
        lines.append(f"Total de Instituições no Lote Importado (CSV): {total_csv}")
        lines.append(f"Total de Cursos Únicos Identificados no CSV: {cursos_unicos}")
        lines.append(f"Modo de Importação: {'PARCIAL (Carga por Estado/Filtro)' if is_parcial else 'COMPLETA (Carga Nacional)'}")
        lines.append("-" * 90)
        lines.append("RESUMO EXECUTIVO DE MUDANÇAS DE ESTADO:")
        lines.append(f"  1. RELAÇÃO DE INSTITUIÇÕES NOVAS IDENTIFICADAS (INSERT): {len(novos)}")
        lines.append(f"  2. COMPARAÇÃO DE ALTERAÇÕES CADASTRAIS (UPDATE): {len(alterados)}")
        lines.append(f"  3. INSTITUIÇÕES MANTIDAS SEM ALTERAÇÕES (MANTIDOS): {len(mantidos)}")
        lines.append(f"  4. INSTITUIÇÕES REATIVADAS (SET ATIVO=1): {len(reativados)}")
        lines.append(f"  5. RELAÇÃO DE INSTITUIÇÕES A SEREM INATIVADAS (SET ATIVO=0): {len(inativados)} {'(Ignorado em Carga Parcial)' if is_parcial else ''}")
        lines.append("-" * 90)

        if est_cursos:
            lines.append("MUDANÇAS DE OFERTAS DE CURSOS (NÍVEL DE CURSOS):")
            lines.append(f"  - Novas Ofertas Vinculadas: {est_cursos.get('novos_cursos_qtd', 0)}")
            lines.append(f"  - Ofertas Mantidas: {est_cursos.get('cursos_mantidos_qtd', 0)}")
            lines.append(f"  - Ofertas Descontinuadas/Encerradas: {est_cursos.get('cursos_descontinuados_qtd', 0)}")
            lines.append("-" * 90)

        lines.append("\n1. RELAÇÃO DE INSTITUIÇÕES NOVAS IDENTIFICADAS")
        lines.append("=" * 90)
        lines.append(cls.format_novas_instituicoes_table(novos))

        lines.append("\n\n2. COMPARAÇÃO DE ALTERAÇÕES CADASTRAIS (BANCO MYSQL vs RASPAGEM CNCT)")
        lines.append("=" * 90)
        lines.append(cls.format_alterados_table(alterados))

        lines.append("\n\n3. RELAÇÃO DE INSTITUIÇÕES A SEREM INATIVADAS (ativo = 0)")
        lines.append("=" * 90)
        lines.append(cls.format_inativados_table(inativados))

        lines.append("\n\n4. DETALHAMENTO DE CURSOS E OFERTAS (NOVOS VÍNCULOS / ENCERRADOS)")
        lines.append("=" * 90)
        lines.append(cls.format_cursos_detalhes_table(cursos_detalhes))

        return "\n".join(lines)


# Delegadores de nível de módulo para 100% de retrocompatibilidade
export_diff_to_files = DiffExporter.export_to_files
format_novas_instituicoes_table = DiffExporter.format_novas_instituicoes_table
format_alterados_table = DiffExporter.format_alterados_table
format_inativados_table = DiffExporter.format_inativados_table
format_cursos_detalhes_table = DiffExporter.format_cursos_detalhes_table
generate_text_diagnosis_c = DiffExporter.generate_text_diagnosis
