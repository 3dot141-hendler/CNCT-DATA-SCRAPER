"""
Cliente HTTP de alta velocidade e diagnostico transparente para a API REST do CNCT.
Utiliza httpx / urllib com headers de navegador e fallback automatizado.
"""

import time
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional, Callable


class CNCTApiClient:
    """
    Cliente desacoplado e ultrarrapido para a API REST do CNCT.
    Elimina travamentos de subprocessos e fornece diagnosticos em tempo real.
    """

    def __init__(self, base_url: str = "https://cnct.mec.gov.br", delay_seconds: float = 0.5, log_callback: Optional[Callable] = None):
        self.base_url = base_url.rstrip("/")
        self.delay_seconds = delay_seconds
        self.log_callback = log_callback

        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://cnct.mec.gov.br/",
            "Origin": "https://cnct.mec.gov.br"
        }

    def log(self, message: str, level: str = "INFO"):
        """
        Emite logs no terminal do sistema e no WebSocket do frontend.
        """
        print(f"[{level}] [CLIENT] {message}")
        if self.log_callback:
            try:
                self.log_callback(message, level)
            except Exception:
                pass

    def start_session(self):
        """
        Inicializa o cliente HTTP e valida a conectividade com a API REST do MEC.
        """
        self.log("Inicializando cliente HTTP de alta velocidade...")
        start_t = time.time()
        
        # Testar conectividade inicial com a API REST
        test_url = f"{self.base_url}/cnct-api/version"
        status, data = self._http_get_json(test_url, timeout=10)
        
        if status == 200:
            elapsed = time.time() - start_t
            self.log(f"Sessao HTTP validada com sucesso em {elapsed:.2f}s! API Versao: {data}", "SUCESSO")
        else:
            self.log(f"Conexao inicial com API retornou status {status}. Continuando com headers resilientes...", "AVISO")

    def close_session(self):
        """
        Encerramento da sessao HTTP.
        """
        self.log("Sessao HTTP finalizada de forma limpa.")

    def get_home_catalog(self) -> Optional[Dict[str, Any]]:
        """
        Obtem o catalogo principal e a lista de Eixos Tecnologicos.
        """
        url = f"{self.base_url}/cnct-api/home/"
        status, data = self._http_get_json(url)
        if status == 200 and isinstance(data, dict):
            return data
        return None

    def get_course_details(self, course_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtem os detalhes de um curso tentando os endpoints conhecidos.
        """
        candidate_urls = [
            f"{self.base_url}/cnct-api/cursos/{course_id}",
            f"{self.base_url}/cnct-api/curso/{course_id}",
            f"{self.base_url}/cnct-api/curso?id={course_id}"
        ]

        for url in candidate_urls:
            status, data = self._http_get_json(url, timeout=8)
            if status == 200 and isinstance(data, dict) and ("nome" in data or "id" in data):
                return data

        return None

    def get_institutions_by_course_name(self, course_name: str) -> List[Dict[str, Any]]:
        """
        Obtem a lista de instituicoes ofertantes para determinado nome de curso.
        """
        time.sleep(self.delay_seconds)
        encoded_name = urllib.parse.quote(course_name)
        url = f"{self.base_url}/cnct-api/instituicao/buscaPorNomeCurso?nomeCurso={encoded_name}"
        
        status, data = self._http_get_json(url, timeout=12)
        if status == 200 and isinstance(data, list):
            return data
        return []

    def _http_get_json(self, url: str, timeout: int = 10, retries: int = 2) -> (int, Optional[Any]):
        """
        Executa requisicao GET nativa via urllib com headers completos de navegador.
        Retorna (status_code, json_data).
        """
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, headers=self.default_headers, method="GET")
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status = resp.getcode()
                    body_bytes = resp.read()
                    if status == 200 and body_bytes:
                        data = json.loads(body_bytes.decode("utf-8"))
                        return (status, data)
                    return (status, None)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return (404, None)
                time.sleep(0.5 * (attempt + 1))
            except Exception as e:
                time.sleep(0.5 * (attempt + 1))

        return (0, None)
