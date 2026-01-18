# Deployment Guide - AI-Powered LMS

This guide covers deploying the AI-Powered LMS to production using **Vercel** (frontend), **Fly.io** (backend), and **Supabase** (PostgreSQL database).

## Current Production Deployment

| Service | Platform | URL |
|---------|----------|-----|
| Frontend | Vercel | https://fyp-ai-lms.vercel.app |
| Backend | Fly.io | https://fyp-ai-lms-backend.fly.dev |
| Database | Supabase | PostgreSQL (Singapore region) |

---

## Option 1: Cloud Deployment (Recommended)

### Prerequisites
- GitHub account with repository access
- Vercel account (free tier)
- Fly.io account (free tier)
- Supabase account (free tier)

### Step 1: Set Up Supabase Database

1. Create a new project at [supabase.com](https://supabase.com)
2. Choose a region close to your users (e.g., Singapore)
3. Copy the connection string from Settings → Database:
   ```
   postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
   ```
4. **Important:** URL-encode special characters in password (e.g., `@` → `%40`)

### Step 2: Deploy Backend to Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Navigate to backend
cd backend

# Create app (first time only)
fly apps create fyp-ai-lms-backend

# Set secrets
fly secrets set DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres"
fly secrets set SECRET_KEY="your-secure-secret-key"
fly secrets set HUGGINGFACE_API_TOKEN="hf_xxx"

# Deploy
fly deploy --wait-timeout 300
```

### Step 3: Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com) → Add New Project
2. Import your GitHub repository: `NGJIERU/fyp-ai-lms`
3. Configure:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Next.js
4. Add Environment Variable:
   - `NEXT_PUBLIC_API_BASE_URL` = `https://fyp-ai-lms-backend.fly.dev`
5. Click Deploy

### Step 4: Seed Database

```bash
# SSH into Fly.io and run seed script
fly ssh console --app fyp-ai-lms-backend -C "python /app/scripts/seeds/setup_demo.py"
```

---

## Option 2: Traditional VM Deployment

> For deploying to a self-managed Ubuntu server with Nginx.

### Prerequisites

- Ubuntu 22.04 LTS (or similar)
- Domain name pointing to your server
- SSH access to the server

## 1. Server Setup

### Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx
```

### Install PostgreSQL
```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create Database
```bash
sudo -u postgres psql

CREATE USER lms_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE lms_db OWNER lms_user;
GRANT ALL PRIVILEGES ON DATABASE lms_db TO lms_user;
\q
```

## 2. Application Setup

### Create Application User
```bash
sudo useradd -m -s /bin/bash lms
sudo su - lms
```

### Clone Repository
```bash
git clone <your-repo-url> ~/lms-app
cd ~/lms-app
```

### Create Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Configure Environment
```bash
cat > .env << EOF
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=lms_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=lms_db

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Services (Optional)
OPENAI_API_KEY=sk-your-openai-key
YOUTUBE_API_KEY=your-youtube-api-key
GITHUB_ACCESS_TOKEN=your-github-token
EOF

chmod 600 .env
```

### Run Migrations
```bash
alembic upgrade head
```

### Seed Initial Data
```bash
python seed_courses_syllabus.py
```

### Test Application
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
# Test in another terminal: curl http://127.0.0.1:8000/
```

## 3. Systemd Service

### Create Service File
```bash
sudo tee /etc/systemd/system/lms.service << EOF
[Unit]
Description=AI-Powered LMS FastAPI Application
After=network.target postgresql.service

[Service]
User=lms
Group=lms
WorkingDirectory=/home/lms/lms-app
Environment="PATH=/home/lms/lms-app/venv/bin"
EnvironmentFile=/home/lms/lms-app/.env
ExecStart=/home/lms/lms-app/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable lms
sudo systemctl start lms
sudo systemctl status lms
```

## 4. Nginx Configuration

### Create Nginx Config
```bash
sudo tee /etc/nginx/sites-available/lms << EOF
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # API documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    # Static files (if any)
    location /static {
        alias /home/lms/lms-app/static;
        expires 30d;
    }

    client_max_body_size 50M;
}
EOF
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/lms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 5. SSL/HTTPS with Let's Encrypt

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot will automatically:
- Obtain SSL certificate
- Configure Nginx for HTTPS
- Set up auto-renewal

### Verify Auto-Renewal
```bash
sudo certbot renew --dry-run
```

## 6. Firewall Configuration

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## 7. Monitoring & Logging

### View Application Logs
```bash
sudo journalctl -u lms -f
```

### View Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Setup Log Rotation
```bash
sudo tee /etc/logrotate.d/lms << EOF
/var/log/lms/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 lms lms
    sharedscripts
    postrotate
        systemctl reload lms > /dev/null 2>&1 || true
    endscript
}
EOF
```

## 8. Database Backup

### Create Backup Script
```bash
sudo tee /home/lms/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/lms/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U lms_user lms_db > $BACKUP_DIR/lms_db_$TIMESTAMP.sql

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "Backup completed: lms_db_$TIMESTAMP.sql"
EOF

chmod +x /home/lms/backup.sh
```

### Schedule Daily Backup
```bash
(crontab -l 2>/dev/null; echo "0 2 * * * /home/lms/backup.sh") | crontab -
```

## 9. Docker Deployment (Alternative)

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_SERVER=db
      - POSTGRES_USER=lms_user
      - POSTGRES_PASSWORD=your_password
      - POSTGRES_DB=lms_db
      - SECRET_KEY=your-secret-key
    depends_on:
      - db
    restart: always

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=lms_user
      - POSTGRES_PASSWORD=your_password
      - POSTGRES_DB=lms_db
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/letsencrypt
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
```

### Deploy with Docker
```bash
docker-compose up -d
docker-compose logs -f
```

## 10. Health Checks

### Create Health Check Endpoint
The API already has a root endpoint. You can also add:

```python
# In app/main.py
@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}
```

### Monitor with Uptime Service
- Use services like UptimeRobot, Pingdom, or self-hosted alternatives
- Monitor: `https://your-domain.com/health`

## 11. Performance Tuning

### PostgreSQL Tuning
Edit `/etc/postgresql/15/main/postgresql.conf`:
```
shared_buffers = 256MB
effective_cache_size = 768MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 16MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 4
max_parallel_workers_per_gather = 2
max_parallel_workers = 4
```

### Uvicorn Workers
Adjust workers based on CPU cores:
```
workers = (2 * CPU_CORES) + 1
```

## 12. Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong database password
- [ ] Enable firewall (UFW)
- [ ] Configure HTTPS
- [ ] Set up fail2ban
- [ ] Regular security updates
- [ ] Database backups
- [ ] Log monitoring
- [ ] Rate limiting (Nginx)

## Troubleshooting

### Application Won't Start
```bash
sudo journalctl -u lms -n 50
```

### Database Connection Issues
```bash
sudo -u postgres psql -c "SELECT 1;"
```

### Nginx 502 Bad Gateway
```bash
sudo systemctl status lms
curl http://127.0.0.1:8000/
```

### Permission Issues
```bash
sudo chown -R lms:lms /home/lms/lms-app
```
