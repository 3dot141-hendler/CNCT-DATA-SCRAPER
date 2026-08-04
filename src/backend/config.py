"""
Configuracoes e Gerenciamento de Variaveis de Ambiente do CNCT Scraper.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega arquivo .env na raiz do projeto
ROOT_DIR = Path(__file__).parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)

# Segredo JWT para autenticacao
SCRAPER_JWT_SECRET = os.getenv("SCRAPER_JWT_SECRET", "dev_default_secret_key_change_in_production")

# Origens permitidas para CORS e iFrame CSP (separadas por virgula)
ALLOWED_ORIGINS_RAW = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(",") if origin.strip()]

# Ambiente
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
# Em producao ou HTTPS, cookies de iframe cross-site devem ter Secure=True
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() in ("true", "1", "yes")
