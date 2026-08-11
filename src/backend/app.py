"""
Aplicacao Backend Principal FastAPI para o CNCT Scraper com Autenticacao JWT, Cookie HttpOnly e Suporte a iFrame.
"""

import os
import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path para garantir que importacoes 'from src...' funcionem em qualquer ambiente
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Query, status, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from src.backend.config import ALLOWED_ORIGINS, COOKIE_SECURE
from src.backend.auth import COOKIE_NAME, decode_jwt_token, require_auth_dependency
from src.backend.routes.scraper_routes import router as scraper_router
from src.backend.routes.data_routes import router as data_router
from src.backend.routes.migracao_enderecos import router as migracao_router
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
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
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
app.include_router(migracao_router, dependencies=[Depends(require_auth_dependency)])

FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"

def get_403_forbidden_response() -> HTMLResponse:
    """
    Retorna uma pagina HTML estilizada com status 403 Forbidden para acessos nao autenticados.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>403 - Acesso Negado | CNCT Scraper</title>
        <style>
            body {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: system-ui, -apple-system, sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            .card {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 2.5rem;
                text-align: center;
                max-width: 460px;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
            }
            .icon { font-size: 3.5rem; margin-bottom: 1rem; }
            h1 { color: #f43f5e; margin: 0 0 0.5rem 0; font-size: 1.75rem; font-weight: 800; }
            p { color: #94a3b8; font-size: 0.95rem; line-height: 1.5; margin-bottom: 1.5rem; }
            .badge {
                background-color: #0f172a;
                border: 1px solid #334155;
                color: #38bdf8;
                padding: 0.4rem 0.8rem;
                border-radius: 6px;
                font-size: 0.85rem;
                font-family: monospace;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">🔒</div>
            <h1>403 - Acesso Negado</h1>
            <p>O acesso direto a este microsserviço é restrito. Por favor, acesse o utilitário através do portal <strong>Esteio Conecta</strong> com uma sessão JWT válida.</p>
            <span class="badge">CNCT Scraper Microservice</span>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=status.HTTP_403_FORBIDDEN)


@app.get("/")
def read_root(request: Request, token: Optional[str] = Query(None)):
    """
    Serve a pagina principal index.html. Exige token JWT valido ou cookie de sessao HTTP 403.
    """
    valid_token_string = None
    if token and decode_jwt_token(token) is not None:
        valid_token_string = token
    else:
        session_cookie = request.cookies.get(COOKIE_NAME)
        if session_cookie and decode_jwt_token(session_cookie) is not None:
            valid_token_string = session_cookie

    if not valid_token_string:
        return get_403_forbidden_response()

    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        response = FileResponse(index_file)
    else:
        response = HTMLResponse("<h1>CNCT Scraper Backend Ativo</h1><p>Frontend index.html nao encontrado.</p>")

    response.set_cookie(
        key=COOKIE_NAME,
        value=valid_token_string,
        httponly=True,
        samesite="none" if COOKIE_SECURE else "lax",
        secure=COOKIE_SECURE,
        max_age=86400
    )
    return response

@app.get("/migracao")
@app.get("/migracao/")
@app.get("/migracao.html")
@app.get("/static/migracao.html")
def read_migracao(request: Request, token: Optional[str] = Query(None)):
    """
    Serve a pagina de migracao e sincronizacao de enderecos migracao.html.
    Exige token JWT valido ou cookie de sessao HTTP 403.
    """
    valid_token_string = None

    if token and decode_jwt_token(token) is not None:
        valid_token_string = token
    else:
        session_cookie = request.cookies.get(COOKIE_NAME)
        if session_cookie and decode_jwt_token(session_cookie) is not None:
            valid_token_string = session_cookie

    if not valid_token_string:
        return get_403_forbidden_response()

    migracao_file = FRONTEND_DIR / "migracao.html"
    if migracao_file.exists():
        response = FileResponse(migracao_file)
    else:
        response = HTMLResponse("<h1>CNCT Scraper Backend Ativo</h1><p>Página migracao.html não encontrada.</p>")

    response.set_cookie(
        key=COOKIE_NAME,
        value=valid_token_string,
        httponly=True,
        samesite="none" if COOKIE_SECURE else "lax",
        secure=COOKIE_SECURE,
        max_age=86400
    )
    return response

# Montar arquivos estaticos do Frontend (DEPOIS das rotas especificas de HTML protegidas)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

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

@app.get("/api/maintenance/deduplicate-vps")
def maintenance_deduplicate_vps():
    """
    Executa a deduplicação atômica no MySQL da VPS e adiciona o UNIQUE INDEX idx_unique_inst_id (id).
    """
    from scratch.deduplicate_vps import deduplicate_and_add_unique_index
    sucesso = deduplicate_and_add_unique_index(apply_changes=True)
    return {
        "status": "sucesso" if sucesso else "erro",
        "mensagem": "Deduplicação e criação do UNIQUE INDEX executadas!" if sucesso else "Falha ao deduplicar."
    }

@app.get("/api/maintenance/update-csv-format")
def update_csv_format():
    """
    Formata o csv_instituicoes.csv para conter todas as colunas de endereço estruturadas (logradouro, numero, complemento, bairro, municipio, uf, cep).
    """
    import os, csv
    from src.c_aggregator.bridge import parse_address_c
    csv_path = os.path.join(project_root, "src", "output", "csv_instituicoes.csv")
    if not os.path.exists(csv_path):
        return {"status": "erro", "mensagem": "CSV não encontrado."}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f, delimiter=";"))

    fieldnames = [
        "snowflake_id", "nome_instituicao", "dependencia_adm",
        "endereco", "logradouro", "numero", "complemento",
        "bairro", "municipio", "uf", "cep",
        "telefone", "email", "homepage", "cursos_ofertados_ids"
    ]

    updated_rows = []
    for r in reader:
        raw_end = r.get("endereco", "")
        parsed = parse_address_c(raw_end)
        updated_rows.append({
            "snowflake_id": r.get("snowflake_id") or r.get("id"),
            "nome_instituicao": r.get("nome_instituicao") or r.get("nome"),
            "dependencia_adm": r.get("dependencia_adm"),
            "endereco": raw_end,
            "logradouro": r.get("logradouro") or parsed["logradouro"],
            "numero": r.get("numero") or parsed["numero"],
            "complemento": r.get("complemento") or parsed["complemento"],
            "bairro": r.get("bairro") or parsed["bairro"],
            "municipio": r.get("municipio") or parsed["municipio"],
            "uf": r.get("uf") or parsed["uf"],
            "cep": r.get("cep") or parsed["cep"],
            "telefone": r.get("telefone"),
            "email": r.get("email"),
            "homepage": r.get("homepage"),
            "cursos_ofertados_ids": r.get("cursos_ofertados_ids") or "[]"
        })

    with open(csv_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(updated_rows)

    return {"status": "sucesso", "mensagem": "CSV atualizado com sucesso!", "total_registros": len(updated_rows)}

@app.get("/api/maintenance/validate-diff")
def maintenance_validate_diff():
    """
    Executa o diff em C contra o MySQL limpo e valida a eliminação dos 45 inativados.
    """
    import os, csv
    from src.c_aggregator.bridge import compare_datasets_c, parse_address_c
    from src.backend.database import get_db_connection

    csv_path = os.path.join(project_root, "src", "output", "csv_instituicoes.csv")
    csv_raw = []
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8") as f:
            csv_raw = list(csv.DictReader(f, delimiter=";"))

    csv_items = []
    for row in csv_raw:
        raw_end = row.get("endereco", "")
        parsed = parse_address_c(raw_end)
        csv_items.append({
            "snowflake_id": row.get("snowflake_id") or row.get("id"),
            "nome_instituicao": row.get("nome_instituicao") or row.get("nome"),
            "dependencia_adm": row.get("dependencia_adm"),
            "endereco_original": raw_end,
            "endereco": raw_end,
            "logradouro": parsed["logradouro"],
            "numero": parsed["numero"],
            "complemento": parsed["complemento"],
            "bairro": parsed["bairro"],
            "municipio": parsed["municipio"],
            "uf": parsed["uf"],
            "cep": parsed["cep"],
            "telefone": row.get("telefone"),
            "email": row.get("email"),
            "homepage": row.get("homepage")
        })

    conn = get_db_connection()
    if not conn:
        return {"status": "erro", "mensagem": "Falha de conexão com o MySQL"}
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nome_instituicao, municipio, uf, endereco, ativo FROM INSTITUICOES_ENSINO_TECNICO")
    db_items = cursor.fetchall()
    cursor.close()
    conn.close()

    res = compare_datasets_c(db_data=db_items, csv_data=csv_items, is_parcial=False)

    marista = next((m for m in res["mantidos"] if "Marista Nossa Senhora das Graças" in m.get("nome_instituicao", "")), None)
    florence = next((m for m in res["mantidos"] if "Florence" in m.get("nome_instituicao", "")), None)

    return {
        "status": "sucesso",
        "resumo_diff": {
            "total_db": len(db_items),
            "total_csv": len(csv_items),
            "mantidos": len(res["mantidos"]),
            "alterados": len(res["alterados"]),
            "novos": len(res["novos"]),
            "inativados": len(res["inativados"])
        },
        "validacao_escolas": {
            "colegio_marista_status": "MANTIDO (ativo=1)" if marista else "NÃO ENCONTRADO EM MANTIDOS",
            "colegio_marista_id": marista.get("id") if marista else None,
            "colegio_florence_status": "MANTIDO (ativo=1)" if florence else "NÃO ENCONTRADO EM MANTIDOS",
            "colegio_florence_id": florence.get("id") if florence else None
        },
        "amostra_inativados": res["inativados"][:10]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.backend.app:app", host="127.0.0.1", port=8000, reload=True)
