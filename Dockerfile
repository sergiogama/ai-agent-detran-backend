FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema para ibm-db
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    wget \
    tar \
    libxml2 \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Comando para iniciar o servidor (sem reload em produção)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]