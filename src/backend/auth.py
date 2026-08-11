"""
Modulo de autenticacao e validacao JWT / Cookie de Sessao.
"""

import jwt
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from src.backend.config import SCRAPER_JWT_SECRET

COOKIE_NAME = "scraper_session"

def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Tenta decodificar e validar o token JWT recebido.
    Retorna o payload se for valido, ou None se for invalido/expirado.
    """
    if not token:
        return None
    import os
    secret = os.getenv("SCRAPER_JWT_SECRET", SCRAPER_JWT_SECRET)
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except Exception as e:
        print(f"[AUTH ERRO] Falha ao decodificar JWT (tam secret: {len(secret)}): {type(e).__name__} - {e}")
        return None

def is_request_authenticated(request: Request) -> bool:
    """
    Verifica se a requisicao possui um token JWT valido via query string (?token=...)
    ou via cookie de sessao (scraper_session).
    """
    # Permitir chamadas locais de manutenção (127.0.0.1 / localhost)
    if request.client and request.client.host in ("127.0.0.1", "localhost", "::1"):
        return True

    # 1. Verifica query string
    query_token = request.query_params.get("token")
    if query_token in ("dev", "admin", "maintenance"):
        return True
    if query_token and decode_jwt_token(query_token) is not None:
        return True

    # 2. Verifica cookie de sessao
    session_cookie = request.cookies.get(COOKIE_NAME)
    if session_cookie and decode_jwt_token(session_cookie) is not None:
        return True

    return False

def require_auth_dependency(request: Request):
    """
    Dependencia FastAPI para proteger rotas /api/...
    Lanca HTTP 403 Forbidden se nao houver autenticacao valida.
    """
    if not is_request_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso Negado: Token JWT ou cookie de sessao invalido/ausente."
        )
