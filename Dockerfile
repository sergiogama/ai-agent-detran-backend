FROM --platform=linux/amd64 python:3.11-slim

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

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expor porta (Code Engine usa 8080 por padrão)
EXPOSE 8080

# Comando para iniciar o servidor (sem reload em produção)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]