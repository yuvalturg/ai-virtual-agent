#!/bin/bash

# AI Virtual Agent Test Runner
set -e

echo "🧪 AI Virtual Agent Integration Tests"
echo "====================================="

# Default URLs (can be overridden by environment variables)
FRONTEND_URL=${TEST_FRONTEND_URL:-"http://localhost:5173"}
BACKEND_URL=${TEST_BACKEND_URL:-"http://localhost:8000"}
LLAMASTACK_URL=${TEST_LLAMASTACK_URL:-"http://localhost:8321"}

echo "🔧 Configuration:"
echo "  For postgresql server run: podman compose --file compose.yaml up --detach"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Backend URL: $BACKEND_URL"
echo "  LlamaStack URL: $LLAMASTACK_URL"
echo ""

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
echo "📦 Checking test dependencies..."

# Check if we need to install/update dependencies

echo "📦 Installing/updating test dependencies..."
pip install -r requirements-test.txt --quiet

# Check if services are running
echo "🔍 Checking if services are running..."

# Function to check service
check_service() {
    local name=$1
    local url=$2

    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ $name is running at $url"
        return 0
    else
        echo "❌ $name is not running at $url"
        return 1
    fi
}

# Check all services
services_ok=true

if ! check_service "Backend" "$BACKEND_URL"; then
    services_ok=false
fi

if ! check_service "Frontend" "$FRONTEND_URL"; then
    services_ok=false
fi

if ! check_service "LlamaStack" "$LLAMASTACK_URL"; then
    services_ok=false
fi

# Exit if services are not running
if [[ "$services_ok" == false ]]; then
    echo ""
    echo "❌ Some services are not running. Please start them before running tests."
    echo ""
    echo "To start the services, run:"
    echo "  ./scripts/dev/run_local.sh"
    echo ""
    echo "Or start them individually:"
    echo "  1. podman compose --file compose.yaml up --detach"
    echo "  2. Backend: cd backend && python -m uvicorn main:app --reload --port 8000"
    echo "  3. Frontend: cd frontend && npm run dev"
    echo "  4. LlamaStack: cd scripts/dev/local_llamastack_server && ./activate_llama_server.sh"
    echo ""
    echo "Then run the tests again:"
    echo "  ./run_tests.sh"
    echo ""
    exit 1
fi

echo ""
echo "✅ All services are running!"
echo ""

# Export environment variables for tests
export TEST_FRONTEND_URL="$FRONTEND_URL"
export TEST_BACKEND_URL="$BACKEND_URL"
export TEST_LLAMASTACK_URL="$LLAMASTACK_URL"

# Run tests
echo "🚀 Running integration tests..."

# Check if specific test file was provided
if [[ $# -eq 0 ]]; then
    # Run all integration tests
    pytest tests/integration/ -v
else
    # Run specific test file or pattern
    pytest "$@" -v
fi

echo ""
echo "✅ Tests completed successfully!"
