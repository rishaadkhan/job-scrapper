#!/usr/bin/env bash

# Enterprise Job Scraper & Intelligence Platform - Local Start Script
# Starts Backend API (Port 8000), Sandboxed LaTeX Compiler (Port 8001), and Frontend (Port 5173).

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}        🚀 Starting Job Scraper Enterprise Application System         ${NC}"
echo -e "${CYAN}======================================================================${NC}"

# Check Python virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtualenv not found. Running setup.sh first...${NC}"
    ./setup.sh
fi

# Activate Python virtual environment
source venv/bin/activate

# Ensure output directory exists for log files
mkdir -p output

# Array of background process PIDs
PIDS=()

cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down all services gracefully...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    sleep 1
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
    rm -f .app_pids
    echo -e "${GREEN}✓ All services stopped successfully.${NC}"
    exit 0
}

# Trap Ctrl+C (SIGINT) and SIGTERM
trap cleanup SIGINT SIGTERM EXIT

# 1. Start LaTeX Compiler Microservice (Port 8001)
echo -e "${CYAN}[1/3] Starting Sandboxed LaTeX Compiler Service (Port 8001)...${NC}"
(cd services/latex-compiler && uvicorn main:app --port 8001 > ../../output/latex_compiler.log 2>&1) &
LATEX_PID=$!
PIDS+=($LATEX_PID)

# 2. Start FastAPI Backend REST API (Port 8000)
echo -e "${CYAN}[2/3] Starting FastAPI Backend API (Port 8000)...${NC}"
uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload > output/backend_api.log 2>&1 &
BACKEND_PID=$!
PIDS+=($BACKEND_PID)

# 3. Start Frontend React Dashboard (Port 5173)
echo -e "${CYAN}[3/3] Starting Frontend React Web Dashboard (Port 5173)...${NC}"
(cd frontend && npm run dev > ../output/frontend.log 2>&1) &
FRONTEND_PID=$!
PIDS+=($FRONTEND_PID)

# Save PIDs to file for stop.sh script
echo "${PIDS[@]}" > .app_pids

sleep 2

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  🎉 Application successfully started and running in background!    ${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo -e "  🌐 ${CYAN}Web Dashboard:${NC}   http://localhost:5173"
echo -e "  ⚙️  ${CYAN}Backend API:${NC}     http://localhost:8000"
echo -e "  📚 ${CYAN}Swagger Docs:${NC}    http://localhost:8000/docs"
echo -e "  📄 ${CYAN}LaTeX Compiler:${NC}  http://localhost:8001"
echo ""
echo -e "  📋 Logs written to:${NC}"
echo -e "     - output/backend_api.log"
echo -e "     - output/frontend.log"
echo -e "     - output/latex_compiler.log"
echo ""
echo -e "  ${YELLOW}Press [Ctrl+C] in this terminal window to stop all services.${NC}"
echo -e "  ${YELLOW}Alternatively, run ./stop.sh in another terminal window.${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""

# Block and wait for background jobs / Ctrl+C signal
wait
