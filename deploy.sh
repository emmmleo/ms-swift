#!/bin/bash

# SkyForge Web UI Deployment Script

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting SkyForge Web UI Deployment...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed."
    exit 1
fi

# Create necessary directories
echo -e "${GREEN}Creating directories...${NC}"
mkdir -p output logs

# Build and start services
echo -e "${GREEN}Building and starting services...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose up -d --build
else
    docker compose up -d --build
fi

echo -e "${GREEN}Deployment successful!${NC}"
echo -e "Frontend: http://localhost:8080"
echo -e "Backend:  http://localhost:8000"
echo -e "Use 'docker-compose logs -f' to view logs."
