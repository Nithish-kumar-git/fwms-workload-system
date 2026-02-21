# Post-Launch Monitoring

## Daily Checks

### Health Endpoint
```bash
# Quick health check (should return "ok")
curl -s https://YOUR_DOMAIN/health | python3 -m json.tool

# Detailed metrics
curl -s https://YOUR_DOMAIN/health/metrics | python3 -m json.tool
```

### Docker Service Status
```bash
cd /opt/faculty-selection
docker compose -f docker-compose.prod.yml ps
```
All services should show `running (healthy)`.

### Application Logs
```bash
# Last 100 lines
docker logs faculty_app --tail 100

# Follow live
docker logs faculty_app -f

# Filter errors only
docker logs faculty_app 2>&1 | grep -i "error\|exception\|critical"
```

---

## Key Metrics to Watch

| Metric | Where | Alert Threshold |
|--------|-------|-----------------|
| Health status | `/health` | Any non-OK response |
| Active windows | `/health/metrics` → `windows` | 0 during selection period |
| DB connections | PostgreSQL logs | > 25 concurrent |
| Redis memory | `docker exec faculty_redis redis-cli info memory` | > 100 MB |
| Disk usage | `df -h` on VPS | > 80% |
| SSL expiry | `certbot certificates` | < 14 days |

---

## Database Monitoring

```bash
# Active connections
docker exec faculty_db psql -U faculty_user -d faculty_selection \
  -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Lock waits (deadlock indicator)
docker exec faculty_db psql -U faculty_user -d faculty_selection \
  -c "SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock';"

# Table sizes
docker exec faculty_db psql -U faculty_user -d faculty_selection \
  -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC;"
```

---

## Redis Monitoring

```bash
# Basic info
docker exec faculty_redis redis-cli info

# Active sessions count
docker exec faculty_redis redis-cli dbsize

# Memory usage
docker exec faculty_redis redis-cli info memory | grep used_memory_human
```

---

## Common Issues

### 1. App returns 502 Bad Gateway
```bash
# Check if app is running
docker ps | grep faculty_app
# Check app logs
docker logs faculty_app --tail 50
# Restart app
docker compose -f docker-compose.prod.yml restart app
```

### 2. OAuth Login Fails
```bash
# Check callback URL matches Google Console
docker logs faculty_app 2>&1 | grep -i "oauth\|token"
# Verify redirect URI
echo $GOOGLE_REDIRECT_URI
```

### 3. Sessions Lost After Restart
Ensure `SESSION_BACKEND=redis` (not `memory`). Redis data persists via Docker volume.

### 4. Rate Limit False Positives
```bash
# Check current rate limit keys
docker exec faculty_redis redis-cli keys "staff_id:*"
# Clear rate limits (emergency only)
docker exec faculty_redis redis-cli flushdb
```

### 5. SSL Certificate Expired
```bash
# Manual renewal
docker compose -f docker-compose.prod.yml run --rm certbot renew
# Reload Nginx
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

---

## Backup Schedule

```bash
# Daily database backup (add to crontab)
# crontab -e
0 2 * * * docker exec faculty_db pg_dump -U faculty_user faculty_selection | gzip > /opt/backups/faculty_$(date +\%Y\%m\%d).sql.gz

# Keep last 30 days
0 3 * * * find /opt/backups -name "faculty_*.sql.gz" -mtime +30 -delete
```

---

## Escalation

| Severity | Condition | Action |
|----------|-----------|--------|
| P1 - Critical | Health endpoint down | Restart all services, check DB/Redis |
| P2 - High | OAuth failing for all users | Check Google Cloud Console status, verify credentials |
| P3 - Medium | High error rate in logs | Review logs, check for deadlocks |
| P4 - Low | Rate limit complaints | Adjust `RATE_LIMIT_SELECT_MAX_REQUESTS` |
