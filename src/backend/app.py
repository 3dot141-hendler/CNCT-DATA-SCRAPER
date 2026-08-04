"""
Aplicacao Backend Principal FastAPI para o CNCT Scraper com Autenticacao JWT, Cookie HttpOnly e Suporte a iFrame.
"""

import sys
import asyncio
from typing import Optional
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Query, status, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from src.backend.config import ALLOWED_ORIGINS, COOKIE_SECURE
from src.backend.auth import COOKIE_NAME, decode_jwt_token, require_auth_dependency
from src.backend.routes.scraper_routes import router as scraper_router
from src.backend.routes.data_routes import router as data_router
from src.backend.websocket_manager import ws_manager

# Correcao da politica de event loop para Windows 11 / Python 3.13 para evitar AssertionError no Proactor
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

app = FastAPI(
    title="CNCT Scraper WebApp API",
    description="Backend modular para raspagem com suporte a autenticacao JWT, Cookies de sessao e embedding via iFrame.",
    version="2.1.0"
)

# 1. Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Middleware de Cabecalhos de Seguranca para iFrame (CSP frame-ancestors & X-Frame-Options)
@app.middleware("http")
async def iframe_security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    # Remove X-Frame-Options padrao para permitir inclusao em iframe
    if "X-Frame-Options" in response.headers:
        del response.headers["X-Frame-Options"]

    # Configura Content-Security-Policy com frame-ancestors para os dominios autorizados
    origins_str = " ".join(ALLOWED_ORIGINS) if ALLOWED_ORIGINS else "*"
    response.headers["Content-Security-Policy"] = f"frame-ancestors 'self' {origins_str};"
    return response

@app.on_event("startup")
async def startup_event():
    """
    Registra o event loop principal no WebSocketManager para transmissao de logs thread-safe.
    """
    loop = asyncio.get_running_loop()
    ws_manager.set_main_loop(loop)

# 3. Incluir rotas modulares protegidas por Autenticacao
app.include_router(scraper_router, dependencies=[Depends(require_auth_dependency)])
app.include_router(data_router, dependencies=[Depends(require_auth_dependency)])

# Montar arquivos estaticos do Frontend
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def read_root(request: Request, token: Optional[str] = Query(None)):
    """
    Serve a pagina principal index.html se autenticado via token JWT (?token=...) ou cookie de sessao.
    Retorna HTTP 403 Forbidden caso contrario.
    """
    valid_token_string = None

    # Tenta validar token da query string
    if token and decode_jwt_token(token) is not None:
        valid_token_string = token
    else:
        # Tenta validar cookie de sessao existente
        session_cookie = request.cookies.get(COOKIE_NAME)
        if session_cookie and decode_jwt_token(session_cookie) is not None:
            valid_token_string = session_cookie

    # Se nao houver autenticacao valida, nega o acesso
    if not valid_token_string:
        forbidden_html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>403 Forbidden - Acesso Negado</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .card { background: #1e293b; padding: 2.5rem 3rem; border-radius: 12px; text-align: center; border: 1px solid #334155; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); }
        h1 { color: #ef4444; font-size: 2.25rem; margin-top: 0; margin-bottom: 0.75rem; }
        p { color: #94a3b8; font-size: 1.1rem; margin: 0; }
    </style>
</head>
<body>
    <div class="card">
        <h1>403 Forbidden</h1>
        <p>Acesso Negado: Token JWT ou sessão inválida/ausente.</p>
    </div>
</body>
</html>"""
        return HTMLResponse(content=forbidden_html, status_code=status.HTTP_403_FORBIDDEN)

    # Autenticado: serve a interface do frontend
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        response = FileResponse(index_file)
    else:
        response = HTMLResponse("<h1>CNCT Scraper Backend Ativo</h1><p>Frontend index.html nao encontrado.</p>")

    # Grava o cookie HttpOnly para manter a sessao nas navegacoes e chamadas de API subsequentes no iFrame
    response.set_cookie(
        key=COOKIE_NAME,
        value=valid_token_string,
        httponly=True,
        samesite="none" if COOKIE_SECURE else "lax",
        secure=COOKIE_SECURE,
        max_age=86400  # 24 horas
    )
    return response

@app.websocket("/ws/terminal")
async def websocket_terminal_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket autenticado para streaming de logs do terminal em tempo real.
    """
    await websocket.accept()

    # Valida se possui token na query string do WebSocket ou cookie de sessao enviado no handshake
    token = websocket.query_params.get("token") or websocket.cookies.get(COOKIE_NAME)
    if not token or decode_jwt_token(token) is None:
        await websocket.send_text("[ERRO] Sessão expirada ou token JWT inválido. Clique no botão 'Renovar Sessão / Recarregar'.")
        await websocket.close(code=1008)
        return

    await ws_manager.connect(websocket)
    try:
        await websocket.send_text("[INFO] Conexao WebSocket estabelecida com o Terminal CNCT Scraper.")
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("[PONG] Conexao ativa.")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
