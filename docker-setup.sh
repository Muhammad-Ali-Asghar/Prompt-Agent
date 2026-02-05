#!/bin/bash

# Prompt RAG Agent - Docker Setup Script

set -e

echo "🚀 Setting up Prompt RAG Agent with Docker..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your GOOGLE_API_KEY before running docker-compose"
    echo ""
    echo "   Edit with: nano .env"
    echo "   Then run:  docker-compose up --build"
    exit 1
fi

# Check if GOOGLE_API_KEY is set
if grep -q "your-google-api-key-here" .env; then
    echo "⚠️  Please set your GOOGLE_API_KEY in .env file"
    echo "   Edit with: nano .env"
    exit 1
fi

echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "✅ Prompt RAG Agent is starting!"
echo ""
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Useful commands:"
echo "   View logs:     docker-compose logs -f"
echo "   Stop:          docker-compose down"
echo "   Rebuild:       docker-compose up --build -d"
echo ""
