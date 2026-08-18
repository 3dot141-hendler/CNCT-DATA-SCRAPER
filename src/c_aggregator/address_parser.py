"""
Submódulo para parsing, sanitização e decomposição de textos estruturados de endereços brasileiros.
Encapsulado na Classe POO AddressParser.
"""

import re
import unicodedata
from typing import Dict, Any, Optional, List, Tuple
from src.c_aggregator.ceps import CepExtractor
from src.c_aggregator.numerais_romanos import RomanNumeralProtector


class AddressParser:
    """
    Classe utilitária para parsing, sanitização e decomposição de endereços brasileiros.
    Delegador para CepExtractor e RomanNumeralProtector.
    """

    INVALID_MUNI_PREFIXES = (
        "rua", "avenida", "av", "travessa", "trv", "praça", "pça", "alameda", "rodovia", "rod",
        "quadra", "qda", "setor", "st", "lote", "lt", "bloco", "bl", "apartamento", "apto",
        "sala", "sl", "sn", "s/n", "centro", "bairro", "distrito", "parque", "pq",
        "km", "nº", "no", "n"
    )

    INVALID_JARDIM_NEIGHBORHOODS = {
        "jardim america", "jardim botanico", "jardim paulista", "jardim eldorado",
        "jardim iguacu", "jardim europa", "jardim alvorada", "jardim primavera",
        "jardim esperanca", "jardim sao paulo", "jardim da penha", "jardim novo",
        "jardim lindo", "jardim belo", "jardim das flores", "jardim dos ipes",
        "jd america", "jd botanico", "jd paulista", "jd eldorado", "jd iguacu"
    }

    VALID_UFS = {
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
        "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
    }

    @staticmethod
    def clean_text_accents(text: str) -> str:
        """
        Remove acentos, converte para minúsculas e remove pontuações.
        """
        if not text:
            return ""
        nfkd = unicodedata.normalize('NFKD', str(text).lower().strip())
        no_accents = "".join([c for c in nfkd if not unicodedata.combining(c)])
        return re.sub(r'[^a-z0-9\s]', ' ', no_accents)

    @staticmethod
    def clean_deduplicate_address(raw_address: str) -> str:
        """
        Higieniza o texto bruto de endereço raspado do CNCT.
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

    @classmethod
    def is_valid_municipio_candidate(cls, candidate: Optional[str]) -> bool:
        """
        Verifica se uma string candidata a município é válida.
        """
        if not candidate:
            return False
        cand_str = candidate.strip().lower()
        cand_str = re.sub(r'\s+', ' ', cand_str)
        
        if not cand_str or cand_str in ("não informado", "n/i", "none"):
            return False
        if re.match(r'^\d+$', cand_str):
            return False
        if re.match(r'^(sl|sala|setor|qda|quadra|lote|bloco|apto)\s*[-:]?\s*\d*', cand_str):
            return False
        
        if cand_str in cls.INVALID_JARDIM_NEIGHBORHOODS:
            return False
            
        for pref in cls.INVALID_MUNI_PREFIXES:
            if cand_str == pref or cand_str.startswith(pref + " ") or cand_str.startswith(pref + "."):
                return False
        return True

    @classmethod
    def normalize_muni_name(cls, muni: str) -> str:
        """
        Normaliza nomes de municípios brasileiros tornando-os imunes a variações.
        """
        if not muni:
            return ""
        txt = cls.clean_text_accents(muni)
        
        txt = txt.replace('z', 's').replace('j', 'g').replace('y', 'i')
        txt = re.sub(r'ç|ss', 's', txt)
        txt = re.sub(r'eo$', 'eu', txt)
        txt = re.sub(r'aes$', 'ais', txt)
        
        stop_words = {'de', 'do', 'da', 'dos', 'das', 'e', 'rr', 'am', 'sp', 'mg', 'rs', 'sc', 'ba', 'pa', 'ma', 'se', 'rj', 'ms', 'mt', 'ac', 'al', 'ap', 'ce', 'df', 'es', 'go', 'pb', 'pr', 'pe', 'pi', 'ro', 'rn', 'to'}
        words = [w for w in txt.split() if w not in stop_words and not w.isdigit()]
        return re.sub(r'[^a-z]', '', "".join(words))

    @classmethod
    def extract_muni_uf_cep(cls, muni_raw: Optional[str]) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Decompõe e purifica completamente qualquer string de município contaminada por UF, CEP ou pontuações residuais.
        Ex: 'Cuiabá MT - 78005-' -> ('Cuiabá', 'MT', '78005')
        Ex: 'Pedreiras MA - 65.72500' -> ('Pedreiras', 'MA', '6572500')
        Ex: 'Fortaleza CE -' -> ('Fortaleza', 'CE', None)
        Ex: 'São Lourenço do Sul RS -' -> ('São Lourenço do Sul', 'RS', None)
        """
        if not muni_raw:
            return "", None, None

        txt = str(muni_raw).strip()
        txt = re.sub(r'[\s,/|-]+$', '', txt).strip()

        # 1. Extração de CEP via CepExtractor (com suporte a CEPs pontuados e sufixos com traço)
        cep_digits, txt = CepExtractor.extract(txt)
        txt = re.sub(r'[\s,/|-]+$', '', txt).strip()

        # 2. Extração de UF
        uf_extracted = None
        words = txt.split()
        if len(words) >= 2:
            last_word_upper = words[-1].upper()
            if last_word_upper in cls.VALID_UFS and not RomanNumeralProtector.is_roman_numeral(last_word_upper):
                uf_extracted = last_word_upper
                txt = " ".join(words[:-1]).strip()

        # 3. Limpeza final de traços ou números no início (ex: '0, São Lourenço do Sul')
        txt = re.sub(r'[\s,/|-]+$', '', txt).strip()
        txt = re.sub(r'^\d+\s*,\s*', '', txt).strip()

        return txt, uf_extracted, cep_digits

    @classmethod
    def sanitize_municipio_name(cls, muni: Optional[str]) -> str:
        """
        Higieniza o nome de um município removendo sufixos de UF, CEPs residuais ou traços,
        preservando inviolavelmente numerais romanos (Pedro II, Pio IX) e nomes compostos.
        """
        clean_muni, _, _ = cls.extract_muni_uf_cep(muni)
        return clean_muni

    @classmethod
    def parse(cls, raw_address: str, native_muni: Optional[str] = None, native_uf: Optional[str] = None) -> Dict[str, Any]:
        """
        Decompõe o texto bruto de endereço em colunas estruturadas.
        """
        sanitized_native = cls.sanitize_municipio_name(native_muni) if native_muni else None
        muni_final = sanitized_native if (sanitized_native and cls.is_valid_municipio_candidate(sanitized_native)) else None
        uf_final = native_uf.strip()[:2].upper() if (native_uf and len(native_uf.strip()) >= 2) else None

        if not raw_address or raw_address.strip() == "" or raw_address.strip().lower() == "não informado":
            return {
                "logradouro": None, "numero": None, "complemento": None,
                "bairro": None, "municipio": muni_final, "uf": uf_final, "cep": None
            }

        raw = cls.clean_deduplicate_address(raw_address.strip().strip('.,;- '))

        # Extração de CEP via CepExtractor
        cep, raw = CepExtractor.extract(raw)
        uf = uf_final

        # Extração de UF
        if not uf:
            uf_match = re.search(r'(?:[\s,/|-]+)([A-Z]{2})\b\s*[-:]?$', raw, re.IGNORECASE)
            if uf_match:
                possible_uf = uf_match.group(1).upper()
                if possible_uf in cls.VALID_UFS and not RomanNumeralProtector.is_roman_numeral(possible_uf):
                    uf = possible_uf
                    raw = raw[:uf_match.start()].strip().strip('.,;- ')

        if not uf:
            words_raw = raw.split()
            if len(words_raw) >= 2:
                last_w = words_raw[-1].upper()
                if last_w in cls.VALID_UFS and not RomanNumeralProtector.is_roman_numeral(last_w):
                    uf = last_w
                    raw = " ".join(words_raw[:-1]).strip().strip('.,;- ')

        words_raw = raw.split()
        if len(words_raw) >= 2:
            last_w = words_raw[-1].upper()
            if last_w in cls.VALID_UFS and not RomanNumeralProtector.is_roman_numeral(last_w):
                raw = " ".join(words_raw[:-1]).strip().strip('.,;- ')

        partes = [p.strip() for p in raw.split(',') if p.strip()]

        logradouro = None
        numero = None
        complemento = None
        bairro = None
        municipio_extracted = None

        if partes:
            for p in reversed(partes):
                p_clean = cls.sanitize_municipio_name(p)
                if cls.is_valid_municipio_candidate(p_clean):
                    municipio_extracted = p_clean
                    break

        if municipio_extracted:
            muni_final = RomanNumeralProtector.protect_municipio_name(muni_final, municipio_extracted)

        if partes and muni_final:
            last_clean = cls.sanitize_municipio_name(cls.clean_text_accents(partes[-1]))
            target_muni_clean = cls.sanitize_municipio_name(cls.clean_text_accents(muni_final))
            if last_clean == target_muni_clean or target_muni_clean.startswith(last_clean):
                partes.pop()

        if len(partes) == 1:
            logradouro = partes[0]
        elif len(partes) == 2:
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
            "municipio": muni_final,
            "uf": uf,
            "cep": cep
        }


# Delegadores de nível de módulo para retrocompatibilidade
INVALID_MUNI_PREFIXES = AddressParser.INVALID_MUNI_PREFIXES
clean_text_accents = AddressParser.clean_text_accents
clean_deduplicate_address = AddressParser.clean_deduplicate_address
is_valid_municipio_candidate = AddressParser.is_valid_municipio_candidate
normalize_muni_name = AddressParser.normalize_muni_name
sanitize_municipio_name = AddressParser.sanitize_municipio_name
extract_muni_uf_cep = AddressParser.extract_muni_uf_cep
parse_address_c = AddressParser.parse
