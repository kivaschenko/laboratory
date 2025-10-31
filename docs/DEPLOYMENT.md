# Deployment Guide

This guide covers different deployment strategies for the Laboratory Management System.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Database Setup](#database-setup)
7. [Environment Configuration](#environment-configuration)
8. [Security Considerations](#security-considerations)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Backup and Recovery](#backup-and-recovery)

## Prerequisites

- Python 3.10+ 
- PostgreSQL 13+ (for production) or SQLite (for development)
- Web server (nginx, Apache) for production
- SSL certificate for HTTPS
- Minimum 1GB RAM, 2GB recommended
- 10GB+ storage space

## Development Deployment

### Quick Start
```bash
# Clone repository
git clone https://github.com/kivaschenko/laboratory.git
cd laboratory

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[testing,development]"

# Set environment variables
cp .env.example .env
# Edit .env with your settings

# Initialize database
alembic upgrade head
initialize_laboratory_db development.ini

# Run development server
pserve development.ini --reload
```

### Development with Docker
```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec web alembic upgrade head
docker-compose exec web initialize_laboratory_db development.ini
```

## Production Deployment

### 1. Server Setup (Ubuntu/Debian)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip nginx postgresql postgresql-contrib supervisor

# Create application user
sudo useradd -m -s /bin/bash laboratory
sudo usermod -aG sudo laboratory

# Create application directory
sudo mkdir -p /opt/laboratory
sudo chown laboratory:laboratory /opt/laboratory
```

### 2. Application Setup
```bash
# Switch to application user
sudo su - laboratory

# Navigate to application directory
cd /opt/laboratory

# Clone repository
git clone https://github.com/kivaschenko/laboratory.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Create configuration
cp .env.example .env
# Edit .env with production settings
```

### 3. Database Setup
```bash
# Create PostgreSQL database
sudo -u postgres psql
```
```sql
CREATE DATABASE laboratory;
CREATE USER laboratory WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE laboratory TO laboratory;
\q
```

### 4. Web Server Configuration

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/laboratory
server {
    listen 80;
    server_name laboratory.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name laboratory.yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    client_max_body_size 50M;

    location /static/ {
        alias /opt/laboratory/laboratory/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:6543;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/laboratory /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Process Management with Supervisor
```ini
# /etc/supervisor/conf.d/laboratory.conf
[program:laboratory]
command=/opt/laboratory/venv/bin/pserve /opt/laboratory/production.ini
directory=/opt/laboratory
user=laboratory
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/laboratory/laboratory.log
environment=
    PATH="/opt/laboratory/venv/bin",
    AUTH_SECRET="your-secure-secret-key",
    SQLALCHEMY_URL="postgresql://laboratory:secure_password@localhost:5432/laboratory"
```

```bash
# Create log directory
sudo mkdir -p /var/log/laboratory
sudo chown laboratory:laboratory /var/log/laboratory

# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start laboratory
```

## Docker Deployment

### Production with Docker Compose
```bash
# Create production environment file
cp .env.example .env.production
# Edit with production values

# Deploy with production compose
docker-compose -f docker-compose.prod.yml up -d

# Initialize database
docker-compose -f docker-compose.prod.yml exec web alembic upgrade head
docker-compose -f docker-compose.prod.yml exec web initialize_laboratory_db production.ini
```

### Docker Swarm Deployment
```yaml
# docker-stack.yml
version: '3.8'

services:
  web:
    image: laboratory:latest
    ports:
      - "80:6543"
    environment:
      - SQLALCHEMY_URL=postgresql://laboratory:${DB_PASSWORD}@db:5432/laboratory
      - AUTH_SECRET=${AUTH_SECRET}
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    volumes:
      - laboratory_data:/app/data
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=laboratory
      - POSTGRES_USER=laboratory
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      replicas: 1
      placement:
        constraints: [node.role == manager]

volumes:
  postgres_data:
  laboratory_data:
```

```bash
# Deploy stack
docker stack deploy -c docker-stack.yml laboratory
```

## Cloud Deployment

### AWS Deployment
```bash
# Using AWS ECS with Fargate
aws ecs create-cluster --cluster-name laboratory

# Create task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service --cluster laboratory --service-name laboratory-service \
  --task-definition laboratory:1 --desired-count 2
```

### Google Cloud Platform
```bash
# Deploy to Cloud Run
gcloud run deploy laboratory \
  --image gcr.io/your-project/laboratory \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Heroku Deployment
```bash
# Create Heroku app
heroku create laboratory-app

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set AUTH_SECRET=your-secret-key

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head
heroku run initialize_laboratory_db production.ini
```

## Environment Configuration

### Required Environment Variables
```bash
# Database
SQLALCHEMY_URL=postgresql://user:pass@host:port/db

# Security
AUTH_SECRET=very-secure-random-string

# Admin User
ADMIN_EMAIL=admin@laboratory.com
ADMIN_PASSWORD=secure-password

# Application
PYRAMID_DEBUG=false
PYRAMID_RELOAD_TEMPLATES=false
```

### Production Environment File
```bash
# .env.production
SQLALCHEMY_URL=postgresql://laboratory:${DB_PASSWORD}@db.internal:5432/laboratory
AUTH_SECRET=${AUTH_SECRET}
ADMIN_EMAIL=admin@laboratory.com
ADMIN_PASSWORD=${ADMIN_PASSWORD}
PYRAMID_DEBUG=false
PYRAMID_RELOAD_TEMPLATES=false
SERVER_HOST=0.0.0.0
SERVER_PORT=6543
LOG_LEVEL=INFO
```

## Security Considerations

### SSL/TLS Configuration
- Use TLS 1.2 or higher
- Implement HSTS headers
- Use strong cipher suites
- Regular certificate renewal

### Application Security
- Strong authentication secrets
- Regular security updates
- Input validation and sanitization
- Rate limiting
- CSRF protection (built-in)

### Database Security
- Encrypted connections
- Strong passwords
- Regular backups
- Access logging
- Network isolation

### System Security
```bash
# Firewall configuration
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Fail2ban for SSH protection
sudo apt install fail2ban
```

## Monitoring and Logging

### Application Logs
```python
# logging.conf
[loggers]
keys = root, laboratory

[handlers]
keys = console, file

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console, file

[logger_laboratory]
level = DEBUG
handlers = file
qualname = laboratory

[handler_console]
class = StreamHandler
args = (sys.stderr,)
formatter = generic

[handler_file]
class = FileHandler
args = ('/var/log/laboratory/laboratory.log',)
formatter = generic

[formatter_generic]
format = %(asctime)s %(levelname)-5.5s [%(name)s] %(message)s
```

### System Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop netstat-nat

# Monitor logs
tail -f /var/log/laboratory/laboratory.log
tail -f /var/log/nginx/access.log
tail -f /var/log/postgresql/postgresql-13-main.log
```

### Health Checks
```bash
# Application health check
curl -f http://localhost:6543/health || exit 1

# Database health check
pg_isready -h localhost -p 5432 -U laboratory
```

## Backup and Recovery

### Database Backup
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
DB_NAME="laboratory"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database dump
pg_dump -h localhost -U laboratory $DB_NAME | gzip > $BACKUP_DIR/laboratory_$DATE.sql.gz

# Keep only last 30 days of backups
find $BACKUP_DIR -name "laboratory_*.sql.gz" -mtime +30 -delete

echo "Backup completed: laboratory_$DATE.sql.gz"
```

```bash
# Schedule backups
# Add to crontab: crontab -e
0 2 * * * /opt/laboratory/scripts/backup.sh
```

### Application Backup
```bash
#!/bin/bash
# backup-app.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
APP_DIR="/opt/laboratory"

# Backup configuration and data
tar -czf $BACKUP_DIR/laboratory_app_$DATE.tar.gz \
  $APP_DIR/.env \
  $APP_DIR/laboratory/static/ \
  $APP_DIR/uploads/ \
  $APP_DIR/logs/

echo "Application backup completed: laboratory_app_$DATE.tar.gz"
```

### Recovery Procedures
```bash
# Database recovery
gunzip -c laboratory_20240101_020000.sql.gz | psql -h localhost -U laboratory laboratory

# Application recovery
tar -xzf laboratory_app_20240101_020000.tar.gz -C /
sudo systemctl restart laboratory
```

## Performance Optimization

### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_substances_name ON substances(name);
CREATE INDEX idx_solutions_normative ON solutions(normative);
CREATE INDEX idx_analysis_recipe_name ON analysis(recipe_name);
CREATE INDEX idx_stock_substance_name ON stock(substance_name);
```

### Application Optimization
```ini
# production.ini optimizations
[app:main]
pyramid.reload_templates = false
pyramid.debug_authorization = false
pyramid.debug_notfound = false
pyramid.debug_routematch = false

# Database connection pooling
sqlalchemy.pool_size = 10
sqlalchemy.max_overflow = 20
sqlalchemy.pool_timeout = 30
sqlalchemy.pool_recycle = 3600
```

### Web Server Optimization
```nginx
# Nginx optimizations
worker_processes auto;
worker_connections 1024;

gzip on;
gzip_vary on;
gzip_comp_level 6;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/javascript
    application/xml+rss
    application/json;
```

## Troubleshooting

### Common Issues
1. **Database connection errors**: Check credentials and network connectivity
2. **Permission errors**: Verify file permissions and user ownership
3. **Memory issues**: Monitor RAM usage and adjust as needed
4. **SSL certificate issues**: Check certificate validity and configuration

### Debug Mode
```bash
# Enable debug mode temporarily
export PYRAMID_DEBUG=true
pserve development.ini --reload
```

### Log Analysis
```bash
# Check application logs
grep ERROR /var/log/laboratory/laboratory.log

# Check system logs
journalctl -u laboratory -f

# Check nginx logs
tail -f /var/log/nginx/error.log
```

## Scaling Considerations

### Horizontal Scaling
- Load balancer configuration
- Session sharing (Redis/Memcached)
- Database read replicas
- CDN for static assets

### Vertical Scaling
- Increase server resources
- Database optimization
- Application profiling
- Caching strategies

This deployment guide provides comprehensive instructions for deploying the Laboratory Management System in various environments. Choose the deployment method that best fits your infrastructure and requirements.