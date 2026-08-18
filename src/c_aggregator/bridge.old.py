"""
Módulo monolítico original preservado como bridge.old.py para auditoria comparativa direta.
"""

import os
import re
import sys
import csv
import json
import html
import zipfile
import subprocess
import unicodedata
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

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

    print("[C BRIDGE] Compilador C nao detectado no PATH do sistema. Utilizando fallback nativo.")
    return False


def run_c_aggregation(institutions_csv: str, relations_csv: str, output_csv: str) -> bool:
    """
    Executa a agregação de cursos por instituição.
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

    print("[C BRIDGE] Executando agregação via motor Python de alta precisao...")
    return _python_fallback_aggregation(institutions_csv, relations_csv, output_csv)


def _python_fallback_aggregation(institutions_csv: str, relations_csv: str, output_csv: str) -> bool:
    """
    Fallback em Python que espelha exatamente o comportamento de 64-bits do C.
    """
    try:
        institutions = {}
        
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

        if os.path.exists(relations_csv):
            with open(relations_csv, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    inst_id = int(row["inst_snowflake_id"])
                    course_id = int(row["course_snowflake_id"])
                    if inst_id in institutions:
                        if course_id not in institutions[inst_id]["cursos"]:
                            institutions[inst_id]["cursos"].append(course_id)

        fieldnames = [
            "snowflake_id", "nome_instituicao", "dependencia_adm",
            "endereco", "logradouro", "numero", "complemento",
            "bairro", "municipio", "uf", "cep",
            "telefone", "email", "homepage", "cursos_ofertados_ids"
        ]

        with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(fieldnames)

            for inst_id, data in institutions.items():
                cursos_json = json.dumps(data["cursos"])
                parsed = parse_address_c(data["endereco"], native_muni=data.get("municipio") or data.get("cidade"), native_uf=data.get("uf"))
                writer.writerow([
                    data["snowflake_id"],
                    data["nome_instituicao"],
                    data["dependencia_adm"],
                    data["endereco"],
                    parsed["logradouro"],
                    parsed["numero"],
                    parsed["complemento"],
                    parsed["bairro"],
                    parsed["municipio"],
                    parsed["uf"],
                    parsed["cep"],
                    data["telefone"],
                    data["email"],
                    data["homepage"],
                    cursos_json
                ])

        print(f"[C BRIDGE] Arquivo agregado gerado com sucesso com colunas estruturadas de endereço: {output_csv}")
        return True
    except Exception as e:
        print(f"[C BRIDGE ERRO]: {e}")
        return False


def clean_text_accents(text: str) -> str:
    """
    Remove acentos, converte para minúsculas e remove pontuações.
    """
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(text).lower().strip())
    no_accents = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return re.sub(r'[^a-z0-9\s]', ' ', no_accents)


def expand_abbreviations(text: str) -> str:
    """
    Expande abreviações padrão de instituições de ensino técnico no Brasil.
    """
    if not text:
        return ""
    txt = clean_text_accents(text)
    
    txt = re.sub(r'\b([a-z])\.\s*([a-z])\.\s*([a-z])\.\s*([a-z])\.\b', r'\1\2\3\4', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\b([a-z])\.\s*([a-z])\.\s*([a-z])\.\b', r'\1\2\3', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\b([a-z])\.\s*([a-z])\.\b', r'\1\2', txt, flags=re.IGNORECASE)
    txt = txt.replace('.', ' ')

    rules = [
        (r'\b(ee|e\s*e)\b', 'escola estadual'),
        (r'\b(em|e\s*m)\b', 'escola municipal'),
        (r'\b(ce|c\s*e)\b', 'colegio estadual'),
        (r'\b(ceja|c\s*e\s*j\s*a)\b', 'centro de educacao de jovens e adultos'),
        (r'\b(esc\s*tec\s*est)\b', 'escola tecnica estadual'),
        (r'\b(esc\s*tec)\b', 'escola tecnica'),
        (r'\besc\b', 'escola'),
        (r'\btec\b', 'tecnica'),
        (r'\best\b', 'estadual'),
        (r'\bprof\b|\bprofa\b|\bprofª\b', 'professor'),
        (r'\bdr\b|\bdra\b', 'doutor'),
        (r'\bpres\b', 'presidente'),
        (r'\bsta\b', 'santa'),
        (r'\bsto\b', 'santo'),
        (r'\bnsra\b|\bns\b', 'nossa senhora'),
        (r'\beem\b', 'escola de ensino medio'),
        (r'\beeb\b', 'escola de educacao basica'),
        (r'\beepp?\b', 'escola de educacao profissional'),
        (r'\bceep\b', 'centro estadual de educacao profissional'),
        (r'\bciep\b', 'centro integrado de educacao publica'),
        (r'\bunicasul\b|\bunicsul\b', 'universidade cruzeiro do sul'),
        (r'\bassis\b', 'francisco de assis'),
        (r'\bkubistchek\b', 'kubitschek'),
    ]
    for pattern, repl in rules:
        txt = re.sub(pattern, repl, txt)
    
    return re.sub(r'\s+', ' ', txt).strip()


def normalize_muni_name(muni: str) -> str:
    """
    Normaliza nomes de municípios brasileiros tornando-os imunes a diferenças
    de preposições (de/do/da/dos/das/e), acentos, hífens, grafias fonéticas e variações.
    """
    if not muni:
        return ""
    txt = clean_text_accents(muni)
    
    txt = txt.replace('z', 's').replace('j', 'g').replace('y', 'i')
    txt = re.sub(r'ç|ss', 's', txt)
    txt = re.sub(r'eo$', 'eu', txt)
    txt = re.sub(r'aes$', 'ais', txt)
    
    stop_words = {'de', 'do', 'da', 'dos', 'das', 'e', 'rr', 'am', 'sp', 'mg', 'rs', 'sc', 'ba', 'pa', 'ma', 'se', 'rj', 'ms', 'mt', 'ac', 'al', 'ap', 'ce', 'df', 'es', 'go', 'pb', 'pr', 'pe', 'pi', 'ro', 'rn', 'to'}
    words = [w for w in txt.split() if w not in stop_words and not w.isdigit()]
    return re.sub(r'[^a-z]', '', "".join(words))


def normalize_natural_key(nome: str, muni: str, uf: str = "") -> str:
    """
    Gera uma chave determinística normalizada a partir de (nome, município, UF)
    com expansão de abreviações institucionais e normalização imunizada de município.
    """
    raw_nome = expand_abbreviations(nome)
    raw_muni = normalize_muni_name(muni)
    raw_uf = clean_text_accents(uf).upper()[:2]
    
    parts = [p for p in [raw_nome, raw_muni, raw_uf] if p]
    raw = "_".join(parts).strip()
    return re.sub(r'[^a-z0-9_]', '', raw)


def clean_pedagogical_acronyms(name: str) -> str:
    """
    Remove acrônimos pedagógicos estaduais comuns que poluem o nome da instituição nas raspagens do MEC/CNCT.
    """
    if not name:
        return ""
    cleaned = name.lower()
    cleaned = re.sub(r'[\-\/,]', ' ', cleaned)
    acronyms = [
        r'\befmp\b', r'\beti\b', r'\bprofis\b', r'\bens\s+fund\b', r'\bmedio\b',
        r'\be\s+e\s+e\s+fund\b', r'\bc\s*e\b', r'\be\s*e\b', r'\be\s*e\s*b\b',
        r'\bcm\b', r'\bemp\b', r'\bei\b', r'\bmp\b'
    ]
    for acr in acronyms:
        cleaned = re.sub(acr, ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return clean_text_accents(cleaned)


def normalize_core_name(name: str) -> str:
    """
    Normaliza o nome da instituição removendo prefixos/abreviações institucionais genéricas
    para comparar apenas o núcleo próprio do nome.
    """
    clean = expand_abbreviations(name)
    prefixes = [
        r'\bescola tecnica estadual de educacao profissional\b',
        r'\bescola tecnica estadual\b',
        r'\bescola tecnica municipal\b',
        r'\bescola tecnica de educacao profissional\b',
        r'\bescola tecnica\b',
        r'\bescola estadual de educacao profissional\b',
        r'\bescola estadual de educacao basica\b',
        r'\bescola estadual de ensino medio\b',
        r'\bescola estadual\b',
        r'\bescola municipal\b',
        r'\binstituto federal\b',
        r'\buniversidade\b',
        r'\bfaculdade\b',
        r'\bcolegio estadual\b',
        r'\bcolegio\b',
        r'\bcentro de educacao de jovens e adultos\b',
        r'\bcentro estadual de educacao profissional\b',
        r'\bcentro de educacao profissional\b',
        r'\bcentro educacional\b',
        r'\bcentro integrado de educacao publica\b',
        r'\bcentro de excelencia\b',
        r'\bescola de educacao profissional\b',
        r'\bescola de especializacao\b',
        r'\bescola agropecuaria\b',
        r'\bescola de musica\b',
        r'\bliceu pedagogico\b',
        r'\bescola senai\b',
        r'\bhotel escola senac\b',
        r'\bhotel escola\b',
        r'\binstituto de ensino e cultura\b',
        r'\binstituto educacional de contagem\b',
        r'\bcentro de profissionalizacao do vale do\b',
        r'\bcentro de profissionalizacao\b',
        r'\bcentro tecnico potiguar\b'
    ]
    for p in prefixes:
        clean = re.sub(p, ' ', clean)

    suffixes = [
        r'\b(c\s*e[\s\-]*ef\s*m\s*eti\s*prof|c\s*e[\s\-]*ef\s*m\s*profis|c\s*e\s*c\s*m\s*efmp|c\s*e\s*e\s*fund\s*med|e\s*e\s*e\s*fund|ef\s*m\s*eti\s*prof|ef\s*m\s*profis|fund\s*med|ens\s*med|ens\s*fund|eti\s*prof|profis|efmp|eti|ef\s*m|ef|em|ead|ei|mp)\b'
    ]
    for s in suffixes:
        clean = re.sub(s, ' ', clean)

    clean = re.sub(r'\b(de poxoreu|de poxoreo|de contagem|do sul|de jacarei|de manaus|assu|acu)\b', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return re.sub(r'[^a-z0-9]', '', clean)


def extract_location_keys(address_str: str, muni: str, uf: str):
    """
    Extrai chave purificada de localização (CEP + número limpo) e (logradouro limpo + número limpo)
    para pareamento resiliência por edifícios e propriedades no MySQL.
    """
    if not address_str or address_str.strip().lower() in ("", "não informado", "n/i", "none"):
        return "", "", ""
    
    parsed = parse_address_c(address_str, native_muni=muni, native_uf=uf)
    cep = (parsed.get("cep") or "").strip()
    num = (parsed.get("numero") or "").strip()
    logr = (parsed.get("logradouro") or "").strip()

    if cep.endswith("000") or len(cep) != 8:
        cep = ""

    num_digits = re.sub(r'\D', '', num)
    if not num_digits:
        if num.lower() in ("s/n", "sn", "sem numero", "sem número", "0", "00"):
            num_clean = "sn"
        else:
            num_clean = ""
    else:
        num_clean = num_digits

    logr_clean = clean_text_accents(logr.lower())
    for pref in ("rua ", "avenida ", "av ", "travessa ", "trv ", "praça ", "pça ", "alameda ", "rodovia ", "rod "):
        if logr_clean.startswith(pref):
            logr_clean = logr_clean[len(pref):].strip()
            break

    return cep, num_clean, logr_clean


def clean_deduplicate_address(raw_address: str) -> str:
    """
    Higieniza o texto bruto de endereço raspado do CNCT:
    1. Purga totalmente referências a Caixa Postal (ex: Cx. Postal, Cx.postal-119.253, C.P. 123).
    2. Corrige erros comuns de digitação/raspagem em prefixos de logradouro ('Enida' -> 'Avenida', etc).
    3. Remove duplicações sequenciais de trechos (ex: 'Rua X, 100, Rua X, 100').
    4. Limpa pontuações duplicadas e espaços extras.
    """
    if not raw_address:
        return ""
    
    txt = raw_address
    txt = re.sub(r'\b(?:Cx\.?\s*postal|Caixa\s*postal|C\.?\s*P\.?)\s*[-:]?\s*[\d\.\-]*\b(?:\s*CEP\s*[-:]?\s*\d{5}-?\d{3})?', '', txt, flags=re.IGNORECASE)

    txt = re.sub(r'\bEnida\b', 'Avenida', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\bAv\.\b|\bAv\b', 'Avenida', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\bR\.\b', 'Rua', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\bAl\.\b', 'Alameda', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\bPco\.\b', 'Praça', txt, flags=re.IGNORECASE)

    parts = [p.strip() for p in txt.split(',') if p.strip()]
    unique_parts = []
    seen = set()

    for p in parts:
        p_lower = p.lower()
        if p_lower not in seen:
            seen.add(p_lower)
            unique_parts.append(p)

    cleaned = ", ".join(unique_parts)
    return re.sub(r'\s+', ' ', cleaned).strip()


INVALID_MUNI_PREFIXES = (
    "rua", "avenida", "av", "travessa", "trv", "praça", "pça", "alameda", "rodovia", "rod",
    "quadra", "qda", "setor", "st", "lote", "lt", "bloco", "bl", "apartamento", "apto",
    "sala", "sl", "sn", "s/n", "centro", "bairro", "distrito", "parque", "pq", "jardim", "jd",
    "km", "nº", "no", "n"
)


def is_valid_municipio_candidate(candidate: Optional[str]) -> bool:
    """
    Verifica se uma string candidata a município é válida e não é lixo de logradouro/número/sala.
    """
    if not candidate:
        return False
    cand_str = candidate.strip().lower()
    if not cand_str or cand_str in ("não informado", "n/i", "none"):
        return False
    if re.match(r'^\d+$', cand_str):
        return False
    if re.match(r'^(sl|sala|setor|qda|quadra|lote|bloco|apto)\s*[-:]?\s*\d*', cand_str):
        return False
    for pref in INVALID_MUNI_PREFIXES:
        if cand_str == pref or cand_str.startswith(pref + " ") or cand_str.startswith(pref + "."):
            return False
    return True


def parse_address_c(raw_address: str, native_muni: Optional[str] = None, native_uf: Optional[str] = None) -> Dict[str, Any]:
    """
    Decompõe o texto bruto de endereço em colunas individuais.
    """
    muni_final = native_muni.strip() if (native_muni and is_valid_municipio_candidate(native_muni)) else None
    uf_final = native_uf.strip()[:2].upper() if (native_uf and len(native_uf.strip()) >= 2) else None

    if not raw_address or raw_address.strip() == "" or raw_address.strip().lower() == "não informado":
        return {
            "logradouro": None, "numero": None, "complemento": None,
            "bairro": None, "municipio": muni_final, "uf": uf_final, "cep": None
        }

    raw = clean_deduplicate_address(raw_address.strip().strip('.,;- '))

    cep = None
    uf = uf_final

    cep_matches = list(re.finditer(r'(?:-\s*|CEP\s*:?\s*|\s+)(\d{5}-?\d{3})\b', raw, re.IGNORECASE))
    if cep_matches:
        last_match = cep_matches[-1]
        cep = last_match.group(1).replace('-', '')
        raw = raw[:last_match.start()].strip().strip('.,;- ')

    if not uf:
        uf_match = re.search(r'(?:[\s,/|-]+)([A-Z]{2})\b\s*$', raw, re.IGNORECASE)
        if uf_match:
            possible_uf = uf_match.group(1).upper()
            valid_ufs = {"AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"}
            if possible_uf in valid_ufs:
                uf = possible_uf
                raw = raw[:uf_match.start()].strip().strip('.,;- ')

    raw = re.sub(r'\b\d{5}-?\d{3}\b', '', raw).strip().strip('.,;- ')
    partes = [p.strip() for p in raw.split(',') if p.strip()]

    logradouro = None
    numero = None
    complemento = None
    bairro = None
    municipio = muni_final

    if not municipio and partes:
        for p in reversed(partes):
            p_clean = re.sub(r'\b\d{5}-?\d{3}\b', '', p).strip()
            p_clean = re.sub(r'\b[A-Z]{2}\b$', '', p_clean, flags=re.IGNORECASE).strip()
            if is_valid_municipio_candidate(p_clean):
                municipio = p_clean
                break

    if len(partes) == 2:
        logradouro = partes[0]
        numero = partes[1]
    elif len(partes) == 3:
        logradouro = partes[0]
        numero = partes[1]
        bairro = partes[2]
    elif len(partes) >= 4:
        logradouro = partes[0]
        numero = partes[1]
        complemento = ", ".join(partes[2:-1])
        bairro = partes[-1]

    return {
        "logradouro": logradouro,
        "numero": numero,
        "complemento": complemento,
        "bairro": bairro,
        "municipio": municipio,
        "uf": uf,
        "cep": cep
    }


def run_post_diff_audit_c(novos: List[Dict[str, Any]], alterados: List[Dict[str, Any]], db_items_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Esteira de Auditoria Automática Pós-Diff.
    """
    filtered_novos = []

    for csv_novo in novos:
        n_nome = (csv_novo.get('nome_instituicao') or csv_novo.get('nome') or "").strip()
        n_end = (csv_novo.get('endereco') or csv_novo.get('endereco_original') or "").strip()
        n_muni = (csv_novo.get('municipio') or csv_novo.get('cidade') or "").strip()
        n_uf = clean_text_accents(csv_novo.get('uf') or "").upper()[:2]
        
        n_cep, n_num, n_logr = extract_location_keys(n_end, n_muni, n_uf)
        n_muni_norm = normalize_muni_name(n_muni)
        
        name_words = set(w for w in clean_text_accents(n_nome.lower()).split() 
                         if len(w) >= 4 and w not in ('escola', 'estadual', 'municipal', 'tecnica', 'profissional', 'educacao', 'centro', 'instituto', 'colegio', 'unidade', 'campus', 'curso', 'cursos'))
        
        matched_audit_db = None
        match_reason = ""
        
        for entry in db_items_list:
            db_obj = entry['db_item']
            db_uf = entry['uf']
            
            if n_uf and db_uf and n_uf != db_uf:
                continue
                
            db_nome = entry['nome']
            db_muni_norm = entry.get('muni_norm') or ""
            db_cep = entry.get('cep_val') or ""
            db_num = entry.get('num_val') or ""
            db_logr = entry.get('logr_val') or ""
            
            if n_cep and db_cep and n_cep == db_cep:
                if n_num and db_num and n_num != db_num:
                    continue
                matched_audit_db = db_obj
                match_reason = f"CEP {n_cep} e número {n_num or 'S/N'} coincidentes na VPS"
                break
                
            if n_logr and db_logr and n_num and db_num and n_logr == db_logr and n_num == db_num and n_muni_norm == db_muni_norm:
                matched_audit_db = db_obj
                match_reason = f"Logradouro '{n_logr}', nº {n_num} em {n_muni} coincidente na VPS"
                break
                
            if name_words and db_muni_norm == n_muni_norm:
                db_words = set(w for w in clean_text_accents(db_nome.lower()).split() if len(w) >= 4)
                common_words = name_words & db_words
                if len(common_words) >= 2 or any(len(w) >= 7 for w in common_words):
                    matched_audit_db = db_obj
                    match_reason = f"Tokens do nome ({', '.join(common_words)}) coincidentes na VPS em {n_muni}"
                    break

        if matched_audit_db:
            db_id = matched_audit_db.get('id') or matched_audit_db.get('snowflake_id')
            csv_novo['is_novo'] = False
            csv_novo['id'] = db_id
            csv_novo['snowflake_id'] = db_id
            csv_novo['endereco_db'] = matched_audit_db.get('endereco') or ""
            csv_novo['diferencas_detectadas'] = [f"auditoria_automática: '{matched_audit_db.get('nome_instituicao') or matched_audit_db.get('nome')}' ➔ '{n_nome}' ({match_reason})"]
            alterados.append(csv_novo)
        else:
            filtered_novos.append(csv_novo)

    return filtered_novos, alterados


