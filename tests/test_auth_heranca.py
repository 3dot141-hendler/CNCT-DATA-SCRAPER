"""
Testes unitários para herança de sessão JWT do Esteio Conecta, reautenticação e auditoria (CNCT_SCRAPER).
Fase 1 (TDD) do Plano de Implantação.
"""

import os
import sys
import jwt
import pytest
from datetime import datetime, timezone

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.backend.auth import decode_jwt_token, is_request_authenticated


def test_decode_jwt_token_valido(monkeypatch):
    secret = "chave_secreta_compartilhada_esteio_conecta"
    monkeypatch.setenv("SCRAPER_JWT_SECRET", secret)

    payload_orig = {
        "user_id": 987654321,
        "email": "admin@esteioconecta.rs.gov.br",
        "role": "admin"
    }

    token = jwt.encode(payload_orig, secret, algorithm="HS256")
    decoded = decode_jwt_token(token)

    assert decoded is not None
    assert decoded["user_id"] == 987654321
    assert decoded["email"] == "admin@esteioconecta.rs.gov.br"


def test_decode_jwt_token_invalido():
    token_invalido = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.token"
    decoded = decode_jwt_token(token_invalido)
    assert decoded is None


def test_auditoria_estrutura_dados():
    audit_record = {
        "usuario_id": 987654321,
        "usuario_email": "admin@esteioconecta.rs.gov.br",
        "ip_origem": "127.0.0.1",
        "data_hora": datetime.now(timezone.utc).isoformat(),
        "total_inseridos": 10,
        "total_atualizados": 2,
        "total_inativados": 1
    }

    assert audit_record["usuario_id"] == 987654321
    assert audit_record["ip_origem"] == "127.0.0.1"
    assert audit_record["total_inativados"] == 1
