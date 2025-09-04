#!/bin/bash

# Development utility script for OptiBet Soccer Betting ML Optimizer
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Setup virtual environment
setup_venv() {
    print_info "Setting up Python virtual environment..."
    if [ ! -d "venv" ]; then
        python3.10 -m venv venv || python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    source venv/bin/activate || source venv/Scripts/activate
    pip install --upgrade pip
    print_success "Virtual environment activated and pip upgraded"
}

# Install dependencies
install_deps() {
    print_info "Installing dependencies..."
    source venv/bin/activate || source venv/Scripts/activate
    
    # Install main dependencies
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    
    # Install services dependencies
    for service in app-backend app-frontend data-ingestion pipelines; do
        if [ -f "$service/requirements.txt" ]; then
            print_info "Installing dependencies for $service"
            pip install -r "$service/requirements.txt"
        fi
    done
    
    # Install optibet_lib in development mode
    print_info "Installing optibet_lib in development mode"
    cd optibet_lib
    pip install -e .
    cd ..
    
    print_success "All dependencies installed"
}

# Setup pre-commit hooks
setup_precommit() {
    print_info "Setting up pre-commit hooks..."
    source venv/bin/activate || source venv/Scripts/activate
    pre-commit install
    print_success "Pre-commit hooks installed"
}

# Run code formatting
format_code() {
    print_info "Formatting code..."
    source venv/bin/activate || source venv/Scripts/activate
    
    print_info "Running Black..."
    black .
    
    print_info "Running isort..."
    isort .
    
    print_success "Code formatted"
}

# Run linting
lint_code() {
    print_info "Linting code..."
    source venv/bin/activate || source venv/Scripts/activate
    
    print_info "Running flake8..."
    flake8 . || print_warning "Flake8 found issues"
    
    print_info "Running mypy..."
    mypy . --config-file pyproject.toml || print_warning "MyPy found issues"
    
    print_info "Running bandit security check..."
    bandit -r . -f json -o bandit-report.json || print_warning "Bandit found security issues"
    
    print_success "Linting completed"
}

# Run tests
run_tests() {
    print_info "Running tests..."
    source venv/bin/activate || source venv/Scripts/activate
    
    # Run tests for each service
    for service in app-backend data-ingestion; do
        if [ -d "$service/tests" ]; then
            print_info "Running tests for $service"
            cd "$service"
            pytest tests/ -v --cov=. --cov-report=term-missing || print_warning "Tests failed for $service"
            cd ..
        fi
    done
    
    print_success "Tests completed"
}

# Build Docker images
build_docker() {
    print_info "Building Docker images..."
    
    if command_exists docker; then
        make build
        print_success "Docker images built"
    else
        print_error "Docker not found. Please install Docker."
        exit 1
    fi
}

# Start local development
start_dev() {
    print_info "Starting local development environment..."
    
    # Load environment variables
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
    fi
    
    if [ -f "secrets.env" ]; then
        set -a
        source secrets.env
        set +a
    fi
    
    source venv/bin/activate || source venv/Scripts/activate
    make start
    
    print_success "Development environment started"
    print_info "Frontend available at: http://localhost:${APP_FRONTEND_PORT:-8204}"
    print_info "Backend API docs at: http://localhost:${APP_BACKEND_PORT:-8203}/docs"
    print_info "Data Ingestion API docs at: http://localhost:${DATA_INGESTION_PORT:-8200}/docs"
}

# Stop local development
stop_dev() {
    print_info "Stopping local development environment..."
    make stop
    print_success "Development environment stopped"
}

# Clean up
cleanup() {
    print_info "Cleaning up..."
    
    # Remove Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Remove coverage files
    find . -name ".coverage" -delete 2>/dev/null || true
    find . -name "coverage.xml" -delete 2>/dev/null || true
    find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
    
    # Remove mypy cache
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Show help
show_help() {
    echo "OptiBet Development Script"
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup        - Complete setup (venv, deps, pre-commit)"
    echo "  venv         - Setup virtual environment"
    echo "  deps         - Install dependencies"
    echo "  precommit    - Setup pre-commit hooks"
    echo "  format       - Format code with Black and isort"
    echo "  lint         - Run linting (flake8, mypy, bandit)"
    echo "  test         - Run all tests"
    echo "  check        - Run format, lint, and test"
    echo "  build        - Build Docker images"
    echo "  start        - Start local development environment"
    echo "  stop         - Stop local development environment"
    echo "  clean        - Clean up cache files"
    echo "  help         - Show this help message"
    echo ""
}

# Main command handling
case "${1:-help}" in
    setup)
        setup_venv
        install_deps
        setup_precommit
        print_success "Setup completed!"
        ;;
    venv)
        setup_venv
        ;;
    deps)
        install_deps
        ;;
    precommit)
        setup_precommit
        ;;
    format)
        format_code
        ;;
    lint)
        lint_code
        ;;
    test)
        run_tests
        ;;
    check)
        format_code
        lint_code
        run_tests
        ;;
    build)
        build_docker
        ;;
    start)
        start_dev
        ;;
    stop)
        stop_dev
        ;;
    clean)
        cleanup
        ;;
    help|*)
        show_help
        ;;
esac