#!/bin/bash

# Script para executar o backend do Detran Agent

set -e

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Detran Agent - Backend API${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar se está no diretório correto
if [ ! -f "main.py" ]; then
    echo -e "${YELLOW}⚠ Execute este script do diretório backend/${NC}"
    exit 1
fi

# Verificar se o .env existe
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ Arquivo .env não encontrado!${NC}"
    echo "Criando .env a partir do .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Por favor, configure o arquivo .env com suas credenciais${NC}"
    exit 1
fi

# Verificar Python
if ! command -v python3.13 &> /dev/null; then
    if ! command -v python3 &> /dev/null; then
        echo -e "${YELLOW}✗ Python não encontrado${NC}"
        exit 1
    fi
    PYTHON_CMD=python3
else
    PYTHON_CMD=python3.13
fi

echo -e "${GREEN}✓${NC} Python encontrado: $($PYTHON_CMD --version)"

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo ""
    echo "Criando ambiente virtual..."
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓${NC} Ambiente virtual criado"
fi

# Ativar ambiente virtual
echo ""
echo "Ativando ambiente virtual..."
source venv/bin/activate
echo -e "${GREEN}✓${NC} Ambiente virtual ativado"

# Instalar/atualizar dependências
echo ""
echo "Instalando dependências..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓${NC} Dependências instaladas"

# Criar diretório de imagens se não existir
if [ ! -d "images" ]; then
    mkdir -p images
    echo -e "${GREEN}✓${NC} Diretório images/ criado"
fi

# Executar o servidor
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Iniciando servidor FastAPI...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Servidor disponível em:"
echo "  • Local:   http://localhost:8000"
echo "  • Docs:    http://localhost:8000/docs"
echo "  • ReDoc:   http://localhost:8000/redoc"
echo ""
echo "Pressione Ctrl+C para parar o servidor"
echo ""

# Executar uvicorn
python main.py