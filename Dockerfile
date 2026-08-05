FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependências de sistema (gcc, make, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala as dependências do sistema operacional para o Playwright e baixa o Chromium
RUN playwright install-deps chromium && playwright install chromium

# Copia todo o código-fonte
COPY . .

# Compila o executável C de agregação
RUN gcc -O3 -Wall src/c_aggregator/aggregator.c -o src/c_aggregator/aggregator

# Expõe a porta do FastAPI
EXPOSE 8000

# Executa o servidor uvicorn
CMD ["uvicorn", "src.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
