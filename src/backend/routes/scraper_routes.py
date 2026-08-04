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
