import json
import time
from playwright.sync_api import sync_playwright

log_file = open("inspect_id7.log", "w", encoding="utf-8")

def log(msg):
    print(msg)
    log_file.write(msg + "\n")
    log_file.flush()

def inspect_course_7():
    log("=" * 80)
    log("INSPECIONANDO REQUISICOES DE REDE E TEMPO DE RESPOSTA PARA CURSO ID=7")
    log("=" * 80 + "\n")

    stealth_args = [
        "--headless=new",
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox"
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=stealth_args)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        api_responses = []

        def on_response(resp):
            url = resp.url
            if "cnct-api" in url:
                status = resp.status
                log(f"[API NETWORK Interceptada] [{status}] {url}")
                try:
                    data = resp.json()
                    api_responses.append({"url": url, "status": status, "data": data})
                except Exception as e:
                    log(f"  -> Erro ao parsear JSON: {e}")

        page.on("response", on_response)

        log("[1] Carregando home para sessao WAF...")
        page.goto("https://cnct.mec.gov.br/", wait_until="networkidle")
        time.sleep(2)

        log("\n[2] Navegando para https://cnct.mec.gov.br/cursos/curso?id=7 e aguardando networkidle...")
        start_time = time.time()
        page.goto("https://cnct.mec.gov.br/cursos/curso?id=7", wait_until="networkidle")
        elapsed = time.time() - start_time
        log(f"Tempo total de carregamento da pagina: {elapsed:.2f} segundos")

        # Aguardar tempo adicional para garantir que requisições assincronas terminem
        time.sleep(5)

        log(f"\n[3] Total de chamadas cnct-api capturadas: {len(api_responses)}")
        for item in api_responses:
            log(f" - URL: {item['url']}")
            if isinstance(item['data'], dict):
                log(f"   Chaves do JSON: {list(item['data'].keys())}")
                if "nome" in item['data']:
                    log(f"   Nome do Curso: {item['data']['nome']}")
            elif isinstance(item['data'], list):
                log(f"   Lista com {len(item['data'])} elementos.")

        with open("inspect_id7_data.json", "w", encoding="utf-8") as f:
            json.dump(api_responses, f, indent=2, ensure_ascii=False)

        browser.close()

if __name__ == "__main__":
    try:
        inspect_course_7()
    except Exception as e:
        log(f"EXCECAO: {e}")
    finally:
        log_file.close()
