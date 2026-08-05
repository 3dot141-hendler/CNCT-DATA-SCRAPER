FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Instala dependências nativas Linux/ARM64 (gcc, make, curl, navegador Chromium)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    make \
    curl \
    chromium \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala dependências de bibliotecas Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código-fonte do projeto
COPY . .

# Compila o executável C de alta performance
RUN gcc -O3 -Wall src/c_aggregator/aggregator.c -o src/c_aggregator/aggregator

# Expõe a porta 8000 da API FastAPI
EXPOSE 8000

# Comando de inicialização do servidor Uvicorn
CMD ["uvicorn", "src.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
