"""
Módulo de ponte entre Python e o compilado em C para agregação de Snowflake IDs,
parsing de endereços em colunas estruturadas e comparação de estado (diff engine).
"""

import os
import re
import sys
import csv
import json
import subprocess
import unicodedata
from pathlib import Path
from typing import Dict, List, Any, Optional

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
                parsed = parse_address_c(data["endereco"])
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


# --- NOVAS FUNÇÕES C BRIDGE DO PLANO DE IMPLANTAÇÃO ---

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
    
    rules = [
        (r'\b(ee|e\s*e)\b', 'escola estadual'),
        (r'\b(em|e\s*m)\b', 'escola municipal'),
        (r'\b(esc\s*tec\s*est)\b', 'escola tecnica estadual'),
        (r'\b(esc\s*tec)\b', 'escola tecnica'),
        (r'\besc\b', 'escola'),
        (r'\btec\b', 'tecnica'),
        (r'\best\b', 'estadual'),
        (r'\bprof\b|\bprofa\b', 'professor'),
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
    de preposições (de/do/da/dos/das/e), acentos, hífens, grafias fonéticas (z/s, j/g, y/i, ç/ss)
    e variações ortográficas genéricas de vogais/consoantes (eo/eu, es/is).
    """
    if not muni:
        return ""
    txt = clean_text_accents(muni)
    
    # Tratamento fonético genérico universal para topônimos brasileiros
    txt = txt.replace('z', 's').replace('j', 'g').replace('y', 'i')
    txt = re.sub(r'ç|ss', 's', txt)
    txt = re.sub(r'eo$', 'eu', txt)
    txt = re.sub(r'aes$', 'ais', txt)
    
    # Remove preposições, artigos e siglas de UF grudadas (ex: "São Luiz RR - 6937" -> "São Luiz")
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
        r'\bcolegio\b',
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
    clean = re.sub(r'\b(de poxoreu|de poxoreo|de contagem|do sul|de jacarei|de manaus|assu|acu)\b', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return re.sub(r'[^a-z0-9]', '', clean)


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
    # Expulsa todas as referências a Caixa Postal (ex: Cx. Postal, Cx.postal-119.253, C.P. 123, CEP associado)
    txt = re.sub(r'\b(?:Cx\.?\s*postal|Caixa\s*postal|C\.?\s*P\.?)\s*[-:]?\s*[\d\.\-]*\b(?:\s*CEP\s*[-:]?\s*\d{5}-?\d{3})?', '', txt, flags=re.IGNORECASE)

    # Sanitização preventiva de typos e abreviações em logradouros
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


def parse_address_c(raw_address: str) -> Dict[str, Any]:
    """
    Decompõe o texto bruto de endereço em colunas individuais:
    logradouro, numero, complemento, bairro, municipio, uf, cep.
    """
    if not raw_address or raw_address.strip() == "" or raw_address.strip().lower() == "não informado":
        return {
            "logradouro": None, "numero": None, "complemento": None,
            "bairro": None, "municipio": None, "uf": None, "cep": None
        }

    raw = clean_deduplicate_address(raw_address.strip().strip('.,;- '))

    cep = None
    uf = None

    # 1. Extração robusta de CEP (5 dígitos - 3 dígitos ou 8 dígitos contínuos no final)
    cep_match = re.search(r'(?:-\s*|CEP\s*:?\s*|\s+)(\d{5}-?\d{3})\b', raw, re.IGNORECASE)
    if cep_match:
        cep = cep_match.group(1).replace('-', '')
        raw = raw[:cep_match.start()].strip().strip('.,;- ')

    # 2. Extração robusta de UF (2 letras de estado brasileiro no final do trecho restante)
    uf_match = re.search(r'(?:[\s,/|-]+)([A-Z]{2})\b\s*$', raw, re.IGNORECASE)
    if uf_match:
        possible_uf = uf_match.group(1).upper()
        valid_ufs = {"AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"}
        if possible_uf in valid_ufs:
            uf = possible_uf
            raw = raw[:uf_match.start()].strip().strip('.,;- ')

    # 3. Divisão dos componentes restantes por vírgula
    partes = [p.strip() for p in raw.split(',') if p.strip()]

    logradouro = None
    numero = None
    complemento = None
    bairro = None
    municipio = None

    if partes:
        # A última parte restante após remover CEP e UF é estritamente o MUNICÍPIO
        municipio = partes[-1]

    if len(partes) == 2:
        logradouro = partes[0]
    elif len(partes) == 3:
        logradouro = partes[0]
        numero = partes[1]
    elif len(partes) == 4:
        logradouro = partes[0]
        numero = partes[1]
        bairro = partes[2]
    elif len(partes) >= 5:
        logradouro = partes[0]
        numero = partes[1]
        complemento = partes[2]
        bairro = partes[3]

    return {
        "logradouro": logradouro[:250] if logradouro else None,
        "numero": numero[:250] if numero else None,
        "complemento": complemento[:250] if complemento else None,
        "bairro": bairro[:250] if bairro else None,
        "municipio": municipio[:250] if municipio else None,
        "uf": uf[:2] if uf else None,
        "cep": cep[:10] if cep else None
    }


def compare_datasets_c(db_data: List[Dict[str, Any]], csv_data: List[Dict[str, Any]], is_parcial: Optional[bool] = None) -> Dict[str, Any]:
    """
    Compara o estado do banco MySQL (com registros ativo=1 e ativo=0) contra a nova carga do CSV.
    Aplica as 3 regras universais de estado utilizando algoritmo de hash O(1) multi-nível:
    - Nível 1: Chave Natural Exata (Nome + Município + UF)
    - Nível 2: Núcleo do Nome + Município Normalizado + UF
    - Nível 3: Núcleo do Nome + UF (Identifica instituições únicas na UF mesmo se o município mudou de nome/grafia)
    - Nível 4: Conjunto de Palavras (Bag of Words) + UF (Identifica inversões de ordem como 'Oscar Dias Correia Ministro')
    """
    db_items_list = []
    
    db_by_full_key = {}
    db_by_core_muni_uf = {}
    db_by_core_uf = {}
    db_by_tokens_uf = {}

    def extract_name_tokens(name_clean: str) -> str:
        words = sorted(w for w in name_clean.split() if len(w) >= 3 and w not in ('escola', 'estadual', 'municipal', 'tecnica', 'profissional', 'educacao', 'centro', 'instituto'))
        return "_".join(words)

    # 1. Pré-computação de Índices Hash em O(1) para alta velocidade e pareamento genérico
    for item in db_data:
        nome = item.get('nome_instituicao') or item.get('nome') or ""
        muni = item.get('municipio') or ""
        uf = item.get('uf') or ""
        end = item.get('endereco') or ""
        
        if (not muni or not uf) and end:
            parsed = parse_address_c(end)
            if not muni: muni = parsed.get('municipio') or ""
            if not uf: uf = parsed.get('uf') or ""
            
        muni_norm = normalize_muni_name(muni)
        core_name = normalize_core_name(nome)
        full_key = normalize_natural_key(nome, muni, uf)
        name_clean = expand_abbreviations(nome)
        tokens_key = extract_name_tokens(name_clean)
        uf_clean = clean_text_accents(uf).upper()[:2]
        
        ativo_val = 1 if (item.get('ativo') == 1 or item.get('ativo') == '1' or item.get('ativo') is None) else 0

        entry = {
            'db_item': item,
            'id': item.get('id') or item.get('snowflake_id'),
            'nome': nome,
            'muni': muni,
            'uf': uf_clean,
            'end': end,
            'muni_norm': muni_norm,
            'core_name': core_name,
            'full_key': full_key,
            'name_clean': name_clean,
            'tokens_key': tokens_key,
            'ativo': ativo_val
        }
        db_items_list.append(entry)

        if full_key:
            db_by_full_key.setdefault(full_key, []).append(entry)

        if core_name and muni_norm and uf_clean:
            c_muni_key = f"{core_name}_{muni_norm}_{uf_clean}"
            db_by_core_muni_uf.setdefault(c_muni_key, []).append(entry)

        if core_name and len(core_name) >= 5 and uf_clean:
            c_uf_key = f"{core_name}_{uf_clean}"
            db_by_core_uf.setdefault(c_uf_key, []).append(entry)

        if tokens_key and len(tokens_key) >= 6 and uf_clean:
            t_uf_key = f"{tokens_key}_{uf_clean}"
            db_by_tokens_uf.setdefault(t_uf_key, []).append(entry)

    matched_db_objects = set()
    novos = []
    alterados = []
    mantidos = []
    reativados = []

    novos_cursos_qtd = 0
    cursos_descontinuados_qtd = 0
    cursos_mantidos_qtd = 0

    cursos_unicos_csv = set()
    cursos_detalhes = []

    total_csv = len(csv_data)
    total_db = len(db_data)

    if is_parcial is None:
        is_parcial_detected = (total_db > 0 and total_csv < (total_db * 0.8))
    else:
        is_parcial_detected = is_parcial

    for csv_item in csv_data:
        c_nome = csv_item.get('nome_instituicao') or csv_item.get('nome') or ""
        c_muni = csv_item.get('municipio') or ""
        c_uf = csv_item.get('uf') or ""
        c_end = csv_item.get('endereco') or csv_item.get('endereco_original') or ""
        
        if (not c_muni or not c_uf) and c_end:
            parsed_c = parse_address_c(c_end)
            if not c_muni: c_muni = parsed_c.get('municipio') or ""
            if not c_uf: c_uf = parsed_c.get('uf') or ""

        c_muni_norm = normalize_muni_name(c_muni)
        c_core_name = normalize_core_name(c_nome)
        c_full_key = normalize_natural_key(c_nome, c_muni, c_uf)
        c_name_clean = expand_abbreviations(c_nome)
        c_tokens_key = extract_name_tokens(c_name_clean)
        c_uf_clean = clean_text_accents(c_uf).upper()[:2]

        matched_entry = None

        # Nível 1: Chave Natural Exata (Nome + Município + UF)
        if c_full_key and c_full_key in db_by_full_key:
            for cand in db_by_full_key[c_full_key]:
                if id(cand['db_item']) not in matched_db_objects:
                    matched_entry = cand
                    break

        # Nível 2: Núcleo do Nome + Município Normalizado + UF
        if not matched_entry and c_core_name and c_muni_norm and c_uf_clean:
            key_lvl2 = f"{c_core_name}_{c_muni_norm}_{c_uf_clean}"
            if key_lvl2 in db_by_core_muni_uf:
                for cand in db_by_core_muni_uf[key_lvl2]:
                    if id(cand['db_item']) not in matched_db_objects:
                        matched_entry = cand
                        break

        # Nível 3: Núcleo do Nome + UF (Identifica mudança de nome de município ou variação de grafia na cidade)
        if not matched_entry and c_core_name and len(c_core_name) >= 5 and c_uf_clean:
            key_lvl3 = f"{c_core_name}_{c_uf_clean}"
            if key_lvl3 in db_by_core_uf:
                candidates = [cand for cand in db_by_core_uf[key_lvl3] if id(cand['db_item']) not in matched_db_objects]
                if len(candidates) == 1:
                    # Match único e inequívoco no Estado!
                    matched_entry = candidates[0]

        # Nível 4: Conjunto de Palavras (Bag of Words) + UF (Identifica inversões de ordem nos títulos)
        if not matched_entry and c_tokens_key and len(c_tokens_key) >= 6 and c_uf_clean:
            key_lvl4 = f"{c_tokens_key}_{c_uf_clean}"
            if key_lvl4 in db_by_tokens_uf:
                candidates = [cand for cand in db_by_tokens_uf[key_lvl4] if id(cand['db_item']) not in matched_db_objects]
                if len(candidates) == 1:
                    matched_entry = candidates[0]

        # Coleta cursos únicos da carga
        cursos_item = csv_item.get('cursos', []) or []
        for c in cursos_item:
            cursos_unicos_csv.add(str(c))

        if not matched_entry:
            # Não tem na VPS, tem na raspagem -> NOVA INSTITUIÇÃO
            csv_item['is_novo'] = True
            csv_item['snowflake_id'] = None
            novos.append(csv_item)
            novos_cursos_qtd += len(cursos_item)
        else:
            db_obj = matched_entry['db_item']
            db_id = db_obj.get('id') or db_obj.get('snowflake_id')
            csv_item['is_novo'] = False
            csv_item['id'] = db_id
            csv_item['snowflake_id'] = db_id
            matched_db_objects.add(id(db_obj))

            if matched_entry['ativo'] == 0:
                # Tinha no banco com ativo = 0, tem na raspagem -> REATIVAR (setar ativo = 1)
                csv_item['ativo'] = 1
                csv_item['reativar'] = True
                reativados.append(csv_item)
            else:
                # Tinha no banco com ativo = 1, tem na raspagem -> MANTIDO ou ALTERADO
                end_csv_raw = (c_end).strip()
                end_csv_clean = clean_deduplicate_address(end_csv_raw)
                end_db_clean = clean_deduplicate_address((matched_entry['end']).strip())

                norm_end_csv = clean_text_accents(end_csv_clean)
                norm_end_db = clean_text_accents(end_db_clean)
                
                nome_db_raw = matched_entry['nome']
                muni_db_raw = matched_entry['muni']
                uf_db_raw = matched_entry['uf']

                diferencas = []

                # 1. Checa divergência de nome (ex: nome truncado ou ordem de palavras)
                if c_nome and nome_db_raw and clean_text_accents(c_nome) != clean_text_accents(nome_db_raw):
                    diferencas.append(f"nome_instituicao: '{nome_db_raw}' ➔ '{c_nome}'")

                # 2. Checa divergência de município (ex: 'Augusto Severo' -> 'Campo Grande', 'Trajano de Morais' -> 'Trajano de Moraes')
                if c_muni and muni_db_raw and clean_text_accents(c_muni) != clean_text_accents(muni_db_raw):
                    diferencas.append(f"municipio: '{muni_db_raw}' ➔ '{c_muni}'")

                # 3. Checa divergência de UF
                if c_uf and uf_db_raw and clean_text_accents(c_uf)[:2] != clean_text_accents(uf_db_raw)[:2]:
                    diferencas.append(f"uf: '{uf_db_raw}' ➔ '{c_uf}'")

                # 4. Checa divergência de endereço
                if norm_end_csv and norm_end_db and norm_end_csv != norm_end_db and len(end_csv_clean) >= int(len(end_db_clean) * 0.80):
                    diferencas.append(f"endereco: '{end_db_clean}' ➔ '{end_csv_clean}'")

                if diferencas:
                    csv_item['endereco_db'] = end_db_clean
                    csv_item['endereco'] = end_csv_clean
                    csv_item['diferencas_detectadas'] = diferencas
                    alterados.append(csv_item)
                else:
                    mantidos.append(csv_item)

            # Comparação dos Cursos Ofertados (Nível 2)
            cursos_csv = set(csv_item.get('cursos', []) or [])
            cursos_db = set(db_obj.get('cursos', []) or [])

            if cursos_csv or cursos_db:
                novos_cursos = cursos_csv - cursos_db
                cursos_fechados = cursos_db - cursos_csv
                mantidos_cursos = cursos_csv & cursos_db

                novos_cursos_qtd += len(novos_cursos)
                cursos_descontinuados_qtd += len(cursos_fechados)
                cursos_mantidos_qtd += len(mantidos_cursos)

                for c_novo in novos_cursos:
                    cursos_detalhes.append({
                        "id": db_id,
                        "nome_instituicao": c_nome,
                        "tipo": "Nova Oferta",
                        "curso": c_novo
                    })

                if not is_parcial_detected:
                    for c_fechado in cursos_fechados:
                        cursos_detalhes.append({
                            "id": db_id,
                            "nome_instituicao": c_nome,
                            "tipo": "Encerrado",
                            "curso": c_fechado
                        })

    # Identifica registros que existem na VPS com ativo = 1 mas NÃO vieram na raspagem
    inativados = []
    if not is_parcial_detected:
        for entry in db_items_list:
            if id(entry['db_item']) not in matched_db_objects:
                if entry['ativo'] == 1:
                    # Tem na VPS (ativo=1), NÃO tem na raspagem -> SETAR ATIVO = 0
                    item_copy = dict(entry['db_item'])
                    item_copy['ativo'] = 0
                    inativados.append(item_copy)

    return {
        "novos": novos,
        "alterados": alterados,
        "inativados": inativados,
        "mantidos": mantidos,
        "reativados": reativados,
        "total_csv": total_csv,
        "total_db": total_db,
        "cursos_unicos_csv_qtd": len(cursos_unicos_csv),
        "cursos_detalhes": cursos_detalhes,
        "is_parcial": is_parcial_detected,
        "estatisticas_cursos": {
            "novos_cursos_qtd": novos_cursos_qtd,
            "cursos_descontinuados_qtd": cursos_descontinuados_qtd if not is_parcial_detected else 0,
            "cursos_mantidos_qtd": cursos_mantidos_qtd
        }
    }


def format_novas_instituicoes_table(novos: List[Dict[str, Any]]) -> str:
    """
    Gera uma tabela formatada em modo texto (ASCII Table) listando as instituicoes novas sem truncamento de endereco.
    """
    if not novos:
        return "Nenhuma nova instituição identificada no lote importado."

    items_show = novos[:50]
    max_end_len = max([len(str(item.get("endereco_original") or item.get("endereco") or item.get("logradouro") or "N/I")) for item in items_show] + [22])
    max_end_len = max(max_end_len, 45)

    border = f"+------------+------------------------------------------+--------------------+{'-' * (max_end_len + 2)}+"
    header = f"| CÓDIGO     | NOME DA INSTITUIÇÃO                      | MUNICÍPIO          | {'ENDEREÇO'.ljust(max_end_len)} |"

    linhas = [border, header, border]

    for item in items_show:
        codigo = str(item.get("snowflake_id") or item.get("id") or item.get("codigo") or "NOVO")[:10].ljust(10)
        nome = str(item.get("nome_instituicao") or item.get("nome") or "Sem nome")[:40].ljust(40)
        muni = str(item.get("municipio") or "N/I")[:18].ljust(18)
        end = str(item.get("endereco_original") or item.get("endereco") or item.get("logradouro") or "N/I").ljust(max_end_len)

        linhas.append(f"| {codigo} | {nome} | {muni} | {end} |")

    linhas.append(border)
    if len(novos) > 50:
        linhas.append(f"  ... e mais {len(novos) - 50} novas instituições no lote.")

    return "\n".join(linhas)


def format_alteracoes_instituicoes_table(alterados: List[Dict[str, Any]]) -> str:
    """
    Gera uma tabela formatada em modo texto destacando os atributos alterados sem truncamento e sem emojis.
    """
    if not alterados:
        return "Nenhuma alteração cadastral detectada em instituições existentes."

    items_show = alterados[:50]
    max_diff_len = max([max([len(str(d)) for d in item.get("diferencas_detectadas", [])] or [50]) for item in items_show] + [50])
    max_diff_len = max(max_diff_len, 60)

    border = f"+------------+------------------------------------------+{'-' * (max_diff_len + 2)}+"
    header = f"| CÓDIGO     | NOME DA INSTITUIÇÃO                      | {'ATRIBUTOS E VALORES ALTERADOS (valorVPS -> valorScraper)'.ljust(max_diff_len)} |"

    linhas = [border, header, border]

    for item in items_show:
        codigo = str(item.get("id") or item.get("snowflake_id") or "N/A")[:10].ljust(10)
        nome = str(item.get("nome_instituicao") or item.get("nome") or "Sem nome")[:40].ljust(40)
        
        diffs = item.get("diferencas_detectadas", [])
        first_diff = diffs[0] if diffs else f"endereco: {item.get('endereco_db', '')} -> {item.get('endereco', '')}"
        first_diff_formatted = first_diff.ljust(max_diff_len)

        linhas.append(f"| {codigo} | {nome} | {first_diff_formatted} |")
        if len(diffs) > 1:
            for extra in diffs[1:]:
                extra_str = f"   [ALTERACAO] {extra}".ljust(max_diff_len)
                linhas.append(f"| {' '*10} | {' '*40} | {extra_str} |")

    linhas.append(border)
    if len(alterados) > 50:
        linhas.append(f"  ... e mais {len(alterados) - 50} instituições com alterações cadastrais.")

    return "\n".join(linhas)


def format_cursos_detalhes_table(cursos_detalhes: List[Dict[str, Any]]) -> str:
    """
    Gera uma tabela formatada em modo texto com os detalhes de inclusao/exclusao de cursos ofertados sem emojis.
    """
    if not cursos_detalhes:
        return "Nenhuma alteração na grade de ofertas de cursos detectada."

    linhas = []
    linhas.append("+------------+------------------------------------------+----------------------+--------------------------------------------------+")
    linhas.append("| CÓDIGO     | NOME DA INSTITUIÇÃO                      | TIPO DE ALTERAÇÃO    | NOME DO CURSO OFERTADO                           |")
    linhas.append("+------------+------------------------------------------+----------------------+--------------------------------------------------+")

    for item in cursos_detalhes[:50]:
        codigo = str(item.get("id") or item.get("snowflake_id") or "N/A")[:10].ljust(10)
        nome = str(item.get("nome_instituicao") or item.get("nome") or "Sem nome")[:40].ljust(40)
        tipo = str(item.get("tipo") or "Alteração").replace("🟢 ", "").replace("🔴 ", "")[:20].ljust(20)
        curso = str(item.get("curso") or "Sem nome")[:48].ljust(48)

        linhas.append(f"| {codigo} | {nome} | {tipo} | {curso} |")

    linhas.append("+------------+------------------------------------------+----------------------+--------------------------------------------------+")
    if len(cursos_detalhes) > 50:
        linhas.append(f"  ... e mais {len(cursos_detalhes) - 50} alterações em ofertas de cursos.")

    return "\n".join(linhas)


def format_inativados_instituicoes_table(inativados: List[Dict[str, Any]]) -> str:
    """
    Gera uma tabela formatada em modo texto listando as instituições que serão inativadas (ativo = 0).
    Exibe o endereço completo sem truncamento.
    """
    if not inativados:
        return "Nenhuma instituição será inativada neste procedimento."

    items_show = inativados[:50]
    max_end_len = max([len(str(item.get("endereco") or item.get("endereco_original") or "N/I")) for item in items_show] + [22])
    max_end_len = max(max_end_len, 45)

    border = f"+------------+------------------------------------------+--------------------+{'-' * (max_end_len + 2)}+"
    header = f"| CÓDIGO     | NOME DA INSTITUIÇÃO (A SER INATIVADA)    | MUNICÍPIO          | {'ENDEREÇO ATUAL (MYSQL)'.ljust(max_end_len)} |"

    linhas = [border, header, border]

    for item in items_show:
        codigo = str(item.get("id") or item.get("snowflake_id") or "N/A")[:10].ljust(10)
        nome = str(item.get("nome_instituicao") or item.get("nome") or "Sem nome")[:40].ljust(40)
        muni = str(item.get("municipio") or "N/I")[:18].ljust(18)
        end = str(item.get("endereco") or item.get("endereco_original") or "N/I").ljust(max_end_len)

        linhas.append(f"| {codigo} | {nome} | {muni} | {end} |")

    linhas.append(border)
    if len(inativados) > 50:
        linhas.append(f"  ... e mais {len(inativados) - 50} instituições marcadas para inativação.")

    return "\n".join(linhas)


def generate_text_diagnosis_c(stats: Dict[str, Any]) -> str:
    """
    Gera o texto de diagnóstico analítico descritivo para auxílio à tomada de decisão sem emojis.
    """
    total_csv = stats.get("total_csv", 0)
    total_db = stats.get("total_db", 0)
    novos_list = stats.get("novos", [])
    alterados_list = stats.get("alterados", [])
    inativados_list = stats.get("inativados", [])
    novos_qtd = stats.get("novos_qtd", len(novos_list))
    alterados_qtd = stats.get("alterados_qtd", len(alterados_list))
    inativados = stats.get("inativados_qtd", len(inativados_list))
    mantidos = stats.get("mantidos_qtd", len(stats.get("mantidos", [])))
    is_parcial = stats.get("is_parcial", False)
    cursos_unicos = stats.get("cursos_unicos_csv_qtd", 0)
    cursos_detalhes_list = stats.get("cursos_detalhes", [])

    est_cursos = stats.get("estatisticas_cursos", {})
    novos_cursos = est_cursos.get("novos_cursos_qtd", 0)
    cursos_desc = est_cursos.get("cursos_descontinuados_qtd", 0)
    cursos_mantidos = est_cursos.get("cursos_mantidos_qtd", 0)

    # Tabelas formatadas
    tabela_novos_texto = format_novas_instituicoes_table(novos_list)
    tabela_alterados_texto = format_alteracoes_instituicoes_table(alterados_list)
    tabela_inativados_texto = format_inativados_instituicoes_table(inativados_list)
    tabela_cursos_texto = format_cursos_detalhes_table(cursos_detalhes_list)

    alerta_parcial = ""
    if is_parcial:
        alerta_parcial = (
            "===================================================================\n"
            "  ATENÇÃO: PESQUISA / RASPAGEM PARCIAL DETECTADA (LOTE REDUZIDO)\n"
            "-------------------------------------------------------------------\n"
            "  • A varredura atual não cobriu a totalidade da base nacional.\n"
            "  • TRAVA DE SEGURANÇA ATIVADA: NENHUM REGISTRO SERÁ INATIVADO (ativo=0).\n"
            "===================================================================\n\n"
        )

    relatorio = (
        alerta_parcial +
        "===================================================================\n"
        "   DIAGNÓSTICO ANALÍTICO DE SINCRONIZAÇÃO (CHAVE NATURAL & OFERTAS)\n"
        "===================================================================\n"
        "ENTIDADE PRINCIPAL (INSTITUIÇÕES DE ENSINO):\n"
        f" -> Total Importado nesta Varredura:          {total_csv}\n"
        f" -> Total Existente no MySQL (VPS):           {total_db}\n"
        f" -> Cursos Únicos Raspados no Lote:           {cursos_unicos}\n"
        "-------------------------------------------------------------------\n"
        f" -> Instituições Novas (A Inserir):              {novos_qtd} (Snowflake IDs gerados no commit)\n"
        f" -> Instituições com Alterações (A Atualizar):  {alterados_qtd} (Mesma Chave Natural)\n"
        f" -> Instituições Mantidas Sem Alteração:      {mantidos}\n"
        f" -> Instituições Inativadas (ativo=0):           {inativados}" + (" [BLOQUEADO POR PESQUISA PARCIAL]" if is_parcial else "") + "\n"
        "-------------------------------------------------------------------\n"
        "ENTIDADE RELACIONADA (CURSOS E OFERTAS - REL_INSTITUICAO_CURSOS):\n"
        f" -> Novas Ofertas de Cursos (Novos Vínculos):   {novos_cursos}\n"
        f" -> Ofertas Descontinuadas / Encerradas:          {cursos_desc} (ativo = 0 no vínculo)\n"
        f" -> Ofertas Mantidas sem Alteração:            {cursos_mantidos}\n"
        "===================================================================\n\n"
        "1. RELAÇÃO DE INSTITUIÇÕES NOVAS IDENTIFICADAS:\n"
        f"{tabela_novos_texto}\n\n"
        "2. COMPARAÇÃO DE ALTERAÇÕES CADASTRAIS (BANCO MYSQL vs RASPAGEM CNCT):\n"
        f"{tabela_alterados_texto}\n\n"
        "3. RELAÇÃO DE INSTITUIÇÕES A SEREM INATIVADAS (ativo = 0):\n"
        f"{tabela_inativados_texto}\n\n"
        "4. DETALHAMENTO DE CURSOS E OFERTAS (NOVOS VÍNCULOS / ENCERRADOS):\n"
        f"{tabela_cursos_texto}\n"
    )

    return relatorio
