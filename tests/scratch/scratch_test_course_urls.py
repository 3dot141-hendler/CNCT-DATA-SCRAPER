import json
import time
from playwright.sync_api import sync_playwright

def inspect_course_endpoints():
    print("=" * 80)
    print("INSPECIONANDO ENDPOINTS EXATOS PARA CURSO ID=2, ID=200, ID=245")
    print("=" * 80 + "\n")

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
                print(f"[API CAPTURADA] [{resp.status}] {url}")
                try:
                    payload = resp.json()
                    api_calls.append({"url": url, "status": resp.status, "data": payload})
                except Exception:
                    pass

        page.on("response", on_response)

        # 1. Carregar home primeiro para cookies do Cloudflare
        page.goto("https://cnct.mec.gov.br/", wait_until="domcontentloaded")
        time.sleep(2)

        # 2. Navegar para a URL do curso ID 2
        print("\n--- Navegando para https://cnct.mec.gov.br/cursos/curso?id=2 ---")
        page.goto("https://cnct.mec.gov.br/cursos/curso?id=2", wait_until="networkidle")
        time.sleep(3)

        # 3. Navegar para a URL do curso ID 200
        print("\n--- Navegando para https://cnct.mec.gov.br/cursos/curso?id=200 ---")
        page.goto("https://cnct.mec.gov.br/cursos/curso?id=200", wait_until="networkidle")
        time.sleep(3)

        # 4. Navegar para a URL do curso ID 245
        print("\n--- Navegando para https://cnct.mec.gov.br/cursos/curso?id=245 ---")
        page.goto("https://cnct.mec.gov.br/cursos/curso?id=245", wait_until="networkidle")
        time.sleep(3)

        # Salvar chamadas de API capturadas durante as 3 navegacoes
        with open("course_endpoints_test.json", "w", encoding="utf-8") as f:
            json.dump(api_calls, f, indent=2, ensure_ascii=False)

        print("\n[SUCESSO] Chamadas salvas em 'course_endpoints_test.json'")
        browser.close()

if __name__ == "__main__":
    inspect_course_endpoints()