def compare_datasets_c(db_data: List[Dict[str, Any]], csv_data: List[Dict[str, Any]], is_parcial: Optional[bool] = None) -> Dict[str, Any]:
    """
    Engine de pareamento multi-nível (Tiers 1 a 7).
    """
    from src.c_aggregator.diff_matching import compare_datasets_c as engine_fn
    return engine_fn(db_data, csv_data, is_parcial=is_parcial)


def get_col_letter(col_idx: int) -> str:
    from src.c_aggregator.excel_exporter import get_col_letter as fn
    return fn(col_idx)


def create_pure_python_xlsx(sheets: List[Tuple[str, List[str], List[List[Any]]]], excel_path: Path):
    from src.c_aggregator.excel_exporter import create_pure_python_xlsx as fn
    return fn(sheets, excel_path)


def export_diff_to_files(stats: Dict[str, Any], target_dir: Path) -> Dict[str, str]:
    from src.c_aggregator.csv_exporter import export_diff_to_files as fn
    return fn(stats, target_dir)


def format_novas_instituicoes_table(novos: List[Dict[str, Any]]) -> str:
    from src.c_aggregator.csv_exporter import format_novas_instituicoes_table as fn
    return fn(novos)


def generate_text_diagnosis_c(stats: Dict[str, Any]) -> str:
    from src.c_aggregator.csv_exporter import generate_text_diagnosis_c as fn
    return fn(stats)
