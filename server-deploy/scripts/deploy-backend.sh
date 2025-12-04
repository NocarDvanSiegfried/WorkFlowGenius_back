#!/bin/bash

set -euo pipefail

BACKEND_DIR="/opt/workflowgenius/backend"
DEPLOY_DIR="/opt/workflowgenius/deploy"
IMAGE_FILE="/tmp/backend-image.tar.gz"
COMPOSE_FILE="$BACKEND_DIR/docker-compose.prod.yml"

echo "Starting backend deployment..."

if [ ! -f "$IMAGE_FILE" ]; then
    echo "Error: Docker image file not found at $IMAGE_FILE"
    exit 1
fi

echo "Loading Docker image..."
docker load -i "$IMAGE_FILE"
rm -f "$IMAGE_FILE"

echo "Updating configuration files..."
if [ -f "$BACKEND_DIR/env.prod.example" ]; then
    if [ ! -f "$BACKEND_DIR/.env.prod" ]; then
        echo "Warning: .env.prod not found. Copying from example..."
        cp "$BACKEND_DIR/env.prod.example" "$BACKEND_DIR/.env.prod"
        echo "Please update .env.prod with actual values before continuing"
    fi
fi

if [ -f "$BACKEND_DIR/docker-compose.prod.yml" ]; then
    echo "docker-compose.prod.yml updated"
fi

echo "Detecting docker compose version..."
if command -v docker > /dev/null && docker compose version > /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose > /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "Error: docker compose or docker-compose not found"
    exit 1
fi

echo "Stopping existing containers..."
cd "$BACKEND_DIR"
if [ -f "$COMPOSE_FILE" ]; then
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" down || true
fi

echo "Starting new containers..."
$DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up -d

echo "Waiting for services to be healthy..."
sleep 10

echo "Checking container status..."
$DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" ps

echo "Checking backend health..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
        echo "Backend is healthy!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for backend to be ready... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Warning: Backend health check failed after $MAX_RETRIES attempts"
    echo "Checking container logs..."
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" logs --tail=50
    exit 1
fi

echo "Cleaning up old Docker images..."
docker image prune -f --filter "until=168h" || true

echo "Backend deployment completed successfully!"
echo "Backend is running at http://localhost:5000"
echo "Health check: http://localhost:5000/api/health"

