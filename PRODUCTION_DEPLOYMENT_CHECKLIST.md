# Production Deployment Checklist

## Pre-Deployment Phase

### 1. Code Review & Testing
- [ ] All performance optimization code reviewed
- [ ] Unit tests passing: `pytest backend/tests/`
- [ ] Integration tests passing
- [ ] Load testing completed (see benchmark.py)
- [ ] No breaking changes to existing APIs
- [ ] All docstrings and comments complete
- [ ] Code follows project style guide

### 2. Security Review
- [ ] CORS properly configured for production domains
- [ ] Redis password set (not blank)
- [ ] PostgreSQL password strong and updated
- [ ] API rate limiting enabled (100 req/min)
- [ ] SQL injection prevention verified (using parameterized queries)
- [ ] HTTPS/TLS certificates prepared
- [ ] Environment variables not committed to git
- [ ] Sensitive data not logged

### 3. Infrastructure Preparation
- [ ] Production server specs validated
  - [ ] CPU: 4+ cores
  - [ ] RAM: 16GB+ 
  - [ ] Disk: 100GB+ SSD
  - [ ] Network: 100 Mbps+ connection
- [ ] Docker and Docker Compose installed
- [ ] PostgreSQL 15+ available
- [ ] Redis 7+ available
- [ ] Node.js 18+ installed (for Express backend)
- [ ] Python 3.9+ installed
- [ ] Reverse proxy (Nginx) configured

### 4. Configuration Preparation
- [ ] Production `.env` file created with secure values
- [ ] Redis broker URL verified
- [ ] Database connection string correct
- [ ] Celery configuration reviewed
- [ ] Logging configured for production
- [ ] Email service configured (for alerts)
- [ ] CDN URLs configured (if using external CDN)
- [ ] S3/storage backend configured (if needed)

---

## Deployment Phase

### 5. Database Deployment

```bash
# 1. Backup existing database (if applicable)
PGPASSWORD=postgres pg_dump -h localhost -U postgres price_intelligence > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Create database if new
PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE price_intelligence;"

# 3. Apply performance optimization migration
PGPASSWORD=postgres psql -h localhost -U postgres -d price_intelligence < backend-express/db/00_performance_optimization.sql

# 4. Verify indexes created
PGPASSWORD=postgres psql -h localhost -U postgres -d price_intelligence << EOF
SELECT schemaname, tablename, indexname FROM pg_indexes 
WHERE schemaname='public' ORDER BY tablename;
EOF
```

**Checklist:**
- [ ] Database created successfully
- [ ] All tables created
- [ ] All indexes created (9+ total)
- [ ] Constraints applied
- [ ] ANALYZE completed
- [ ] Backup verified

### 6. Redis Deployment

```bash
# 1. Start Redis with persistence
docker run -d -p 6379:6379 \
  -v /data/redis:/data \
  --name redis-cache \
  redis:7-alpine redis-server --appendonly yes

# 2. Verify connection
redis-cli ping

# 3. Set requirepass (optional but recommended)
redis-cli CONFIG SET requirepass "your-secure-password"
```

**Checklist:**
- [ ] Redis container running
- [ ] Data persistence enabled (appendonly yes)
- [ ] Password configured (if required)
- [ ] Memory limits set: `MAXMEMORY 2gb`
- [ ] Eviction policy set: `MAXMEMORY-POLICY allkeys-lru`

### 7. Backend Deployment

```bash
# 1. Build Python backend image
docker build -t price-intel-backend:latest backend/

# 2. Start backend service
docker run -d -p 8000:8000 \
  --name backend-api \
  --env-file .env \
  -e POSTGRES_HOST=<production-db-host> \
  -e REDIS_HOST=<production-redis-host> \
  price-intel-backend:latest

# 3. Health check
curl http://localhost:8000/api/metrics
```

**Checklist:**
- [ ] Docker image built successfully
- [ ] All environment variables set
- [ ] Service running on port 8000
- [ ] Health endpoints responding
- [ ] Logs clean (no errors)

### 8. Celery Deployment

