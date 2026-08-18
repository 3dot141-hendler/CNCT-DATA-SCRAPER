FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Instala ferramentas essenciais de compilação C para ARM64 / x86_64, make e curl para Healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala dependências de bibliotecas Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código-fonte do projeto
COPY . .

# Compila o executável C nativo de alta performance para a arquitetura do container (ARM64 / x86_64)
RUN gcc -O3 -Wall src/c_aggregator/aggregator.c -o src/c_aggregator/aggregator && \
    chmod +x src/c_aggregator/aggregator

# Expõe a porta 8000 da API FastAPI
EXPOSE 8000

# Healthcheck nativo consultando a rota pública /health (sem JWT) para o Coolify validar o container
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicialização do servidor Uvicorn
CMD ["uvicorn", "src.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
