"""
Módulo de parsing e normalização de atributos de Cursos e Instituições.
"""

from typing import Dict, Any


def clean_text(text: Any) -> str:
    """
    Remove caracteres indesejados e normaliza espacos.
    """
    if not text:
        return "não informado"
    text_str = str(text).strip()
    return text_str if text_str else "não informado"


def parse_course_record(raw_course: Dict[str, Any], original_id: int, snowflake_id: int) -> Dict[str, Any]:
    """
    Normaliza um registro de curso mapeando seções para colunas do CSV final.
    """
    areas = raw_course.get("areasTecnologicas", [])
    eixo_nome = "não informado"
    if areas and isinstance(areas, list) and len(areas) > 0:
        eixo_nome = areas[0].get("nome", "não informado")

    return {
        "id_original": original_id,
        "snowflake_id": snowflake_id,
        "nome_curso": clean_text(raw_course.get("nome")),
        "eixo_tecnologico": eixo_nome,
        "carga_horaria": clean_text(raw_course.get("cargaHoraria")),
        "pre_requisito": clean_text(raw_course.get("preRequisito")),
        "perfil_profissional": clean_text(raw_course.get("perfilProfissional")),
        "itinerarios": clean_text(raw_course.get("itinerarios")),
        "campo_atuacao": clean_text(raw_course.get("campoAtuacao")),
        "ocupacoes_cbo": clean_text(raw_course.get("ocupacoesCbo")),
        "infraestrutura_minima": clean_text(raw_course.get("infraestruturaMinima"))
    }


def parse_institution_record(raw_inst: Dict[str, Any], snowflake_id: int) -> Dict[str, Any]:
    """
    Normaliza os atributos de uma instituicao ofertante.
    """
    cidade_val = clean_text(raw_inst.get("cidade") or raw_inst.get("municipio"))
    return {
        "snowflake_id": snowflake_id,
        "nome_instituicao": clean_text(raw_inst.get("nome")),
        "dependencia_adm": clean_text(raw_inst.get("tipo")),
        "endereco": clean_text(raw_inst.get("endereco")),
        "telefone": clean_text(raw_inst.get("telefone")),
        "email": clean_text(raw_inst.get("email")),
        "homepage": clean_text(raw_inst.get("site")),
        "uf": clean_text(raw_inst.get("uf")),
        "cidade": cidade_val,
        "municipio": cidade_val
    }
