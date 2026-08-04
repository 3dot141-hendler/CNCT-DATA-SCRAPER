"""
Script de Descoberta e Mapeamento de Rede (Fase 1 - CNCT Scraper - Interceptador Total)

Este script captura TODO o trafego de rede (XHR, Fetch, API, JSON, WebSocket, etc.)
sem filtros restritivos, salvando logs em tempo real durante a navegacao manual.

Uso:
    python discovery_sniffer.py
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from playwright.sync_api import sync_playwright, Response, Request


LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
TRAFFIC_LOG_FILE = LOGS_DIR / f"network_traffic_{TIMESTAMP}.json"
ENDPOINTS_LOG_FILE = LOGS_DIR / f"endpoints_summary_{TIMESTAMP}.json"

captured_traffic: List[Dict[str, Any]] = []
captured_endpoints: Dict[str, Dict[str, Any]] = {}


def save_logs():
    """
    Persiste os logs capturados em disco no formato JSON formatado.
    """
    try:
        with open(TRAFFIC_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(captured_traffic, f, indent=2, ensure_ascii=False)

        formatted_endpoints = {}
        for endpoint, data in captured_endpoints.items():
            formatted_endpoints[endpoint] = {
                "url_pattern": data["url_pattern"],
                "methods": list(data["methods"]),
                "sample_statuses": list(data["sample_statuses"]),
                "sample_headers": data["sample_headers"],
                "call_count": data["call_count"],
                "sample_response": data["sample_response"]
            }

        with open(ENDPOINTS_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(formatted_endpoints, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERRO AO SALVAR LOGS]: {e}")


def handle_request(request: Request):
    """
    Handler para interceptar todas as requisicoes saindo do navegador.
    """
    print(f"[REQUISICAO] [{request.method}] [{request.resource_type}] {request.url}")


def handle_response(response: Response):
    """
    Handler para interceptar e salvar todas as respostas recebidas.
    """
    request = response.request
    url = request.url
    method = request.method
    status = response.status
    headers = response.headers
    resource_type = request.resource_type

    # Ignora apenas arquivos estaticos de midia/fontes pesados para evitar inchar os logs
    ignored_static = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".css")
    if any(url.lower().split("?")[0].endswith(ext) for ext in ignored_static):
        return

    response_body = None
    content_type = headers.get("content-type", "")

    try:
        if "application/json" in content_type or "text/json" in content_type or "json" in url.lower():
            response_body = response.json()
        elif "text/" in content_type or "javascript" in content_type or "xml" in content_type:
            text_content = response.text()
            try:
                response_body = json.loads(text_content)
            except Exception:
                response_body = text_content[:4000]
        else:
            response_body = f"<Data Type: {content_type}>"
    except Exception as err:
        response_body = f"<Body Nao Parseavel: {str(err)}>"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "method": method,
        "url": url,
        "status": status,
        "resource_type": resource_type,
        "request_headers": dict(request.headers),
        "request_payload": request.post_data,
        "response_headers": dict(headers),
        "response_body": response_body
    }

    captured_traffic.append(entry)

    parsed_url = url.split("?")[0]
    if parsed_url not in captured_endpoints:
        captured_endpoints[parsed_url] = {
            "url_pattern": parsed_url,
            "methods": set(),
            "sample_statuses": set(),
            "sample_headers": dict(request.headers),
            "sample_response": response_body,
            "call_count": 0
        }
    
    captured_endpoints[parsed_url]["methods"].add(method)
    captured_endpoints[parsed_url]["sample_statuses"].add(status)
    captured_endpoints[parsed_url]["call_count"] += 1

    print(f"[RESPOSTA DE INTERESSE] [{status}] [{method}] [{resource_type}] {url}")
    
    # Auto-save continuo para garantir persistencia dos logs a cada chamada
    save_logs()


def run_discovery():
    """
    Executa a sessao interativa com modo stealth e auto-save.
    """
    print("=" * 80)
    print("INICIANDO INSPECTOR TOTAL DE REDE (XHR/FETCH/API) - CNCT SCRAPER")
    print("O navegador sera aberto em modo visivel.")
    print("Navegue livremente pelo portal do CNCT.")
    print("Todas as chamadas serao exibidas em tempo real neste terminal.")
    print("=" * 80 + "\n")

    stealth_args = [
        "--start-maximized",
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-infobars"
    ]
    
    real_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(headless=False, args=stealth_args)
        except Exception as e:
            print(f"[AVISO] Chromium nativo nao iniciado: {e}")
            try:
                browser = p.chromium.launch(headless=False, channel="chrome", args=stealth_args)
            except Exception:
                browser = p.chromium.launch(headless=False, channel="msedge", args=stealth_args)

        context = browser.new_context(
            viewport=None,
            user_agent=real_user_agent,
            ignore_https_errors=True
        )
        
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)

        page = context.new_page()
        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            print("[INFO] Abrindo cnct.mec.gov.br...")
            page.goto("https://cnct.mec.gov.br/", wait_until="domcontentloaded")
            print("[INFO] Pronto! Pode clicar nos cursos e instituicoes no navegador.")
            print("[INFO] As chamadas de API serao impressas abaixo instantaneamente.\n")

            while not page.is_closed():
                time.sleep(0.5)
        except Exception as e:
            print(f"Sessao finalizada: {e}")
        finally:
            save_logs()
            print(f"\n[SUCESSO] Logs finais salvos em: {TRAFFIC_LOG_FILE.resolve()}")


if __name__ == "__main__":
    run_discovery()
