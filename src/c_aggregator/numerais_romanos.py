"""
Submódulo dedicado exclusivamente para o tratamento, validação e preservação dinâmica de numerais romanos
e municípios compostos contra truncamento e mutilação.
Encapsulado na Classe POO RomanNumeralProtector.
"""

import re
import unicodedata
from typing import Optional


class RomanNumeralProtector:
    """
    Classe hiperespecializada para proteção e manipulação dinâmica de numerais romanos
    e municípios compostos (ex: Pedro II, Pio IX, Jardim de Piranhas).
    """

    ROMAN_NUMERALS = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"}

    @staticmethod
    def _clean_accents(text: str) -> str:
        if not text:
            return ""
        nfkd = unicodedata.normalize('NFKD', str(text).lower().strip())
        no_accents = "".join([c for c in nfkd if not unicodedata.combining(c)])
        return re.sub(r'[^a-z0-9\s]', ' ', no_accents)

    @classmethod
    def is_roman_numeral(cls, word: str) -> bool:
        """
        Verifica dinamicamente se uma palavra é um numeral romano válido.
        """
        if not word:
            return False
        return word.strip().upper() in cls.ROMAN_NUMERALS

    @classmethod
    def protect_municipio_name(cls, native_muni: Optional[str], candidate_muni: Optional[str]) -> Optional[str]:
        """
        Garante dinamicamente que municípios nativos contendo numerais romanos (ex: Pedro II, Pio IX)
        ou nomes compostos não sejam truncados por partes extraídas de logradouros (ex: Pedro, Jardim).
        """
        if not native_muni:
            return candidate_muni
        if not candidate_muni:
            return native_muni

        norm_native = cls._clean_accents(native_muni).strip()
        norm_candidate = cls._clean_accents(candidate_muni).strip()

        if norm_native == norm_candidate:
            return native_muni

        # 1. Proteção Dinâmica para numerais romanos no final do município nativo (ex: Pedro II, Pio IX)
        words_native = native_muni.strip().split()
        if len(words_native) >= 2 and cls.is_roman_numeral(words_native[-1]):
            if len(norm_native) > len(norm_candidate) and norm_native.startswith(norm_candidate):
                return native_muni

        # 2. Proteção Dinâmica Geral: se o nome nativo for mais completo e contiver o candidato como prefixo
        if len(norm_native) > len(norm_candidate) and norm_native.startswith(norm_candidate):
            return native_muni

        return candidate_muni

    @classmethod
    def clean_pedagogical_acronyms_preserving_romans(cls, name: str) -> str:
        """
        Remove acrônimos pedagógicos estaduais comuns sem tocar em numerais romanos (I a XX).
        """
        if not name:
            return ""
        cleaned = name.lower()
        cleaned = re.sub(r'[\-\/,]', ' ', cleaned)
        acronyms = [
            r'\befmp\b', r'\beti\b', r'\bprofis\b', r'\bens\s+fund\b', r'\bmedio\b',
            r'\be\s+e\s+e\s+fund\b', r'\bc\s*e\b', r'\be\s*e\b', r'\be\s*e\s*b\b',
            r'\bcm\b', r'\bemp\b', r'\bmp\b'
        ]
        for acr in acronyms:
            cleaned = re.sub(acr, ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cls._clean_accents(cleaned)
