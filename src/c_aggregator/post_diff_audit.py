"""
Submódulo para a Esteira de Auditoria Automática Pós-Diff (Double Net Audit).
Encapsulado na Classe POO PostDiffAuditor.
"""

from typing import List, Dict, Any, Tuple, Optional
from src.c_aggregator.address_parser import clean_text_accents, normalize_muni_name, clean_deduplicate_address, sanitize_municipio_name, parse_address_c, extract_muni_uf_cep
from src.c_aggregator.text_normalizer import extract_location_keys, has_ead_indicator, calculate_name_richness_score


class PostDiffAuditor:
    """
    Esteira de Auditoria Pós-Diff em 3 passos para reclassificar candidatos a NOVOS contra a VPS.
    """

    GENERIC_WORDS = {
        'escola', 'estadual', 'municipal', 'tecnica', 'profissional', 'educacao', 'centro',
        'instituto', 'colegio', 'unidade', 'campus', 'curso', 'cursos', 'faculdade',
        'universidade', 'sistema', 'ensino', 'tecnologico', 'integrado', 'polo', 'geral',
        'rede', 'nacional', 'distrito', 'servico', 'social', 'aprendizagem', 'industrial',
        'comercio', 'fundacao', 'associacao', 'complexo', 'grupo', 'nucleo'
    }

    @classmethod
    def audit(cls, novos: List[Dict[str, Any]], alterados: List[Dict[str, Any]], db_items_list: List[Dict[str, Any]], mantidos: Optional[List[Dict[str, Any]]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Executa a esteira de Auditoria Pós-Diff em 3 passos.
        """
        filtered_novos = []

        for csv_novo in novos:
            n_nome = (csv_novo.get('nome_instituicao') or csv_novo.get('nome') or "").strip()
            n_end = (csv_novo.get('endereco') or csv_novo.get('endereco_original') or "").strip()
            n_muni = (csv_novo.get('municipio') or csv_novo.get('cidade') or "").strip()
            n_uf = clean_text_accents(csv_novo.get('uf') or "").upper()[:2]
            n_dep = clean_text_accents(str(csv_novo.get('dependencia_adm') or csv_novo.get('dependencia') or "")).lower()
            n_is_ead = has_ead_indicator(n_nome)
            
            n_cep, n_num, n_logr = extract_location_keys(n_end, n_muni, n_uf)
            n_muni_norm = normalize_muni_name(n_muni)
            
            name_words = set(w for w in clean_text_accents(n_nome.lower()).split() 
                             if len(w) >= 4 and w not in cls.GENERIC_WORDS and w != n_muni_norm and not n_muni_norm.startswith(w))
            
            matched_audit_db = None
            match_reason = ""
            
            for entry in db_items_list:
                db_obj = entry['db_item']
                db_uf = entry['uf']
                db_dep = clean_text_accents(str(db_obj.get('dependencia_adm') or db_obj.get('dependencia') or "")).lower()
                db_nome = entry['nome']
                db_is_ead = has_ead_indicator(db_nome)

                # Trava 1: UF incompatível
                if n_uf and db_uf and n_uf != db_uf:
                    continue

                # Trava 2: Dependência Administrativa Incompatível (Pública vs Privada)
                if n_dep and db_dep:
                    n_is_pub = ("publica" in n_dep or "federal" in n_dep or "estadual" in n_dep or "municipal" in n_dep)
                    db_is_pub = ("publica" in db_dep or "federal" in db_dep or "estadual" in db_dep or "municipal" in db_dep)
                    if n_is_pub != db_is_pub:
                        continue

                # Trava 3: Modalidade EAD incompatível (EAD vs Presencial)
                if n_is_ead != db_is_ead:
                    continue
                    
                db_muni_norm = entry.get('muni_norm') or ""
                db_cep = entry.get('cep_val') or ""
                db_num = entry.get('num_val') or ""
                db_logr = entry.get('logr_val') or ""
                
                # Passo 1: Busca por CEP de rua + Número do Imóvel
                if n_cep and db_cep and n_cep == db_cep:
                    if n_num and db_num and n_num != db_num:
                        continue
                    matched_audit_db = db_obj
                    match_reason = f"CEP {n_cep} e número {n_num or 'S/N'} coincidentes na VPS"
                    break
                    
                # Passo 2: Busca por Logradouro + Número + Município
                if n_logr and db_logr and n_num and db_num and n_logr == db_logr and n_num == db_num and n_muni_norm == db_muni_norm:
                    matched_audit_db = db_obj
                    match_reason = f"Logradouro '{n_logr}', nº {n_num} em {n_muni} coincidente na VPS"
                    break
                    
                # Passo 3: Busca por Palavras Distintas do Nome no mesmo Município
                if name_words and db_muni_norm == n_muni_norm:
                    db_words = set(w for w in clean_text_accents(db_nome.lower()).split() 
                                  if len(w) >= 4 and w not in cls.GENERIC_WORDS and w != db_muni_norm and not db_muni_norm.startswith(w))
                    common_words = name_words & db_words
                    if len(common_words) >= 2:
                        matched_audit_db = db_obj
                        match_reason = f"Tokens específicos do nome ({', '.join(common_words)}) coincidentes na VPS em {n_muni}"
                        break

            # Passo 4: Busca por Núcleo do Nome Único na VPS (para resgatar itens com município/UF truncados no MEC)
            if not matched_audit_db:
                from src.c_aggregator.text_normalizer import normalize_core_name
                n_core = normalize_core_name(n_nome)
                if n_core and len(n_core) >= 5:
                    same_core_candidates = [e['db_item'] for e in db_items_list if normalize_core_name(e['nome']) == n_core]
                    if len(same_core_candidates) == 1:
                        matched_audit_db = same_core_candidates[0]

            if matched_audit_db:
                db_id = matched_audit_db.get('id') or matched_audit_db.get('snowflake_id')
                csv_novo['is_novo'] = False
                csv_novo['id'] = db_id
                csv_novo['snowflake_id'] = db_id

                # Avalia divergências reais
                diferencas = []
                db_nome_raw = matched_audit_db.get('nome_instituicao') or matched_audit_db.get('nome') or ""
                db_muni_raw = matched_audit_db.get('municipio') or ""
                db_end_raw = matched_audit_db.get('endereco') or ""
                db_uf_raw = (matched_audit_db.get('uf') or "").strip()

                if n_nome and db_nome_raw and clean_text_accents(n_nome) != clean_text_accents(db_nome_raw):
                    score_db = calculate_name_richness_score(db_nome_raw)
                    score_csv = calculate_name_richness_score(n_nome)
                    if score_csv > score_db:
                        diferencas.append(f"nome_instituicao: '{db_nome_raw}' ➔ '{n_nome}'")

                n_muni_clean, ext_uf_n, ext_cep_n = extract_muni_uf_cep(n_muni or db_muni_raw)
                parsed_n = parse_address_c(n_end, native_muni=n_muni_clean, native_uf=n_uf)
                if parsed_n.get('municipio'):
                    muni_from_parsed = parsed_n.get('municipio')
                    norm_native = clean_text_accents(n_muni_clean)
                    norm_parsed = clean_text_accents(muni_from_parsed)
                    if norm_native == norm_parsed or (len(norm_native) > len(norm_parsed) and norm_native.startswith(norm_parsed)):
                        pass
                    else:
                        n_muni_clean = muni_from_parsed

                n_uf_clean = parsed_n.get('uf') or n_uf or ext_uf_n or ""
                n_cep_clean = parsed_n.get('cep') or ext_cep_n or ""

                if n_muni_clean and clean_text_accents(n_muni_clean) != clean_text_accents(db_muni_raw):
                    diferencas.append(f"municipio: '{db_muni_raw}' ➔ '{n_muni_clean}'")

                if n_uf_clean:
                    if db_uf_raw and clean_text_accents(n_uf_clean)[:2] != clean_text_accents(db_uf_raw)[:2]:
                        diferencas.append(f"uf: '{db_uf_raw}' ➔ '{n_uf_clean}'")
                    elif not db_uf_raw and diferencas:
                        diferencas.append(f"uf: '' ➔ '{n_uf_clean}'")

                db_cep_raw = (matched_audit_db.get('cep') or "").strip()
                if n_cep_clean:
                    if db_cep_raw and n_cep_clean != db_cep_raw:
                        diferencas.append(f"cep: '{db_cep_raw}' ➔ '{n_cep_clean}'")
                    elif not db_cep_raw and diferencas:
                        diferencas.append(f"cep: '' ➔ '{n_cep_clean}'")

                norm_end_csv = clean_text_accents(clean_deduplicate_address(n_end))
                norm_end_db = clean_text_accents(clean_deduplicate_address(db_end_raw))
                if norm_end_csv and norm_end_db and norm_end_csv != norm_end_db and len(norm_end_csv) >= int(len(norm_end_db) * 0.80):
                    diferencas.append(f"endereco: '{db_end_raw}' ➔ '{n_end}'")

                csv_novo['municipio'] = n_muni_clean
                csv_novo['uf'] = n_uf_clean
                csv_novo['cep'] = n_cep_clean

                if diferencas:
                    csv_novo['endereco_db'] = db_end_raw
                    csv_novo['diferencas_detectadas'] = diferencas
                    alterados.append(csv_novo)
                else:
                    if mantidos is not None:
                        mantidos.append(csv_novo)
            else:
                filtered_novos.append(csv_novo)

        return filtered_novos, alterados


# Delegador de nível de módulo para retrocompatibilidade
run_post_diff_audit_c = PostDiffAuditor.audit
