"""
Módulo de Fachada (Facade Design Pattern) para o pacote c_aggregator.
Re-exporta todas as classes POO e submódulos hiperespecializados:
- RomanNumeralProtector (numerais_romanos.py)
- CepExtractor (ceps.py)
- AddressParser (address_parser.py)
- TextNormalizer (text_normalizer.py)
- DiffEngine (diff_matching.py)
- PostDiffAuditor (post_diff_audit.py)
- DiffExporter (csv_exporter.py)

Garante 100% de retrocompatibilidade com todas as rotas da FastAPI e suíte de testes.
"""

from src.c_aggregator.c_interop import (
    compile_c_aggregator,
    run_c_aggregation,
    _python_fallback_aggregation
)

from src.c_aggregator.numerais_romanos import (
    RomanNumeralProtector
)

from src.c_aggregator.ceps import (
    CepExtractor
)

from src.c_aggregator.address_parser import (
    AddressParser,
    clean_text_accents,
    clean_deduplicate_address,
    is_valid_municipio_candidate,
    normalize_muni_name,
    parse_address_c,
    sanitize_municipio_name,
    INVALID_MUNI_PREFIXES
)

from src.c_aggregator.text_normalizer import (
    TextNormalizer,
    expand_abbreviations,
    normalize_natural_key,
    clean_pedagogical_acronyms,
    normalize_core_name,
    extract_location_keys,
    has_ead_indicator,
    calculate_name_richness_score
)

from src.c_aggregator.diff_matching import (
    DiffEngine,
    compare_datasets_c
)

from src.c_aggregator.post_diff_audit import (
    PostDiffAuditor,
    run_post_diff_audit_c
)

from src.c_aggregator.excel_exporter import (
    get_col_letter,
    create_pure_python_xlsx
)

from src.c_aggregator.csv_exporter import (
    DiffExporter,
    export_diff_to_files,
    format_novas_instituicoes_table,
    generate_text_diagnosis_c
)

__all__ = [
    "RomanNumeralProtector",
    "CepExtractor",
    "AddressParser",
    "TextNormalizer",
    "DiffEngine",
    "PostDiffAuditor",
    "DiffExporter",
    "compile_c_aggregator",
    "run_c_aggregation",
    "_python_fallback_aggregation",
    "clean_text_accents",
    "clean_deduplicate_address",
    "is_valid_municipio_candidate",
    "normalize_muni_name",
    "parse_address_c",
    "sanitize_municipio_name",
    "INVALID_MUNI_PREFIXES",
    "expand_abbreviations",
    "normalize_natural_key",
    "clean_pedagogical_acronyms",
    "normalize_core_name",
    "extract_location_keys",
    "has_ead_indicator",
    "calculate_name_richness_score",
    "compare_datasets_c",
    "run_post_diff_audit_c",
    "get_col_letter",
    "create_pure_python_xlsx",
    "export_diff_to_files",
    "format_novas_instituicoes_table",
    "generate_text_diagnosis_c"
]
