"""
Ponto de entrada principal da aplicação CNCT Scraper.
"""

import sys
import uvicorn
from pathlib import Path

# Adiciona o diretorio raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

def main():
    print("=" * 80)
    print("INICIANDO SERVIDOR WEBAPP CNCT SCRAPER - FASTAPI + WEBSOCKETS")
    print("Acesse no navegador: http://localhost:8000")
    print("=" * 80 + "\n")
    
    uvicorn.run("src.backend.app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
