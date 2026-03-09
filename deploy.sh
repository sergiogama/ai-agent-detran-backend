#!/bin/bash

# ============================================================================
# Script de Deploy - Detran Backend
# Atualiza o código no GitHub para deploy automático no Code Engine
# ============================================================================

set -e  # Parar em caso de erro

echo "🚀 Deploy do Detran Backend"
echo "================================"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar se está no diretório correto
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Erro: Execute este script do diretório backend/${NC}"
    exit 1
fi

# Verificar se há mudanças
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Nenhuma mudança detectada${NC}"
    read -p "Deseja continuar mesmo assim? (s/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 0
    fi
fi

# Mostrar status
echo -e "${YELLOW}📋 Mudanças detectadas:${NC}"
git status --short
echo ""

# Pedir mensagem de commit
read -p "📝 Mensagem do commit: " commit_message

if [ -z "$commit_message" ]; then
    commit_message="Update: $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${YELLOW}Usando mensagem padrão: $commit_message${NC}"
fi

# Git add
echo ""
echo -e "${GREEN}➕ Adicionando arquivos...${NC}"
git add .

# Git commit
echo -e "${GREEN}💾 Criando commit...${NC}"
git commit -m "$commit_message" || {
    echo -e "${YELLOW}⚠️  Nada para commitar ou commit já existe${NC}"
}

# Git push
echo -e "${GREEN}🚀 Enviando para GitHub...${NC}"
git push origin main || git push origin master || {
    echo -e "${RED}❌ Erro ao fazer push${NC}"
    echo -e "${YELLOW}💡 Dica: Verifique se o remote está configurado:${NC}"
    echo "   git remote -v"
    exit 1
}

echo ""
echo -e "${GREEN}✅ Deploy concluído com sucesso!${NC}"
echo ""
echo "📊 Próximos passos:"
echo "1. Acesse: https://cloud.ibm.com/codeengine"
echo "2. Verifique o status do build"
echo "3. Aguarde o deploy automático"
echo ""
echo "🔗 Seu repositório: https://github.com/sergiogama/ai-agent-detran-backend"
echo ""