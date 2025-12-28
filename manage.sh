#!/bin/bash

# Romanian Admin Platform Management Script
# Usage: ./manage.sh [start|stop|restart|status]

PROJECT_DIR="/Users/maleticimiroslav/Facultate/AN3/SEM 2/IC/HackTM2025"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
PID_FILE="$PROJECT_DIR/.pids"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

start_services() {
    echo -e "${BLUE}🚀 Starting Romanian Admin Platform...${NC}"
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        echo -e "${YELLOW}⚠️  Services might already be running. Use './manage.sh stop' first.${NC}"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
    
    # Start Backend
    echo -e "${GREEN}📡 Starting FastAPI backend...${NC}"
    cd "$BACKEND_DIR"
    python main.py > "$PROJECT_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo "BACKEND_PID=$BACKEND_PID" > "$PID_FILE"
    echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
    
    # Wait for backend to initialize
    sleep 3
    
    # Start Frontend
    echo -e "${GREEN}🌐 Starting React frontend...${NC}"
    cd "$FRONTEND_DIR"
    npm run dev > "$PROJECT_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo "FRONTEND_PID=$FRONTEND_PID" >> "$PID_FILE"
    echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
    
    echo ""
    echo -e "${GREEN}✅ System started successfully!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🔗 Backend API:${NC}       http://localhost:8000"
    echo -e "${GREEN}🔗 API Docs:${NC}          http://localhost:8000/api/docs"
    echo -e "${GREEN}🔗 Frontend:${NC}          http://localhost:8080"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}📋 Logs:${NC}"
    echo -e "  Backend:  tail -f $PROJECT_DIR/backend.log"
    echo -e "  Frontend: tail -f $PROJECT_DIR/frontend.log"
    echo ""
    echo -e "${RED}🛑 To stop: ./manage.sh stop${NC}"
}

stop_services() {
    echo -e "${RED}🛑 Stopping Romanian Admin Platform...${NC}"
    
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}⚠️  No PID file found. Attempting to find and kill processes...${NC}"
        
        # Try to kill by process name
        pkill -f "python main.py"
        pkill -f "vite"
        
        echo -e "${GREEN}✓ Attempted cleanup complete${NC}"
        return
    fi
    
    # Read PIDs from file
    source "$PID_FILE"
    
    # Stop Backend
    if [ ! -z "$BACKEND_PID" ]; then
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping backend (PID: $BACKEND_PID)...${NC}"
            kill $BACKEND_PID 2>/dev/null
            sleep 1
            # Force kill if still running
            if ps -p $BACKEND_PID > /dev/null 2>&1; then
                kill -9 $BACKEND_PID 2>/dev/null
            fi
            echo -e "${GREEN}✓ Backend stopped${NC}"
        else
            echo -e "${YELLOW}Backend process not found${NC}"
        fi
    fi
    
    # Stop Frontend
    if [ ! -z "$FRONTEND_PID" ]; then
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
            kill $FRONTEND_PID 2>/dev/null
            sleep 1
            # Force kill if still running
            if ps -p $FRONTEND_PID > /dev/null 2>&1; then
                kill -9 $FRONTEND_PID 2>/dev/null
            fi
            echo -e "${GREEN}✓ Frontend stopped${NC}"
        else
            echo -e "${YELLOW}Frontend process not found${NC}"
        fi
    fi
    
    # Additional cleanup for any remaining processes
    pkill -f "python main.py" 2>/dev/null
    pkill -f "vite" 2>/dev/null
    
    # Remove PID file
    rm -f "$PID_FILE"
    
    echo -e "${GREEN}✅ System stopped successfully!${NC}"
}

status_services() {
    echo -e "${BLUE}📊 Romanian Admin Platform Status${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${RED}✗ Services are not running (no PID file)${NC}"
        return
    fi
    
    source "$PID_FILE"
    
    # Check Backend
    if [ ! -z "$BACKEND_PID" ] && ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend:${NC}  Running (PID: $BACKEND_PID)"
    else
        echo -e "${RED}✗ Backend:${NC}  Not running"
    fi
    
    # Check Frontend
    if [ ! -z "$FRONTEND_PID" ] && ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend:${NC} Running (PID: $FRONTEND_PID)"
    else
        echo -e "${RED}✗ Frontend:${NC} Not running"
    fi
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

restart_services() {
    echo -e "${YELLOW}🔄 Restarting services...${NC}"
    stop_services
    sleep 2
    start_services
}

# Main script logic
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        status_services
        ;;
    *)
        echo -e "${BLUE}Romanian Admin Platform Management Script${NC}"
        echo ""
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start    - Start backend and frontend services"
        echo "  stop     - Stop all running services"
        echo "  restart  - Restart all services"
        echo "  status   - Check status of services"
        echo ""
        exit 1
        ;;
esac

exit 0
