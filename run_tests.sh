#!/bin/bash
# Script di Test Automatico per Crestron MCP
# Avvia il mock server, esegue i test, e fornisce istruzioni per Claude

set -e

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}======================================================================${NC}"
echo -e "${BOLD}🧪 CRESTRON MCP - TEST AUTOMATICO${NC}"
echo -e "${BOLD}======================================================================${NC}"
echo ""

# Verifica Python
echo -e "${BLUE}[1/6]${NC} Verifica Python..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python non trovato!${NC}"
    exit 1
fi

# Usa python3 se disponibile, altrimenti python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo -e "${GREEN}✅ Python trovato: $($PYTHON_CMD --version)${NC}"
echo ""

# Verifica dipendenze
echo -e "${BLUE}[2/6]${NC} Verifica dipendenze..."
$PYTHON_CMD -c "import mcp, httpx, pydantic" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Tutte le dipendenze installate${NC}"
else
    echo -e "${YELLOW}⚠️  Installazione dipendenze...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dipendenze installate${NC}"
fi
echo ""

# Verifica file necessari
echo -e "${BLUE}[3/6]${NC} Verifica file..."
FILES=(
    "crestron_mcp.py"
    "mock_crestron_server.py"
    "test_crestron_mcp.py"
)

for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ File mancante: $file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ Tutti i file presenti${NC}"
echo ""

# Avvia il mock server in background
echo -e "${BLUE}[4/6]${NC} Avvio mock Crestron server..."
echo -e "${YELLOW}📡 Mock server sulla porta 8080...${NC}"

# Termina eventuali processi sulla porta 8080
lsof -ti:8080 | xargs kill -9 2>/dev/null || true

# Avvia il server in background
$PYTHON_CMD mock_crestron_server.py > mock_server.log 2>&1 &
MOCK_PID=$!

# Aspetta che il server sia pronto
sleep 2

# Verifica che il server sia in esecuzione
if ! ps -p $MOCK_PID > /dev/null; then
    echo -e "${RED}❌ Errore nell'avvio del mock server${NC}"
    cat mock_server.log
    exit 1
fi

echo -e "${GREEN}✅ Mock server avviato (PID: $MOCK_PID)${NC}"
echo ""

# Esegui i test
echo -e "${BLUE}[5/6]${NC} Esecuzione test automatici..."
echo ""
$PYTHON_CMD test_crestron_mcp.py

TEST_RESULT=$?

echo ""

# Mostra configurazione per Claude
echo -e "${BLUE}[6/6]${NC} Configurazione per Claude Desktop..."
echo ""
echo -e "${BOLD}Aggiungi al file claude_desktop_config.json:${NC}"
echo ""
echo -e "${YELLOW}{${NC}"
echo -e "${YELLOW}  \"mcpServers\": {${NC}"
echo -e "${YELLOW}    \"crestron\": {${NC}"
echo -e "${YELLOW}      \"command\": \"$PYTHON_CMD\",${NC}"
echo -e "${YELLOW}      \"args\": [\"$(pwd)/crestron_mcp.py\"]${NC}"
echo -e "${YELLOW}    }${NC}"
echo -e "${YELLOW}  }${NC}"
echo -e "${YELLOW}}${NC}"
echo ""

# Comandi di esempio
echo -e "${BOLD}======================================================================${NC}"
echo -e "${BOLD}📝 COMANDI DA TESTARE CON CLAUDE${NC}"
echo -e "${BOLD}======================================================================${NC}"
echo ""
echo -e "${GREEN}1. Autenticazione:${NC}"
echo -e "   ${BLUE}Autenticati con host localhost:8080 e token test-token-123${NC}"
echo ""
echo -e "${GREEN}2. Scoperta:${NC}"
echo -e "   ${BLUE}Mostrami tutte le stanze e i dispositivi${NC}"
echo ""
echo -e "${GREEN}3. Controllo Tapparelle:${NC}"
echo -e "   ${BLUE}Chiudi tutte le tapparelle${NC}"
echo ""
echo -e "${GREEN}4. Scene:${NC}"
echo -e "   ${BLUE}Attiva la scena Film${NC}"
echo ""
echo -e "${GREEN}5. Termostato:${NC}"
echo -e "   ${BLUE}Imposta il termostato a 21 gradi${NC}"
echo ""
echo -e "${GREEN}6. Sensori:${NC}"
echo -e "   ${BLUE}Mostrami i sensori in cucina${NC}"
echo ""
echo -e "${YELLOW}📖 Per più comandi, vedi COMANDI_TEST.md${NC}"
echo ""

# Istruzioni finali
echo -e "${BOLD}======================================================================${NC}"
echo -e "${BOLD}🎯 PROSSIMI PASSI${NC}"
echo -e "${BOLD}======================================================================${NC}"
echo ""
echo -e "${GREEN}✅ Mock server in esecuzione${NC} (http://localhost:8080)"
echo -e "${GREEN}✅ Test automatici completati${NC} ($TEST_RESULT/10 passed)"
echo ""
echo -e "${YELLOW}📋 TODO:${NC}"
echo -e "   1. Configura Claude Desktop (vedi sopra)"
echo -e "   2. Riavvia Claude Desktop"
echo -e "   3. Testa i comandi con Claude"
echo ""
echo -e "${YELLOW}🛑 Per fermare il mock server:${NC}"
echo -e "   kill $MOCK_PID"
echo ""
echo -e "${YELLOW}📖 Guide complete:${NC}"
echo -e "   - GUIDA_TEST.md      (Guida completa)"
echo -e "   - COMANDI_TEST.md    (Lista comandi)"
echo ""
echo -e "${BOLD}======================================================================${NC}"
echo ""

# Mantieni lo script in esecuzione e mostra i log del server
echo -e "${BLUE}📡 Log del mock server (Ctrl+C per terminare):${NC}"
echo ""
tail -f mock_server.log
