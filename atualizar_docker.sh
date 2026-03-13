#!/bin/bash

# Script para atualizar e reexecutar o backend no Docker
# Uso: ./atualizar_docker.sh

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================="
echo "Atualizando Backend no Docker"
echo -e "==============================================${NC}\n"

# Verificar se está no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}✗ Erro: docker-compose.yml não encontrado${NC}"
    echo "Execute este script do diretório backend/"
    exit 1
fi

# Passo 1: Parar containers
echo -e "${YELLOW}1. Parando containers...${NC}"
docker-compose down
echo -e "${GREEN}✓ Containers parados${NC}\n"

# Passo 2: Rebuild da imagem
echo -e "${YELLOW}2. Rebuilding imagem Docker...${NC}"
echo "   (Isso pode levar alguns minutos)"
docker-compose build --no-cache
echo -e "${GREEN}✓ Imagem rebuilded${NC}\n"

# Passo 3: Iniciar containers
echo -e "${YELLOW}3. Iniciando containers...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Containers iniciados${NC}\n"

# Aguardar alguns segundos para o container iniciar
echo -e "${YELLOW}4. Aguardando inicialização...${NC}"
sleep 5

# Passo 4: Verificar status
echo -e "${YELLOW}5. Verificando status...${NC}"
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Backend está rodando${NC}\n"
else
    echo -e "${RED}✗ Backend não está rodando${NC}"
    echo "Verifique os logs com: docker-compose logs"
    exit 1
fi

# Passo 5: Testar health endpoint
echo -e "${YELLOW}6. Testando health endpoint...${NC}"
sleep 2
if curl -s http://localhost:5000/health > /dev/null; then
    echo -e "${GREEN}✓ Health endpoint respondendo${NC}\n"
else
    echo -e "${RED}✗ Health endpoint não está respondendo${NC}"
    echo "Verifique os logs com: docker-compose logs -f"
    exit 1
fi

# Passo 6: Mostrar logs
echo -e "${YELLOW}7. Últimas linhas dos logs:${NC}"
echo -e "${BLUE}----------------------------------------${NC}"
docker-compose logs --tail=20
echo -e "${BLUE}----------------------------------------${NC}\n"

# Resumo
echo -e "${GREEN}=============================================="
echo "✓ Backend atualizado com sucesso!"
echo -e "==============================================${NC}\n"

echo "Comandos úteis:"
echo "  Ver logs:           docker-compose logs -f"
echo "  Parar backend:      docker-compose down"
echo "  Restart:            docker-compose restart"
echo "  Status:             docker-compose ps"
echo ""
echo "Testar APIs:"
echo "  Health:   curl http://localhost:5000/health"
echo "  Login:    curl -X POST http://localhost:5000/api/auth/login \\"
echo "              -H 'Content-Type: application/json' \\"
echo "              -d '{\"cpf\":\"11111111111\",\"senha\":\"1111\"}'"
echo ""
echo -e "${BLUE}Frontend: cd ../frontend && npm run dev${NC}"
echo ""