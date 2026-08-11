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

# Configuracoes de Banco de Dados MySQL (VPS via Túnel SSH / Local)
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "esteio_conecta")

# Origens permitidas para CORS e iFrame CSP (separadas por virgula)
ALLOWED_ORIGINS_RAW = os.getenv("ALLOWED_ORIGINS", "https://app.hif.dev.br,http://localhost:3000,http://localhost:8080,http://localhost:8000,http://127.0.0.1:8000")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(",") if origin.strip()]

# Ambiente
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
# Em producao ou HTTPS, cookies de iframe cross-site devem ter Secure=True e SameSite=None
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() in ("true", "1", "yes")
