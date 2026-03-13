# ============================================================
# Consolidated Dockerfile — Frontend + Backend + Nginx
# ============================================================
# Multi-stage build:
#   1. Build React frontend
#   2. Build Python backend
#   3. Combined with Nginx as reverse proxy
# ============================================================

# Stage 1: Build React Frontend
FROM node:18-alpine as frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./

RUN npm ci --only=production --silent

COPY frontend/ .

RUN npm run build

# Stage 2: Backend base
FROM python:3.12-slim as backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/farmxpert/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Production - Nginx + Backend
FROM python:3.12-slim

# Install Nginx and dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/

WORKDIR /app

# Copy Python dependencies from backend-builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend application
COPY backend/farmxpert/ ./farmxpert/
COPY backend/alembic/ ./alembic/
COPY backend/alembic.ini .

# Copy built frontend to nginx html directory
COPY --from=frontend-builder /frontend/build /usr/share/nginx/html

# Copy nginx configuration
COPY frontend/nginx.conf /etc/nginx/nginx.conf

# Create supervisor log directory
RUN mkdir -p /var/log/supervisor

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose the Railway port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
