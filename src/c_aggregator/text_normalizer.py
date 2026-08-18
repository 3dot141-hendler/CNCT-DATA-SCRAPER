"""
Submódulo para normalização de nomes de instituições, chaves naturais e extração de chaves de localização.
Encapsulado na Classe POO TextNormalizer.
"""

import re
import unicodedata
from typing import Tuple
from src.c_aggregator.address_parser import clean_text_accents, normalize_muni_name, parse_address_c
from src.c_aggregator.numerais_romanos import RomanNumeralProtector


class TextNormalizer:
    """
    Classe utilitária para normalização léxica e geração de chaves determinísticas de comparação.
    """

    ABBREVIATION_RULES = [
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

    PREFIXES = [
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

    SUFFIXES = [
        r'\b(c\s*e[\s\-]*ef\s*m\s*eti\s*prof|c\s*e[\s\-]*ef\s*m\s*profis|c\s*e\s*c\s*m\s*efmp|c\s*e\s*e\s*fund\s*med|e\s*e\s*e\s*fund|ef\s*m\s*eti\s*prof|ef\s*m\s*profis|fund\s*med|ens\s*med|ens\s*fund|eti\s*prof|profis|efmp|eti|ef\s*m|ef|em|mp)\b'
    ]

    @classmethod
    def expand_abbreviations(cls, text: str) -> str:
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

        for pattern, repl in cls.ABBREVIATION_RULES:
            txt = re.sub(pattern, repl, txt)
        
        return re.sub(r'\s+', ' ', txt).strip()

    @staticmethod
    def has_ead_indicator(name: str) -> bool:
        """
        Verifica se a instituição possui indicador explícito de modalidade EAD.
        """
        if not name:
            return False
        norm = clean_text_accents(name.lower())
        return bool(re.search(r'\b(ead|ea d|poloead|distancia)\b|\(ead\)', name.lower()) or "a distancia" in norm)

    @classmethod
    def calculate_richness_score(cls, name: str) -> int:
        """
        Calcula uma pontuação de riqueza léxica de um nome de instituição.
        """
        if not name:
            return 0
        words = [w for w in clean_text_accents(name).split() if len(w) >= 3]
        acronyms_set = {'ce', 'ee', 'em', 'efmp', 'eti', 'profis', 'ef', 'mp', 'eti', 'ead', 'p', 'c', 'm'}
        score = 0
        for w in words:
            if w in acronyms_set:
                score -= 2
            elif len(w) >= 5:
                score += 3
            else:
                score += 1
        return max(score, 0)

    @classmethod
    def normalize_natural_key(cls, nome: str, muni: str, uf: str = "") -> str:
        """
        Gera uma chave determinística normalizada a partir de (nome, município, UF).
        """
        raw_nome = cls.expand_abbreviations(nome)
        raw_muni = normalize_muni_name(muni)
        raw_uf = clean_text_accents(uf).upper()[:2]
        
        ead_tag = "_ead" if cls.has_ead_indicator(nome) else ""
        
        parts = [p for p in [raw_nome, raw_muni, raw_uf] if p]
        raw = "_".join(parts).strip() + ead_tag
        return re.sub(r'[^a-z0-9_]', '', raw)

    @classmethod
    def clean_pedagogical_acronyms(cls, name: str) -> str:
        """
        Delegador para RomanNumeralProtector: remove acrônimos pedagógicos sem afetar numerais romanos.
        """
        return RomanNumeralProtector.clean_pedagogical_acronyms_preserving_romans(name)

    @classmethod
    def normalize_core_name(cls, name: str) -> str:
        """
        Normaliza o nome da instituição removendo prefixos/abreviações institucionais genéricas.
        """
        clean = cls.expand_abbreviations(name)
        for p in cls.PREFIXES:
            clean = re.sub(p, ' ', clean)

        for s in cls.SUFFIXES:
            clean = re.sub(s, ' ', clean)

        clean = re.sub(r'\b(de poxoreu|de poxoreo|de contagem|do sul|de jacarei|de manaus|assu|acu)\b', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return re.sub(r'[^a-z0-9]', '', clean)

    @classmethod
    def extract_location_keys(cls, address_str: str, muni: str, uf: str) -> Tuple[str, str, str]:
        """
        Extrai chave purificada de localização (CEP + número limpo) e (logradouro limpo + número limpo).
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


# Delegadores de nível de módulo para retrocompatibilidade
expand_abbreviations = TextNormalizer.expand_abbreviations
has_ead_indicator = TextNormalizer.has_ead_indicator
calculate_name_richness_score = TextNormalizer.calculate_richness_score
normalize_natural_key = TextNormalizer.normalize_natural_key
clean_pedagogical_acronyms = TextNormalizer.clean_pedagogical_acronyms
normalize_core_name = TextNormalizer.normalize_core_name
extract_location_keys = TextNormalizer.extract_location_keys
