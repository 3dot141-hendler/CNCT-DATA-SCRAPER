FROM python:3.11-slim

# Instala dependências de sistema (gcc/make para o compilador C e ferramentas auxiliares)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala os navegadores e dependências de sistema do Playwright (Headless Chromium)
RUN playwright install --with-deps chromium

# Copia o código-fonte do projeto
COPY . .

# Compila o módulo C de agregação
RUN make clean && make

# Expõe a porta do FastAPI
EXPOSE 8000

# Executa o servidor uvicorn ouvindo na porta 8000
CMD ["uvicorn", "src.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
