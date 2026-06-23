#!/bin/bash
# ============================================================
# deploy.sh — Script de deploy automatizado para Edumetria WC26
# ============================================================

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

echo "=========================================="
echo "🚀 Edumetria WC26 — Deploy Automatizado"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Verificar branch
echo "📋 Verificando git..."
BRANCH=$(git branch --show-current)
echo "   Branch atual: $BRANCH"

if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ]; then
    echo -e "${YELLOW}⚠️  Você está na branch '$BRANCH'. Mudar para main? (y/n)${NC}"
    read -r response
    if [ "$response" = "y" ]; then
        git checkout main 2>/dev/null || git checkout master
    fi
fi

# 2. Verificar se há dados processados
echo ""
echo "📊 Verificando dados processados..."
PROCESSED_DIR="$REPO_DIR/data/processed"

if [ ! -d "$PROCESSED_DIR" ] || [ -z "$(ls -A $PROCESSED_DIR/*.parquet 2>/dev/null)" ]; then
    echo -e "${YELLOW}⚠️  Nenhum parquet encontrado em data/processed/${NC}"
    echo "   Deseja rodar o ETL agora? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        echo "   🔄 Rodando ETL..."
        python -m etl.run_pipeline
        if [ $? -ne 0 ]; then
            echo -e "${RED}✗ ETL falhou. Abortando deploy.${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ ETL concluído${NC}"
    else
        echo -e "${YELLOW}⚠️  Deploy sem dados. O Cloud usará dados de demonstração.${NC}"
    fi
else
    PARQUET_COUNT=$(ls -1 $PROCESSED_DIR/*.parquet 2>/dev/null | wc -l)
    echo -e "${GREEN}✓ $PARQUET_COUNT parquets encontrados${NC}"
fi

# 3. Verificar mudanças no repo
echo ""
echo "📦 Verificando mudanças..."
git add -A

if git diff --cached --quiet; then
    echo -e "${GREEN}✓ Nenhuma mudança para commitar${NC}"
else
    echo "   Mudanças detectadas:"
    git diff --cached --stat
    
    echo ""
    echo "📝 Digite a mensagem do commit (ou Enter para padrão):"
    read -r msg
    if [ -z "$msg" ]; then
        msg="chore: atualiza dados processados para Streamlit Cloud ($(date +%Y-%m-%d))"
    fi
    
    git commit -m "$msg"
    echo -e "${GREEN}✓ Commit realizado${NC}"
fi

# 4. Push
echo ""
echo "☁️  Enviando para o GitHub..."
git push origin $(git branch --show-current)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Push realizado com sucesso!${NC}"
else
    echo -e "${RED}✗ Push falhou. Verifique suas credenciais.${NC}"
    exit 1
fi

# 5. Abrir app
echo ""
echo "⏳ Aguardando deploy do Streamlit Cloud..."
APP_URL="https://quantasystemdev.streamlit.app"

echo "   URL do app: $APP_URL"
echo ""
echo "   Deseja abrir o app no navegador? (y/n)"
read -r response
if [ "$response" = "y" ]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "$APP_URL"
    elif command -v open &> /dev/null; then
        open "$APP_URL"
    elif command -v start &> /dev/null; then
        start "$APP_URL"
    else
        echo "   Abra manualmente: $APP_URL"
    fi
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Deploy concluído!${NC}"
echo "=========================================="
