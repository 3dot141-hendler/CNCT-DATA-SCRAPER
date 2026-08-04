"""
Testes de integracao para as rotas FastAPI do backend com suporte a Autenticacao JWT.
"""

import pytest
import jwt
from fastapi.testclient import TestClient
from src.backend.app import app
from src.backend.config import SCRAPER_JWT_SECRET, COOKIE_NAME

client = TestClient(app)

def create_valid_token() -> str:
    return jwt.encode({"sub": "esteio_conecta_test", "role": "admin"}, SCRAPER_JWT_SECRET, algorithm="HS256")

def create_invalid_token() -> str:
    return jwt.encode({"sub": "invalid"}, "wrong_secret_key", algorithm="HS256")


def test_read_root_unauthenticated():
    response = client.get("/")
    assert response.status_code == 403
    assert "Acesso Negado" in response.text


def test_read_root_invalid_token():
    invalid_token = create_invalid_token()
    response = client.get(f"/?token={invalid_token}")
    assert response.status_code == 403
    assert "Acesso Negado" in response.text


def test_read_root_authenticated_query_token():
    valid_token = create_valid_token()
    response = client.get(f"/?token={valid_token}")
    assert response.status_code == 200
    assert COOKIE_NAME in response.cookies


def test_read_root_authenticated_cookie():
    valid_token = create_valid_token()
    client.cookies.set(COOKIE_NAME, valid_token)
    response = client.get("/")
    assert response.status_code == 200


def test_api_unauthenticated_forbidden():
    # Limpa cookies para simular usuario anonimo
    client.cookies.clear()
    response = client.get("/api/scraper/status")
    assert response.status_code == 403


def test_api_authenticated():
    valid_token = create_valid_token()
    client.cookies.set(COOKIE_NAME, valid_token)
    
    response = client.get("/api/scraper/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_running" in data


def test_iframe_security_headers():
    valid_token = create_valid_token()
    response = client.get(f"/?token={valid_token}")
    assert response.status_code == 200
    assert "content-security-policy" in response.headers
    assert "frame-ancestors" in response.headers["content-security-policy"]
    assert "x-frame-options" not in response.headers


def test_download_invalid_file_authenticated():
    valid_token = create_valid_token()
    client.cookies.set(COOKIE_NAME, valid_token)
    response = client.get("/api/data/download/invalid.csv")
    assert response.status_code == 400
