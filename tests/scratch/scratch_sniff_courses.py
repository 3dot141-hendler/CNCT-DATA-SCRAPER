import json
import time
from playwright.sync_api import sync_playwright

log_file = open("sniff_courses.log", "w", encoding="utf-8")

def log(msg):
    print(msg)
    log_file.write(msg + "\n")
    log_file.flush()

def sniff_course_navigation():
    log("=" * 80)
    log("SNIFFER DE ENDPOINTS DE CURSOS - NAVEGACAO DIRETA")
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

        api_calls = []

        def on_response(resp):
            url = resp.url
            if "cnct-api" in url:
                status = resp.status
                log(f"[API RESPONSE] [{status}] {url}")
                try:
                    payload = resp.json()
                    api_calls.append({"url": url, "status": status, "data": payload})
                except Exception as e:
                    log(f"  -> Nao foi possivel parsear JSON: {e}")

        page.on("response", on_response)

        log("[1] Carregando home...")
        page.goto("https://cnct.mec.gov.br/", wait_until="domcontentloaded")
        time.sleep(2)

        # Testar IDs 1, 2, 7 e 200 navegando pelo Angular
        for course_id in [1, 2, 7, 200]:
            target_url = f"https://cnct.mec.gov.br/cursos/curso?id={course_id}"
            log(f"\n--- [TESTE] Navegando para {target_url} ---")
            start_t = time.time()
            page.goto(target_url, wait_until="networkidle")
            elapsed = time.time() - start_t
            log(f"Tempo de carregamento: {elapsed:.2f}s")
            time.sleep(2)

        with open("sniff_courses_captured.json", "w", encoding="utf-8") as f:
            json.dump(api_calls, f, indent=2, ensure_ascii=False)

        log("\n[SUCESSO] Chamadas salvas em 'sniff_courses_captured.json'")
        browser.close()

if __name__ == "__main__":
    try:
        sniff_course_navigation()
    except Exception as e:
        log(f"ERRO: {e}")
    finally:
        log_file.close()
