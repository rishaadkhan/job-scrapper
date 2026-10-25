#!/usr/bin/env bash

# Enterprise Job Scraper & Intelligence Platform - Stop Script
# Gracefully terminates Backend API (Port 8000), LaTeX Compiler (Port 8001), and Frontend (Port 5173).

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}Stopping Job Scraper Application Services...${NC}"

# 1. Terminate tracked background PIDs if .app_pids file exists
if [ -f ".app_pids" ]; then
    PIDS=$(cat .app_pids)
    for pid in $PIDS; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    rm -f .app_pids
fi

# 2. Fallback: Clean up any active listeners on application ports (8000, 8001, 5173)
PORTS=(8000 8001 5173)
for port in "${PORTS[@]}"; do
    PIDS_ON_PORT=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$PIDS_ON_PORT" ]; then
        echo -e "${YELLOW}Stopping process on port $port (PID: $PIDS_ON_PORT)...${NC}"
        kill -9 $PIDS_ON_PORT 2>/dev/null || true
    fi
done

echo -e "${GREEN}✓ All application services have been stopped successfully.${NC}"
