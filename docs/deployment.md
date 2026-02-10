# Deployment Guide

## Production Deployment

### Prerequisites

- Python 3.8+
- PostgreSQL 12+ (recommended) or MySQL 5.7+
- Redis (optional, for caching)
- Web server (Nginx/Apache)
- WSGI server (Gunicorn/uWSGI)

### Environment Setup

#### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip python3-venv postgresql nginx redis-server

# CentOS/RHEL
sudo yum install python3-pip python3-virtualenv postgresql-server nginx redis
```

#### 2. Create Virtual Environment

```bash
python3 -m venv /var/www/myproject/venv
source /var/www/myproject/venv/bin/activate
```

#### 3. Install Package

```bash
pip install wagtail-subscriptions gunicorn psycopg2-binary
```

### Django Configuration

#### settings/production.py

```python
import os
from .base import *

# Security
DEBUG = False
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# Static files
STATIC_ROOT = '/var/www/myproject/static/'
STATIC_URL = '/static/'

MEDIA_ROOT = '/var/www/myproject/media/'
MEDIA_URL = '/media/'

# Wagtail Subscriptions
WAGTAIL_SUBSCRIPTIONS = {
    'PAYMENT_PROCESSORS': {
        'stripe': {
            'public_key': os.environ['STRIPE_PUBLIC_KEY'],
            'secret_key': os.environ['STRIPE_SECRET_KEY'],
            'webhook_secret': os.environ['STRIPE_WEBHOOK_SECRET'],
        }
    },
    'DEFAULT_PROCESSOR': 'stripe',
}

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
DEFAULT_FROM_EMAIL = os.environ['DEFAULT_FROM_EMAIL']

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/myproject/django.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'wagtail_subscriptions': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Environment Variables

Create `.env` file:

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=myproject.settings.production

# Database
DB_NAME=myproject_db
DB_USER=myproject_user
DB_PASSWORD=secure-password
DB_HOST=localhost
DB_PORT=5432

# Stripe
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Redis
REDIS_URL=redis://127.0.0.1:6379/1
```

### Database Setup

```bash
# Create database
sudo -u postgres psql
CREATE DATABASE myproject_db;
CREATE USER myproject_user WITH PASSWORD 'secure-password';
ALTER ROLE myproject_user SET client_encoding TO 'utf8';
ALTER ROLE myproject_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE myproject_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE myproject_db TO myproject_user;
\q

# Run migrations
python manage.py migrate
python manage.py setup_subscription_permissions
python manage.py collectstatic --noinput
```

### Gunicorn Configuration

Create `/etc/systemd/system/myproject.service`:

```ini
[Unit]
Description=Myproject Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/myproject
EnvironmentFile=/var/www/myproject/.env
ExecStart=/var/www/myproject/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/myproject/myproject.sock \
    --timeout 120 \
    --access-logfile /var/log/myproject/access.log \
    --error-logfile /var/log/myproject/error.log \
    myproject.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start service:

```bash
sudo systemctl start myproject
sudo systemctl enable myproject
```

### Nginx Configuration

Create `/etc/nginx/sites-available/myproject`:

```nginx
upstream myproject {
    server unix:/var/www/myproject/myproject.sock fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/myproject/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/myproject/media/;
        expires 30d;
    }

    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_pass http://myproject;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Celery Setup (Optional)

For background tasks:

#### celery.service

```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/var/www/myproject/.env
WorkingDirectory=/var/www/myproject
ExecStart=/var/www/myproject/venv/bin/celery -A myproject worker \
    --loglevel=info \
    --logfile=/var/log/myproject/celery.log

[Install]
WantedBy=multi-user.target
```

#### celerybeat.service

```ini
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
EnvironmentFile=/var/www/myproject/.env
WorkingDirectory=/var/www/myproject
ExecStart=/var/www/myproject/venv/bin/celery -A myproject beat \
    --loglevel=info \
    --logfile=/var/log/myproject/celerybeat.log

[Install]
WantedBy=multi-user.target
```

Start services:

```bash
sudo systemctl start celery celerybeat
sudo systemctl enable celery celerybeat
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "myproject.wsgi:application"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: myproject_db
      POSTGRES_USER: myproject_user
      POSTGRES_PASSWORD: secure-password
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  web:
    build: .
    command: gunicorn --bind 0.0.0.0:8000 --workers 3 myproject.wsgi:application
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/static
      - media_volume:/app/media
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    restart: unless-stopped

  celery:
    build: .
    command: celery -A myproject worker --loglevel=info
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: unless-stopped

  celerybeat:
    build: .
    command: celery -A myproject beat --loglevel=info
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

Deploy:

```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py setup_subscription_permissions
```

## Monitoring

### Health Check Endpoint

```python
# views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Health check endpoint for monitoring."""
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({'status': 'healthy'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=500)
```

### Monitoring Tools

- **Sentry**: Error tracking
- **New Relic**: Application performance monitoring
- **Prometheus + Grafana**: Metrics and dashboards
- **Uptime Robot**: Uptime monitoring

## Backup Strategy

### Database Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/myproject"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -U myproject_user myproject_db | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

Add to crontab:

```bash
0 2 * * * /var/www/myproject/backup.sh
```

### Media Files Backup

```bash
# Sync to S3
aws s3 sync /var/www/myproject/media/ s3://your-bucket/media/ --delete
```

## Scaling

### Horizontal Scaling

- Use load balancer (AWS ELB, Nginx)
- Multiple application servers
- Shared database and Redis
- Centralized media storage (S3, CloudFront)

### Database Optimization

- Connection pooling (PgBouncer)
- Read replicas
- Query optimization
- Proper indexing

### Caching Strategy

- Redis for session storage
- Cache frequently accessed data
- CDN for static files
- Database query caching

## Security Checklist

- [ ] Use HTTPS everywhere
- [ ] Set secure cookie flags
- [ ] Configure CORS properly
- [ ] Enable CSRF protection
- [ ] Use strong SECRET_KEY
- [ ] Restrict ALLOWED_HOSTS
- [ ] Keep dependencies updated
- [ ] Regular security audits
- [ ] Implement rate limiting
- [ ] Monitor for suspicious activity
