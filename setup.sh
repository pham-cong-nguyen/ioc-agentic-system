#!/bin/bash

# IOC Agentic System - Quick Setup Script
# This script sets up the development environment

set -e

echo "🚀 IOC Agentic System - Setup Script"
echo "===================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}❌ Please do not run this script as root${NC}"
    exit 1
fi

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    echo -e "${BLUE}➜${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION found"

if ! command_exists docker; then
    print_warning "Docker not found - Docker setup will be skipped"
    DOCKER_AVAILABLE=false
else
    print_success "Docker found"
    DOCKER_AVAILABLE=true
fi

if ! command_exists docker-compose; then
    print_warning "Docker Compose not found - Docker setup will be skipped"
    DOCKER_COMPOSE_AVAILABLE=false
else
    print_success "Docker Compose found"
    DOCKER_COMPOSE_AVAILABLE=true
fi

echo ""

# Ask setup preference
echo "Choose setup method:"
echo "1) Docker Compose (Recommended - includes PostgreSQL & Redis)"
echo "2) Local Development (requires manual PostgreSQL & Redis setup)"
echo "3) Exit"
echo ""
read -p "Enter choice [1-3]: " setup_choice

case $setup_choice in
    1)
        if [ "$DOCKER_AVAILABLE" = false ] || [ "$DOCKER_COMPOSE_AVAILABLE" = false ]; then
            print_error "Docker or Docker Compose not available"
            exit 1
        fi
        
        print_status "Setting up with Docker Compose..."
        
        # Create .env file if not exists
        if [ ! -f .env ]; then
            print_status "Creating .env file..."
            cp .env.example .env
            print_success ".env file created"
            print_warning "Please edit .env file and add your API keys:"
            echo "  - GOOGLE_API_KEY (for Gemini)"
            echo "  - Or OPENAI_API_KEY (for GPT)"
            echo "  - Or ANTHROPIC_API_KEY (for Claude)"
            echo ""
            read -p "Press Enter to continue after editing .env..."
        else
            print_success ".env file already exists"
        fi
        
        # Build and start containers
        print_status "Building Docker images..."
        docker-compose build
        print_success "Docker images built"
        
        print_status "Starting services..."
        docker-compose up -d
        print_success "Services started"
        
        # Wait for services to be ready
        print_status "Waiting for services to be ready..."
        sleep 10
        
        # Initialize database
        print_status "Initializing database..."
        docker-compose exec -T backend python scripts/init_db.py
        print_success "Database initialized"
        
        echo ""
        print_success "Setup complete! 🎉"
        echo ""
        echo "Services running:"
        echo "  - Backend API: http://localhost:8862"
        echo "  - API Docs: http://localhost:8862/api/v1/docs"
        echo "  - Frontend: http://localhost:80"
        echo "  - PostgreSQL: localhost:5432"
        echo "  - Redis: localhost:6379"
        echo ""
        echo "Useful commands:"
        echo "  - View logs: docker-compose logs -f"
        echo "  - Stop services: docker-compose down"
        echo "  - Restart: docker-compose restart"
        ;;
        
    2)
        print_status "Setting up local development environment..."
        
        # Check if venv exists
        if [ ! -d "venv" ]; then
            print_status "Creating virtual environment..."
            python3 -m venv venv
            print_success "Virtual environment created"
        else
            print_success "Virtual environment already exists"
        fi
        
        # Activate virtual environment
        print_status "Activating virtual environment..."
        source venv/bin/activate
        
        # Install dependencies
        print_status "Installing Python dependencies..."
        pip install --upgrade pip
        pip install -r backend/requirements.txt
        print_success "Dependencies installed"
        
        # Create .env file if not exists
        if [ ! -f .env ]; then
            print_status "Creating .env file..."
            cp .env.example .env
            
            # Set local database defaults
            sed -i 's/POSTGRES_HOST=postgres/POSTGRES_HOST=localhost/' .env
            sed -i 's/REDIS_HOST=redis/REDIS_HOST=localhost/' .env
            
            print_success ".env file created"
        fi
        
        echo ""
        print_warning "Manual steps required:"
        echo ""
        echo "1. Start PostgreSQL:"
        echo "   sudo systemctl start postgresql"
        echo "   OR"
        echo "   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=ioc_password --name ioc-postgres postgres:15"
        echo ""
        echo "2. Start Redis:"
        echo "   sudo systemctl start redis"
        echo "   OR"
        echo "   docker run -d -p 6379:6379 --name ioc-redis redis:7-alpine"
        echo ""
        echo "3. Edit .env file and add your API keys:"
        echo "   - GOOGLE_API_KEY (for Gemini)"
        echo "   - Or OPENAI_API_KEY (for GPT)"
        echo "   - Or ANTHROPIC_API_KEY (for Claude)"
        echo ""
        echo "4. Initialize database:"
        echo "   python scripts/init_db.py"
        echo ""
        echo "5. Start the application:"
        echo "   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8862"
        echo ""
        ;;
        
    3)
        print_status "Exiting..."
        exit 0
        ;;
        
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac
