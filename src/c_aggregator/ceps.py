"""
Submódulo dedicado exclusivamente para o parsing, extração e validação de CEPs brasileiros (5 a 8 dígitos).
Encapsulado na Classe POO CepExtractor.
"""

import re
from typing import Tuple, Optional


class CepExtractor:
    """
    Classe hiperespecializada para extração e manipulação de CEPs residuais ou formatados em textos brutos.
    """

    @classmethod
    def extract(cls, raw_text: str) -> Tuple[Optional[str], str]:
        """
        Extrai CEP de 5 a 8 dígitos (com ou sem pontos/hífens/sufixos) do final ou do corpo da string
        e retorna uma tupla `(cep_encontrado, texto_limpo_sem_cep)`.
        Ex: 'Pedreiras MA - 65.72500' -> ('6572500', 'Pedreiras MA')
        Ex: 'Cuiabá MT - 78005-' -> ('78005', 'Cuiabá MT')
        """
        if not raw_text:
            return None, ""

        txt = raw_text.strip().strip('.,;- ')
        cep_digits = None

        # 1. Remoção inicial de pontuações residuais no final da string
        txt = re.sub(r'[\s,/|-]+$', '', txt).strip()

        # 2. Extração de CEP no final do texto (suporta CEPs como 65.72500, 78005-, 2863008, 25515)
        cep_match = re.search(r'(?:[-\s,/|-]+)(?:CEP\s*:?\s*)?(\d{2}\.\d{3}[-\.]?\d{2,3}|\d{5}[-\.]?\d{1,3}|\d{5,8})\s*[-.]*$', txt, re.IGNORECASE)
        if cep_match:
            digits = re.sub(r'\D', '', cep_match.group(1))
            if len(digits) >= 5:
                cep_digits = digits
                txt = txt[:cep_match.start()].strip()

        # 3. Expurgo final de CEPs residuais soltos em qualquer lugar do texto
        txt = re.sub(r'\b\d{2}\.\d{3}[-\.]?\d{2,3}\b|\b\d{5}-?\d{1,3}\b', '', txt).strip().strip('.,;- ')
        txt = re.sub(r'[\s,/|-]+$', '', txt).strip()

        return cep_digits, txt

    @classmethod
    def format_cep(cls, cep_digits: Optional[str]) -> str:
        """
        Formata um CEP de 8 dígitos para o padrão clássico '#####-###'.
        """
        if not cep_digits:
            return ""
        clean = re.sub(r'\D', '', str(cep_digits))
        if len(clean) == 8:
            return f"{clean[:5]}-{clean[5:]}"
        return clean

    @classmethod
    def is_valid_cep(cls, cep_str: Optional[str]) -> bool:
        """
        Verifica se a string representa um CEP válido.
        """
        if not cep_str:
            return False
        clean = re.sub(r'\D', '', str(cep_str))
        return 5 <= len(clean) <= 8