```bash
# 1. Build Celery worker image
docker build -t price-intel-celery:latest backend/

# 2. Start Celery worker
docker run -d \
  --name celery-worker \
  --env-file .env \
  -e POSTGRES_HOST=<production-db-host> \
  -e REDIS_HOST=<production-redis-host> \
  price-intel-celery:latest \
  celery -A app.celery_app worker \
    --concurrency=4 \
    --loglevel=info

# 3. Start Celery beat scheduler
docker run -d \
  --name celery-beat \
  --env-file .env \
  -e POSTGRES_HOST=<production-db-host> \
  -e REDIS_HOST=<production-redis-host> \
  price-intel-celery:latest \
  celery -A app.celery_app beat \
    --loglevel=info
```

**Checklist:**
- [ ] Celery worker running with 4+ concurrency
- [ ] Celery beat scheduler running
- [ ] Tasks visible in Flower (`http://localhost:5555`)
- [ ] No failed task logs
- [ ] Periodic tasks scheduled

### 9. Frontend Deployment

```bash
# 1. Build production bundle
cd frontend
npm install --production
npm run build
# Output: dist/

# 2. Build frontend image
docker build -t price-intel-frontend:latest .

# 3. Start frontend service
docker run -d -p 5173:5173 \
  --name frontend \
  --env-file .env \
  price-intel-frontend:latest
```

**Checklist:**
- [ ] Build completes without errors
- [ ] Bundle size < 500KB (with code splitting)
- [ ] No console errors in browser
- [ ] Lazy loading components working
- [ ] Images optimized (WebP served where supported)

### 10. Reverse Proxy (Nginx) Setup

```nginx
# /etc/nginx/sites-available/price-intelligence

upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:5173;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL certificates (Let's Encrypt recommended)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Compression
    gzip on;
    gzip_types text/plain text/css text/javascript application/json;
    gzip_min_length 1000;
    
    # API proxy
    location /api/ {
        proxy_pass http://backend/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Frontend
    location / {
        proxy_pass http://frontend/;
        proxy_set_header Host $host;
        proxy_buffering off;
    }
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

**Checklist:**
- [ ] Nginx installed and running
- [ ] SSL certificates obtained (Let's Encrypt)
- [ ] Virtual host configured
- [ ] Proxy rules correct
- [ ] GZIP compression enabled
- [ ] Static caching enabled

### 11. Monitoring & Observability

```bash
# 1. Setup application performance monitoring (APM)
# Option A: Datadog
# Option B: New Relic
# Option C: Prometheus + Grafana (self-hosted)

# 2. Configure logging aggregation
# Option A: ELK Stack
# Option B: Splunk
# Option C: CloudWatch (AWS)

# 3. Enable database monitoring
# PostgreSQL extensions:
- pg_stat_statements
- pg_stat_monitor
- pgBadger (for query analysis)

# 4. Setup alerting
# - API response time > 1s
# - Database connections > 80% of max
# - Redis memory > 80% of limit
# - Celery task failure rate > 5%
# - CPU > 80%
# - Disk > 80%
```

**Checklist:**
- [ ] APM service configured
- [ ] Logs aggregation setup
- [ ] Database stats enabled
- [ ] Prometheus metrics exposed
- [ ] Alert rules created
- [ ] Dashboards created

---

## Post-Deployment Phase

### 12. Verification & Testing

```bash
# 1. Health check
./health_check.bat

# 2. Run benchmarks
python benchmark.py all

# 3. Load testing
# Using Apache Bench
ab -n 1000 -c 100 https://api.yourdomain.com/api/metrics

# 4. Synthetic monitoring
# Periodically test critical flows:
# - User signup
# - Product comparison
# - Price alert creation
# - Wishlist operations
```

**Tests to Pass:**
- [ ] Health check: all green
- [ ] Benchmarks: Redis <5ms, API <50ms (async)
- [ ] Load test: 0% error rate under 100 concurrent users
- [ ] All API endpoints responding
- [ ] Database queries < 100ms
- [ ] Cache hit rate > 70%

### 13. Performance Validation

```bash
# 1. Check page load time
# Use WebPageTest: https://www.webpagetest.org/
# Expected: < 3 seconds fully loaded

# 2. Verify caching
curl -i https://api.yourdomain.com/api/metrics | grep -i cache-control

# 3. Check compression
curl -i https://api.yourdomain.com/api/metrics | grep -i content-encoding
# Should show: gzip

