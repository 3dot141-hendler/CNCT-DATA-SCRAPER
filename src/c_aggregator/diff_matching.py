"""
Submódulo do Motor de Comparação Multi-Nível (Diff Engine) para os 4 estados de instituições e ofertas.
Encapsulado na Classe POO DiffEngine.
"""

from typing import List, Dict, Any, Optional
from src.c_aggregator.address_parser import (
    parse_address_c,
    clean_deduplicate_address,
    normalize_muni_name,
    clean_text_accents,
    sanitize_municipio_name,
    extract_muni_uf_cep
)
from src.c_aggregator.text_normalizer import (
    normalize_core_name,
    normalize_natural_key,
    expand_abbreviations,
    extract_location_keys,
    calculate_name_richness_score
)
from src.c_aggregator.post_diff_audit import run_post_diff_audit_c


class DiffEngine:
    """
    Motor de comparação em 7 Níveis (Tiers) para determinar alterações cadastrais, novos, inativados e mantidos.
    """

    @staticmethod
    def _extract_name_tokens(name_clean: str) -> str:
        words = sorted(w for w in name_clean.split() if len(w) >= 3 and w not in ('escola', 'estadual', 'municipal', 'tecnica', 'profissional', 'educacao', 'centro', 'instituto'))
        return "_".join(words)

    @classmethod
    def compare(cls, db_data: List[Dict[str, Any]], csv_data: List[Dict[str, Any]], is_parcial: Optional[bool] = None) -> Dict[str, Any]:
        """
        Compara o estado do banco MySQL contra a nova carga do CSV.
        """
        db_items_list = []
        
        db_by_full_key = {}
        db_by_core_muni_uf = {}
        db_by_core_uf = {}
        db_by_tokens_uf = {}
        db_by_cep_num = {}
        db_by_street_num = {}

        # 1. Pré-computação de Índices Hash em O(1)
        for item in db_data:
            nome = item.get('nome_instituicao') or item.get('nome') or ""
            muni_raw = item.get('municipio') or ""
            muni_clean, ext_uf, ext_cep = extract_muni_uf_cep(muni_raw)
            uf = item.get('uf') or ext_uf or ""
            end = item.get('endereco') or ""
            
            if (not muni_clean or not uf) and end:
                parsed = parse_address_c(end, native_muni=muni_clean, native_uf=uf)
                if not muni_clean: muni_clean = sanitize_municipio_name(parsed.get('municipio') or "")
                if not uf: uf = parsed.get('uf') or ""
                
            muni_norm = normalize_muni_name(muni_clean)
            core_name = normalize_core_name(nome)
            full_key = normalize_natural_key(nome, muni_clean, uf)
            name_clean = expand_abbreviations(nome)
            tokens_key = cls._extract_name_tokens(name_clean)
            uf_clean = clean_text_accents(uf).upper()[:2]
            cep_val, num_val, logr_val = extract_location_keys(end, muni_clean, uf_clean)
            if not cep_val and ext_cep:
                cep_val = ext_cep
            
            ativo_val = 1 if (item.get('ativo') == 1 or item.get('ativo') == '1' or item.get('ativo') is None) else 0

            entry = {
                'db_item': item,
                'id': item.get('id') or item.get('snowflake_id'),
                'nome': nome,
                'muni': muni_clean,
                'uf': uf_clean,
                'end': end,
                'muni_norm': muni_norm,
                'core_name': core_name,
                'full_key': full_key,
                'name_clean': name_clean,
                'tokens_key': tokens_key,
                'cep_val': cep_val,
                'num_val': num_val,
                'logr_val': logr_val,
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

            if cep_val and num_val and uf_clean:
                cep_key = f"{cep_val}_{num_val}_{uf_clean}"
                db_by_cep_num.setdefault(cep_key, []).append(entry)

            if logr_val and num_val and muni_norm and uf_clean:
                street_key = f"{logr_val}_{num_val}_{muni_norm}_{uf_clean}"
                db_by_street_num.setdefault(street_key, []).append(entry)

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
            c_nome = (csv_item.get('nome_instituicao') or csv_item.get('nome') or "").strip()
            c_end = (csv_item.get('endereco') or csv_item.get('endereco_original') or "").strip()
            
            if (not c_nome or c_nome.lower() in ('sem nome', 'não informado', 'n/i', 'none')) and (not c_end or c_end.lower() in ('não informado', 'n/i', 'none', '')):
                continue
            
            c_muni_raw = (csv_item.get('municipio') or csv_item.get('cidade') or "").strip()
            c_muni_clean, ext_uf_c, ext_cep_c = extract_muni_uf_cep(c_muni_raw)
            c_uf = (csv_item.get('uf') or ext_uf_c or "").strip()
            
            if c_end:
                parsed_c = parse_address_c(c_end, native_muni=c_muni_clean, native_uf=c_uf)
                parsed_muni = parsed_c.get('municipio')
                if parsed_muni:
                    norm_parsed = clean_text_accents(parsed_muni)
                    norm_muni = clean_text_accents(c_muni_clean)
                    if not c_muni_clean or len(norm_parsed) > len(norm_muni) or norm_parsed.startswith(norm_muni):
                        c_muni_clean = parsed_muni
                if not c_uf: c_uf = parsed_c.get('uf') or ""

            c_muni_norm = normalize_muni_name(c_muni_clean)
            c_core_name = normalize_core_name(c_nome)
            c_full_key = normalize_natural_key(c_nome, c_muni_clean, c_uf)
            c_name_clean = expand_abbreviations(c_nome)
            c_tokens_key = cls._extract_name_tokens(c_name_clean)
            c_uf_clean = clean_text_accents(c_uf).upper()[:2]

            matched_entry = None

            # Nível 1: Chave Natural Exata
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

            # Nível 3: Núcleo do Nome + UF
            if not matched_entry and c_core_name and len(c_core_name) >= 5 and c_uf_clean:
                key_lvl3 = f"{c_core_name}_{c_uf_clean}"
                if key_lvl3 in db_by_core_uf:
                    candidates = [cand for cand in db_by_core_uf[key_lvl3] if id(cand['db_item']) not in matched_db_objects]
                    if len(candidates) == 1:
                        matched_entry = candidates[0]

            # Nível 4: Bag of Words + UF
            if not matched_entry and c_tokens_key and len(c_tokens_key) >= 6 and c_uf_clean:
                key_lvl4 = f"{c_tokens_key}_{c_uf_clean}"
                if key_lvl4 in db_by_tokens_uf:
                    candidates = [cand for cand in db_by_tokens_uf[key_lvl4] if id(cand['db_item']) not in matched_db_objects]
                    if len(candidates) == 1:
                        matched_entry = candidates[0]

            # Nível 5: Localização Física por CEP + Número + UF
            c_cep_val, c_num_val, c_logr_val = extract_location_keys(c_end, c_muni_clean, c_uf_clean)
            if not c_cep_val and ext_cep_c:
                c_cep_val = ext_cep_c

            if not matched_entry and c_cep_val and c_num_val and c_uf_clean:
                key_lvl5 = f"{c_cep_val}_{c_num_val}_{c_uf_clean}"
                if key_lvl5 in db_by_cep_num:
                    candidates = [cand for cand in db_by_cep_num[key_lvl5] if id(cand['db_item']) not in matched_db_objects]
                    if len(candidates) >= 1:
                        matched_entry = candidates[0]

            # Nível 6: Localização Física por Logradouro + Número + Município + UF
            if not matched_entry and c_logr_val and c_num_val and c_muni_norm and c_uf_clean:
                key_lvl6 = f"{c_logr_val}_{c_num_val}_{c_muni_norm}_{c_uf_clean}"
                if key_lvl6 in db_by_street_num:
                    candidates = [cand for cand in db_by_street_num[key_lvl6] if id(cand['db_item']) not in matched_db_objects]
                    if len(candidates) >= 1:
                        matched_entry = candidates[0]

            # Nível 7 (Fallback Duplicatas MEC)
            if not matched_entry:
                if c_full_key and c_full_key in db_by_full_key:
                    matched_entry = db_by_full_key[c_full_key][0]
                elif c_core_name and c_muni_norm and c_uf_clean:
                    key_lvl2 = f"{c_core_name}_{c_muni_norm}_{c_uf_clean}"
                    if key_lvl2 in db_by_core_muni_uf:
                        matched_entry = db_by_core_muni_uf[key_lvl2][0]
                elif c_cep_val and c_num_val and c_uf_clean:
                    key_lvl5 = f"{c_cep_val}_{c_num_val}_{c_uf_clean}"
                    if key_lvl5 in db_by_cep_num:
                        matched_entry = db_by_cep_num[key_lvl5][0]

            cursos_item = csv_item.get('cursos', []) or []
            for c in cursos_item:
                cursos_unicos_csv.add(str(c))

            if not matched_entry:
                csv_item['is_novo'] = True
                csv_item['snowflake_id'] = None
                csv_item['municipio'] = c_muni_clean
                csv_item['uf'] = c_uf_clean
                csv_item['cep'] = c_cep_val or csv_item.get('cep')
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
                    csv_item['ativo'] = 1
                    csv_item['reativar'] = True
                    csv_item['municipio'] = c_muni_clean
                    csv_item['uf'] = c_uf_clean
                    csv_item['cep'] = c_cep_val or csv_item.get('cep')
                    reativados.append(csv_item)
                else:
                    end_csv_raw = (c_end).strip()
                    end_csv_clean = clean_deduplicate_address(end_csv_raw)
                    end_db_clean = clean_deduplicate_address((matched_entry['end']).strip())

                    norm_end_csv = clean_text_accents(end_csv_clean)
                    norm_end_db = clean_text_accents(end_db_clean)
                    
                    nome_db_raw = db_obj.get('nome_instituicao') or db_obj.get('nome') or matched_entry['nome']
                    muni_db_raw = db_obj.get('municipio') or db_obj.get('cidade') or matched_entry['muni']
                    db_uf_actual = (db_obj.get('uf') or "").strip()

                    diferencas = []

                    if c_nome and nome_db_raw and clean_text_accents(c_nome) != clean_text_accents(nome_db_raw):
                        score_db = calculate_name_richness_score(nome_db_raw)
                        score_csv = calculate_name_richness_score(c_nome)
                        if score_csv > score_db:
                            diferencas.append(f"nome_instituicao: '{nome_db_raw}' ➔ '{c_nome}'")

                    muni_db_clean, ext_uf_db, ext_cep_db = extract_muni_uf_cep(muni_db_raw)
                    if not c_muni_clean:
                        c_muni_clean = muni_db_clean
                    c_cep = csv_item.get('cep') or c_cep_val or ext_cep_c or ext_cep_db or ""

                    if end_csv_raw:
                        parsed_end_csv = parse_address_c(end_csv_raw, native_muni=c_muni_clean, native_uf=c_uf)
                        if parsed_end_csv.get('municipio'):
                            muni_from_parsed = parsed_end_csv.get('municipio')
                            norm_native = clean_text_accents(c_muni_clean)
                            norm_parsed = clean_text_accents(muni_from_parsed)
                            if norm_native == norm_parsed or (len(norm_native) > len(norm_parsed) and norm_native.startswith(norm_parsed)):
                                pass
                            else:
                                c_muni_clean = muni_from_parsed

                        if parsed_end_csv.get('uf'):
                            c_uf_clean = parsed_end_csv.get('uf')
                        elif not c_uf_clean:
                            c_uf_clean = ext_uf_c or ext_uf_db or ""

                        if parsed_end_csv.get('cep'):
                            c_cep_clean = parsed_end_csv.get('cep')
                        elif not c_cep:
                            c_cep_clean = c_cep
                        else:
                            c_cep_clean = c_cep
                    else:
                        if not c_uf_clean:
                            c_uf_clean = ext_uf_c or ext_uf_db or ""
                        c_cep_clean = c_cep

                    # 1. Divergência de Município
                    if c_muni_clean and (clean_text_accents(c_muni_clean) != clean_text_accents(muni_db_raw)):
                        diferencas.append(f"municipio: '{muni_db_raw}' ➔ '{c_muni_clean}'")

                    # 2. Divergência de UF (Atualiza se a UF mudou, ou se houver outras alterações e a UF do BD estiver em branco)
                    if c_uf_clean:
                        if db_uf_actual and clean_text_accents(c_uf_clean)[:2] != clean_text_accents(db_uf_actual)[:2]:
                            diferencas.append(f"uf: '{db_uf_actual}' ➔ '{c_uf_clean}'")
                        elif not db_uf_actual and diferencas:
                            diferencas.append(f"uf: '' ➔ '{c_uf_clean}'")

                    # 3. Divergência de CEP (Atualiza se o CEP mudou, ou se houver outras alterações e o CEP do BD estiver em branco)
                    cep_db_raw = (matched_entry.get('cep') or "").strip()
                    if c_cep_clean:
                        if cep_db_raw and c_cep_clean != cep_db_raw:
                            diferencas.append(f"cep: '{cep_db_raw}' ➔ '{c_cep_clean}'")
                        elif not cep_db_raw and diferencas:
                            diferencas.append(f"cep: '' ➔ '{c_cep_clean}'")

                    # 4. Divergência de Endereço
                    if norm_end_csv and norm_end_db and norm_end_csv != norm_end_db and len(end_csv_clean) >= int(len(end_db_clean) * 0.80):
                        diferencas.append(f"endereco: '{end_db_clean}' ➔ '{end_csv_clean}'")

                    csv_item['municipio'] = c_muni_clean
                    csv_item['uf'] = c_uf_clean
                    csv_item['cep'] = c_cep_clean

                    if diferencas:
                        csv_item['endereco_db'] = end_db_clean
                        csv_item['endereco'] = end_csv_clean
                        csv_item['diferencas_detectadas'] = diferencas
                        alterados.append(csv_item)
                    else:
                        mantidos.append(csv_item)

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

        inativados = []
        if not is_parcial_detected:
            for entry in db_items_list:
                if id(entry['db_item']) not in matched_db_objects:
                    if entry['ativo'] == 1:
                        item_copy = dict(entry['db_item'])
                        item_copy['ativo'] = 0
                        inativados.append(item_copy)

        # Executa a Esteira de Auditoria Automática Pós-Diff em 3 Passos
        novos, alterados = run_post_diff_audit_c(novos, alterados, db_items_list, mantidos)

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


# Delegador de nível de módulo para retrocompatibilidade
compare_datasets_c = DiffEngine.compare
