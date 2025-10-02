# AUCS 2.0 Deployment Guide

## Overview

This guide covers deploying the AUCS Interactive UI to production using Docker, Nginx, and optional CI/CD.

## Prerequisites

- **Docker** 24.0+ and Docker Compose 2.20+
- **Server**: Linux (Ubuntu 22.04 LTS recommended), 16GB RAM, 100GB disk
- **Domain**: Registered domain with DNS configured (for HTTPS)
- **SSL Certificate**: Let's Encrypt recommended (free, automated)

## Production Architecture

```
Internet
    ↓
Nginx (reverse proxy, SSL termination)
    ↓
Gunicorn (WSGI server, 4 workers)
    ↓
Dash Application (Python)
    ↓
Redis (cache) + DiskCache (fallback)
```

## Deployment Steps

### 1. Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 2. Clone Repository

```bash
# Clone repo
git clone https://github.com/paulaker/Urban_Amenities2.git
cd Urban_Amenities2

# Checkout production branch
git checkout main
```

### 3. Configure Environment

Create `.env` file:

```bash
# Application settings
AUCS_ENV=production
AUCS_HOST=0.0.0.0
AUCS_PORT=8050
AUCS_WORKERS=4
AUCS_SECRET_KEY=<generate-random-secret>

# Cache settings
AUCS_CACHE_BACKEND=redis
AUCS_REDIS_HOST=redis
AUCS_REDIS_PORT=6379

# Data paths
AUCS_DATA_DIR=/app/data
AUCS_OUTPUT_DIR=/app/output
AUCS_CACHE_DIR=/app/.cache

# Logging
AUCS_LOG_LEVEL=INFO
AUCS_LOG_FORMAT=json

# Security
AUCS_ALLOWED_HOSTS=aucs.example.com
AUCS_CORS_ORIGINS=https://aucs.example.com
```

### 4. Prepare Data

```bash
# Create data directories
mkdir -p data/processed output .cache

# Copy AUCS output files
cp /path/to/aucs.parquet output/
cp /path/to/explainability.parquet output/

# Set permissions
chmod -R 755 data output .cache
```

### 5. Configure SSL

#### Option A: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate (interactive)
sudo certbot --nginx -d aucs.example.com

# Auto-renewal (already configured by Certbot)
sudo certbot renew --dry-run
```

#### Option B: Manual Certificate

```bash
# Copy certificate files
mkdir -p deployment/ssl
cp /path/to/fullchain.pem deployment/ssl/cert.pem
cp /path/to/privkey.pem deployment/ssl/key.pem
chmod 600 deployment/ssl/*.pem
```

### 6. Build and Start Services

```bash
# Build Docker images
docker-compose -f deployment/docker-compose.yml build

# Start services
docker-compose -f deployment/docker-compose.yml up -d

# Verify services are running
docker-compose -f deployment/docker-compose.yml ps

# Check logs
docker-compose -f deployment/docker-compose.yml logs -f aucs-ui
```

### 7. Verify Deployment

```bash
# Health check
curl -f http://localhost:8050/health

# Test via Nginx
curl -f https://aucs.example.com/health

# Test full UI
curl -I https://aucs.example.com/
```

Expected response: `HTTP/2 200 OK`

### 8. Configure Firewall

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Verify rules
sudo ufw status
```

## Monitoring

### Application Logs

```bash
# View UI logs
docker-compose -f deployment/docker-compose.yml logs -f aucs-ui

# View Nginx logs
docker-compose -f deployment/docker-compose.yml logs -f nginx

# View Redis logs
docker-compose -f deployment/docker-compose.yml logs -f redis
```

### Health Checks

Set up monitoring with cron:

```bash
# Add to crontab (every 5 minutes)
*/5 * * * * curl -f https://aucs.example.com/health || echo "AUCS health check failed" | mail -s "AUCS Alert" admin@example.com
```

### Performance Monitoring

Install Prometheus + Grafana (optional):

```bash
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./deployment/prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  depends_on:
    - prometheus
```

## Maintenance

### Updating Application

```bash
# Pull latest code
cd Urban_Amenities2
git pull origin main

# Rebuild and restart
docker-compose -f deployment/docker-compose.yml build aucs-ui
docker-compose -f deployment/docker-compose.yml up -d aucs-ui

# Verify
docker-compose -f deployment/docker-compose.yml logs -f aucs-ui
```

### Updating Data

```bash
# Stop UI temporarily
docker-compose -f deployment/docker-compose.yml stop aucs-ui

# Copy new data files
cp /path/to/new/aucs.parquet output/

# Restart UI
docker-compose -f deployment/docker-compose.yml start aucs-ui
```

### Clearing Cache

```bash
# Clear Redis cache
docker-compose -f deployment/docker-compose.yml exec redis redis-cli FLUSHALL

# Clear DiskCache
docker-compose -f deployment/docker-compose.yml exec aucs-ui rm -rf /app/.cache/*

# Restart to rebuild cache
docker-compose -f deployment/docker-compose.yml restart aucs-ui
```

### Backup

```bash
# Backup data directory
tar -czf aucs-backup-$(date +%Y%m%d).tar.gz data/ output/ .cache/

# Backup database (if using PostgreSQL)
docker-compose -f deployment/docker-compose.yml exec postgres pg_dump -U aucs > backup-$(date +%Y%m%d).sql
```

## Scaling

### Horizontal Scaling

To handle more concurrent users:

1. **Increase Gunicorn workers**:

   ```yaml
   # docker-compose.yml
   environment:
     - AUCS_WORKERS=8  # Increase from 4
   ```

2. **Add more UI containers**:

   ```yaml
   # docker-compose.yml
   aucs-ui-2:
     <<: *aucs-ui
     container_name: aucs-ui-2
   ```

3. **Configure Nginx load balancing**:

   ```nginx
   upstream aucs_ui {
       server aucs-ui:8050;
       server aucs-ui-2:8050;
   }
   ```

### Vertical Scaling

Allocate more resources:

```yaml
# docker-compose.yml
services:
  aucs-ui:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f deployment/docker-compose.yml logs aucs-ui

# Common issues:
# - Missing .env file → Create .env with required vars
# - Port conflict → Change AUCS_PORT in .env
# - Permission denied → Fix with: chmod -R 755 data/ output/
```

### 502 Bad Gateway

```bash
# Check if UI container is running
docker-compose -f deployment/docker-compose.yml ps

# Check UI logs
docker-compose -f deployment/docker-compose.yml logs aucs-ui

# Restart Nginx
docker-compose -f deployment/docker-compose.yml restart nginx
```

### Slow Performance

1. **Check Redis**: `docker-compose exec redis redis-cli INFO stats`
2. **Check disk I/O**: `iostat -x 1`
3. **Check memory**: `free -h`
4. **Increase workers**: Edit `AUCS_WORKERS` in `.env`

## Security Checklist

- [x] SSL/TLS enabled (HTTPS only)
- [x] Firewall configured (only 80/443 open)
- [x] Non-root user in Docker containers
- [x] Environment variables for secrets (not hardcoded)
- [x] Rate limiting enabled in Nginx
- [x] Security headers configured (CSP, HSTS, X-Frame-Options)
- [x] Regular updates (OS, Docker, dependencies)
- [x] Backup strategy in place
- [x] Monitoring and alerting configured

## Support

For deployment issues:

- **GitHub Issues**: <https://github.com/paulaker/Urban_Amenities2/issues>
- **Email**: <devops@aucs.example.com>
