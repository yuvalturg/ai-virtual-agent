#!/bin/bash

# AI Virtual Agent - Development Environment Startup Script
# This script replaces the manual 4-terminal setup with a single command

set -e

# Change to project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$PROJECT_ROOT"
COMPOSE_FILE="$PROJECT_ROOT/deploy/local/compose.yaml"

echo "🚀 Starting AI Virtual Agent Development Environment..."

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    echo "❌ Error: podman is not installed or not in PATH"
    echo "Please install podman to continue"
    exit 1
fi

# Check if podman compose is available
if ! podman compose --help &> /dev/null; then
    echo "❌ Error: podman compose is not available"
    echo "Please ensure you have podman-compose installed"
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env from template..."
    cp .env.example .env
    echo "✅ Created .env - you can customize it if needed"
fi

# Check if attachments should be enabled
ENABLE_ATTACHMENTS=${ENABLE_ATTACHMENTS:-true}
if [ "$ENABLE_ATTACHMENTS" = "true" ]; then
    COMPOSE_PROFILES="--profile attachments"
    echo "📎 Attachments enabled - MinIO will be started"
else
    COMPOSE_PROFILES=""
    echo "📎 Attachments disabled - MinIO will be skipped"
    export DISABLE_ATTACHMENTS=true
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
podman compose -f "$COMPOSE_FILE" $COMPOSE_PROFILES down --remove-orphans

# Start all services
echo "🏗️  Building and starting all services..."
podman compose -f "$COMPOSE_FILE" $COMPOSE_PROFILES up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "📊 Service Status:"
podman compose -f "$COMPOSE_FILE" $COMPOSE_PROFILES ps

# Show helpful information
echo ""
echo "🎉 Development environment is ready!"
echo ""
echo "📍 Service URLs:"
echo "   Frontend:    http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   Database:    postgresql://admin:password@localhost:5432/ai_virtual_agent"
echo "   LlamaStack:  http://localhost:8321"
if [ "$ENABLE_ATTACHMENTS" = "true" ]; then
    echo "   MinIO:       http://localhost:9000"
    echo "   MinIO Console: http://localhost:9001 (admin: minio_rag_user/minio_rag_password)"
fi
echo ""
echo "📚 Useful commands:"
echo "   View logs:      podman compose -f compose.yaml logs -f"
echo "   Stop services:  ./scripts/stop-dev.sh"
echo "   Restart:        podman compose -f compose.yaml restart [service]"
echo ""
echo "🔧 Development features:"
echo "   ✅ Hot reload enabled for backend and frontend"
echo "   ✅ Database persisted in volume"
echo "   ✅ Auto-migrations run on startup"
echo ""