# 4. Monitor real user metrics (RUM)
# Check frontend performance monitoring dashboard
```

**Performance Targets:**
- [ ] Page load time: < 3 seconds
- [ ] Time to First Byte (TTFB): < 500ms
- [ ] Largest Contentful Paint (LCP): < 2.5s
- [ ] First Input Delay (FID): < 100ms
- [ ] Cumulative Layout Shift (CLS): < 0.1
- [ ] Cache hit rate: > 70%

### 14. Documentation & Runbooks

- [ ] Operations runbook created
- [ ] Disaster recovery procedure documented
- [ ] On-call escalation procedures defined
- [ ] Performance tuning guide created
- [ ] API documentation updated
- [ ] Architecture diagram updated
- [ ] Team trained on new systems

### 15. Backup & Disaster Recovery

```bash
# 1. Database backups
# Daily backup script
0 2 * * * PGPASSWORD=<pwd> pg_dump -h <host> -U postgres price_intelligence | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz

# 2. Redis snapshots
# Configuration
appendonly yes
appendfsync everysec

# 3. Verify backup restoration
# Test restoring from backup weekly
PGPASSWORD=<pwd> psql -h localhost -U postgres -d test_restore < backup.sql
```

**Checklist:**
- [ ] Daily database backups configured
- [ ] Backups tested monthly
- [ ] Backup retention policy set (30+ days)
- [ ] Off-site backup storage configured
- [ ] Recovery time objective (RTO): < 1 hour
- [ ] Recovery point objective (RPO): < 24 hours

---

## Rollback Plan

If issues occur, rollback in this order:

1. **Stop new traffic** - Update DNS/load balancer
2. **Revert code** - Switch to previous Docker image version
3. **Revert database** - Restore from backup if schema changed
4. **Verify services** - Health checks pass
5. **Notify team** - Update status page
6. **Post-mortem** - Document what went wrong

```bash
# Rollback script
docker-compose down
git checkout previous-version
docker pull price-intel-backend:v1.2.3
docker-compose up -d
./health_check.bat
```

---

## Maintenance & Optimization

### Monthly Tasks
- [ ] Review performance metrics
- [ ] Check database index effectiveness
- [ ] Update dependencies
- [ ] Review and optimize slow queries
- [ ] Check disk usage

### Quarterly Tasks
- [ ] Update PostgreSQL and Redis to latest patch
- [ ] Re-analyze database statistics
- [ ] Review security configurations
- [ ] Capacity planning (do we need more resources?)
- [ ] Update SSL certificates (if approaching expiry)

### Annual Tasks
- [ ] Major version upgrades
- [ ] Architecture review
- [ ] Disaster recovery drill
- [ ] Security audit
- [ ] Cost optimization review

---

## Success Criteria

Production deployment is successful when:

```
Performance Metrics:
✓ API response time: < 200ms (p95)
✓ Page load time: < 3 seconds
✓ Cache hit rate: > 70%
✓ Error rate: < 0.1%
✓ Database connections: < 50% of max

Reliability:
✓ Uptime: > 99.9%
✓ MTTF (Mean Time To Failure): > 30 days
✓ MTTR (Mean Time To Repair): < 15 minutes
✓ No data loss incidents

Resource Efficiency:
✓ CPU utilization: 40-60%
✓ Memory utilization: 50-70%
✓ Disk utilization: < 70%
✓ Network: < 50% capacity
```

---

## Post-Deployment Monitoring

Monitor these metrics daily:

1. **API Performance**
   - Response time (p50, p95, p99)
   - Error rate
   - Requests per second
   - Slow endpoint identification

2. **Database Performance**
   - Connection count
   - Query execution time
   - Cache hit rate
   - Slow query log

3. **Celery Tasks**
   - Task success rate
   - Task execution time
   - Failed task rate
   - Queue length

4. **Infrastructure**
   - CPU utilization
   - Memory utilization
   - Disk space
   - Network I/O

5. **User Experience**
   - Page load times (RUM)
   - Error tracking (client-side)
   - User flow completion
   - Conversion rates

---

## Sign-Off

- [ ] Project Manager: _________________ Date: _______
- [ ] Tech Lead: _________________ Date: _______
- [ ] DevOps/SRE: _________________ Date: _______
- [ ] QA Lead: _________________ Date: _______
- [ ] Security Team: _________________ Date: _______

