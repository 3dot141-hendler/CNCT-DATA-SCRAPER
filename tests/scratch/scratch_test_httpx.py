import httpx
import json

def test_httpx():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://cnct.mec.gov.br/"
    }

    with httpx.Client(headers=headers, follow_redirects=True, timeout=10.0) as client:
        print("[1] Testando GET https://cnct.mec.gov.br/cnct-api/home/...")
        res_home = client.get("https://cnct.mec.gov.br/cnct-api/home/")
        print("Status Home:", res_home.status_code)
        if res_home.status_code == 200:
            print("Home data keys:", list(res_home.json().keys()))

        print("\n[2] Testando GET https://cnct.mec.gov.br/cnct-api/cursos/1...")
        res_c1 = client.get("https://cnct.mec.gov.br/cnct-api/cursos/1")
        print("Status Curso 1:", res_c1.status_code)
        if res_c1.status_code == 200:
            print("Curso 1 Nome:", res_c1.json().get("nome"))

        print("\n[3] Testando GET https://cnct.mec.gov.br/cnct-api/cursos/7...")
        res_c7 = client.get("https://cnct.mec.gov.br/cnct-api/cursos/7")
        print("Status Curso 7:", res_c7.status_code)
        if res_c7.status_code == 200:
            print("Curso 7 Nome:", res_c7.json().get("nome"))

        print("\n[4] Testando GET buscaPorNomeCurso...")
        res_inst = client.get("https://cnct.mec.gov.br/cnct-api/instituicao/buscaPorNomeCurso?nomeCurso=T%C3%A9cnico%20em%20Agente%20Comunit%C3%A1rio%20de%20Sa%C3%BAde")
        print("Status Instituicoes:", res_inst.status_code)
        if res_inst.status_code == 200:
            print("Total instituicoes:", len(res_inst.json()))

if __name__ == "__main__":
    test_httpx()
