"""
Submódulo para exportação de planilhas Excel (.xlsx) multi-abas utilizando OpenXML nativo via zipfile.
100% livre de dependências externas (openpyxl, pandas, etc).
"""

import re
import html
import zipfile
from pathlib import Path
from typing import List, Tuple, Any


def get_col_letter(col_idx: int) -> str:
    """
    Converte um índice numérico de coluna (1-indexed) em letras do Excel (ex: 1->A, 27->AA).
    """
    result = ""
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        result = chr(65 + remainder) + result
    return result


def create_pure_python_xlsx(sheets: List[Tuple[str, List[str], List[List[Any]]]], excel_path: Path):
    """
    Gera um arquivo Excel (.xlsx) válido com múltiplas abas estilizadas utilizando apenas a biblioteca padrão (zipfile).
    """
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    illegal_char_re = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]')

    def clean_xml_str(val: Any) -> str:
        if val is None:
            return ""
        val_str = illegal_char_re.sub('', str(val))
        return html.escape(val_str)

    with zipfile.ZipFile(excel_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. [Content_Types].xml
        ct_overrides = []
        for i in range(1, len(sheets) + 1):
            ct_overrides.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')

        content_types_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  {"".join(ct_overrides)}
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>'''
        zf.writestr('[Content_Types].xml', content_types_xml)

        # 2. _rels/.rels
        rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''
        zf.writestr('_rels/.rels', rels_xml)

        # 3. xl/_rels/workbook.xml.rels
        wb_rels = []
        for i in range(1, len(sheets) + 1):
            wb_rels.append(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>')
        wb_rels.append(f'<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>')

        wb_rels_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {"".join(wb_rels)}
</Relationships>'''
        zf.writestr('xl/_rels/workbook.xml.rels', wb_rels_xml)

        # 4. xl/workbook.xml
        wb_sheets = []
        for i, (title, _, _) in enumerate(sheets, 1):
            clean_title = html.escape(title[:31])
            wb_sheets.append(f'<sheet name="{clean_title}" sheetId="{i}" r:id="rId{i}"/>')

        workbook_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    {"".join(wb_sheets)}
  </sheets>
</workbook>'''
        zf.writestr('xl/workbook.xml', workbook_xml)

        # 5. xl/styles.xml (Estilo 1 = Cabecalho com fundo escuro #1E293B e texto branco em negrito)
        styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="10"/><name val="Arial"/></font>
    <font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Arial"/></font>
  </fonts>
  <fills count="2">
    <fill><patternFill fillType="none"/></fill>
    <fill><patternFill fillType="solid"><fgColor rgb="FF1E293B"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="1">
    <border><left/><right/><top/><bottom/></border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="2">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="1" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
  </cellXfs>
</styleSheet>'''
        zf.writestr('xl/styles.xml', styles_xml)

        # 6. xl/worksheets/sheet{i}.xml
        for i, (_, headers, rows) in enumerate(sheets, 1):
            sheet_rows = []

            # Linha 1: Cabeçalhos com estilo 1
            header_cells = []
            for col_idx, h in enumerate(headers, 1):
                col_ref = f"{get_col_letter(col_idx)}1"
                val_clean = clean_xml_str(h)
                header_cells.append(f'<c r="{col_ref}" t="inlineStr" s="1"><is><t>{val_clean}</t></is></c>')
            sheet_rows.append(f'<row r="1">{"".join(header_cells)}</row>')

            # Linhas de Dados
            for row_idx, row in enumerate(rows, 2):
                row_cells = []
                for col_idx, val in enumerate(row, 1):
                    col_ref = f"{get_col_letter(col_idx)}{row_idx}"
                    val_clean = clean_xml_str(val)
                    row_cells.append(f'<c r="{col_ref}" t="inlineStr"><is><t>{val_clean}</t></is></c>')
                sheet_rows.append(f'<row r="{row_idx}">{"".join(row_cells)}</row>')

            sheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    {"".join(sheet_rows)}
  </sheetData>
</worksheet>'''
            zf.writestr(f'xl/worksheets/sheet{i}.xml', sheet_xml)
