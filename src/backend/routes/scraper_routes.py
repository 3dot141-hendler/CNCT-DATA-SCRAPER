"""
Rotas FastAPI para controle e disparos do pipeline de raspagem.
Executa a raspagem em uma thread dedicada para evitar conflitos de event loop no Windows/Python 3.13.
"""

import threading
from fastapi import APIRouter, HTTPException
from src.scraper.pipeline import ScraperPipeline

router = APIRouter(prefix="/api/scraper", tags=["Scraper"])

# Estado global da raspagem
scraper_status = {
    "is_running": False,
    "last_result": None,
    "current_course": 0,
    "total_courses": 0
}

def _background_scraper_task(max_courses: int):
    global scraper_status
    scraper_status["is_running"] = True
    try:
        pipeline = ScraperPipeline()
        result = pipeline.run(max_courses=max_courses)
        scraper_status["last_result"] = result
    except Exception as e:
        scraper_status["last_result"] = {"error": str(e)}
    finally:
        scraper_status["is_running"] = False

@router.post("/start")
def start_scraping(max_courses: int = 5):
    """
    Dispara o pipeline de raspagem em segundo plano via thread dedicada.
    """
    global scraper_status
    if scraper_status["is_running"]:
        raise HTTPException(status_code=400, detail="O pipeline de raspagem ja esta em execucao.")

    thread = threading.Thread(target=_background_scraper_task, args=(max_courses,), daemon=True)
    thread.start()
    
    return {"message": "Pipeline de raspagem iniciado em segundo plano.", "max_courses": max_courses}

@router.get("/status")
def get_scraping_status():
    """
    Retorna o status atual do pipeline de raspagem.
    """
    return scraper_status


@router.get("/total-cursos-mec")
def get_total_cursos_mec():
    """
    Consulta ultrarrápida ao catálogo oficial do MEC (~200ms) para retornar o total exato de cursos cadastrados.
    """
    try:
        from src.scraper.client import CNCTApiClient
        client = CNCTApiClient()
        catalog = client.get_home_catalog()
        if catalog and "catalogo" in catalog:
            total = catalog["catalogo"].get("quantidadeCursos", 215)
            return {"total_cursos_mec": total, "sucesso": True}
    except Exception as e:
        print(f"[WARN] Falha ao consultar total de cursos no MEC: {e}")
    
    return {"total_cursos_mec": 215, "sucesso": False, "mensagem": "Usando valor padrão de fallback."}
