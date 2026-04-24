# Production Deployment Guide

This guide covers production deployment, monitoring, and maintenance of the SmartRU PostgreSQL implementation.

## Production Environment Configuration

### 1. Security Hardening

**Environment Variables (.env.production):**
```env
# Database Configuration
POSTGRES_HOST=postgres.internal
POSTGRES_PORT=5432
POSTGRES_DB=smartru_production
POSTGRES_USER=smartru_prod_user
POSTGRES_PASSWORD=strong_password_here  # Use a secure password generator

# Connection Pool (adjust based on load)
DB_POOL_MIN_CONNECTIONS=10
DB_POOL_MAX_CONNECTIONS=100
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800  # 30 minutes

# Application Settings
APP_ENV=production
APP_DEBUG=False

# Security
BCRYPT_ROUNDS=14  # Higher for production
```

### 2. PostgreSQL Production Configuration

**postgresql.conf adjustments:**
```ini
# Connection settings
max_connections = 200
shared_buffers = 4GB  # 25% of available RAM
effective_cache_size = 12GB  # 75% of available RAM

# Write settings
synchronous_commit = on
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Memory settings
work_mem = 16MB
maintenance_work_mem = 512MB

# Logging
log_statement = 'none'  # Change to 'ddl' or 'mod' for debugging
log_duration = off
log_connections = on
log_disconnections = on
log_lock_waits = on
log_min_duration_statement = 1000  # Log slow queries > 1s
```

### 3. Docker Compose for Production

**docker-compose.production.yml:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: smartru-postgres-prod
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgresql.conf:/etc/postgresql/postgresql.conf:ro
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - smartru-network
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G

  app:
    build: .
    container_name: smartru-app-prod
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - APP_ENV=production
      - APP_DEBUG=False
    volumes:
      - ./logs:/app/logs
    networks:
      - smartru-network
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

volumes:
  postgres_data:

networks:
  smartru-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## Monitoring and Alerting

### 1. PostgreSQL Monitoring

**Essential metrics to monitor:**
- Connection count
- Query performance (slow queries)
- Disk usage
- Replication lag (if using replication)
- Lock contention
- Cache hit ratio

**Monitoring tools:**
- **pg_stat_statements**: Track query performance
- **pgBadger**: Log analyzer
- **Prometheus + Grafana**: Comprehensive monitoring
- **pgAdmin**: Web-based administration

### 2. Application Monitoring

**Add to database.py:**
```python
import time
from functools import wraps

def monitor_query(func):
    """Decorator to monitor query performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log slow queries
            if execution_time > 1.0:  # 1 second threshold
                logger.warning(f"Slow query detected in {func.__name__}: {execution_time:.2f}s")
            
            return result
        except Exception as e:
            logger.error(f"Query failed in {func.__name__}: {e}")
            raise
    return wrapper
```

### 3. Health Check Endpoint

**Create health_check.py:**
```python
from database import DataBase
import psycopg2

def check_database_health():
    """Check database health status"""
    try:
        db = DataBase()
        conn = db.connect()
        
        checks = {
            'connection': False,
            'tables_exist': False,
            'query_performance': False
        }
        
        # Test connection
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        checks['connection'] = cursor.fetchone()[0] == 1
        
        # Check tables
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('usuarios', 'agendamentos')
        """)
        checks['tables_exist'] = cursor.fetchone()[0] == 2
        
        # Test query performance
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        query_time = time.time() - start_time
        checks['query_performance'] = query_time < 0.1  # 100ms threshold
        
        db.connection_pool.putconn(conn)
        db.close()
        
        return {
            'healthy': all(checks.values()),
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
```

## Backup and Disaster Recovery

### 1. Automated Backups

**backup_script.sh:**
```bash
#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/smartru_backup_$DATE.sql"

# Create backup
docker exec smartru-postgres-prod pg_dump -U smartru_prod_user smartru_production > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

# Sync to remote storage (optional)
# rsync -avz $BACKUP_DIR remote-backup-server:/backups/smartru/
```

### 2. Restore Procedure

```bash
# Stop application
docker-compose -f docker-compose.production.yml stop app

# Restore database
gunzip -c backup_file.sql.gz | docker exec -i smartru-postgres-prod psql -U smartru_prod_user smartru_production

# Start application
docker-compose -f docker-compose.production.yml start app
```

### 3. Point-in-Time Recovery

Enable WAL archiving in postgresql.conf:
```ini
wal_level = replica
archive_mode = on
archive_command = 'cp %p /wal_archive/%f'
```

## Performance Optimization

### 1. Database Indexes

**Additional indexes for production:**
```sql
-- Add to schema.sql for production
CREATE INDEX IF NOT EXISTS idx_usuarios_tipo_usuario ON usuarios(tipo_usuario);
CREATE INDEX IF NOT EXISTS idx_agendamentos_tipo_refeicao ON agendamentos(tipo_refeicao);
CREATE INDEX IF NOT EXISTS idx_agendamentos_usuario_data ON agendamentos(usuario_id, data_refeicao);
```

### 2. Query Optimization

**Common optimizations:**
- Use `EXPLAIN ANALYZE` to analyze query plans
- Avoid `SELECT *` - specify columns explicitly
- Use appropriate data types
- Implement pagination for large result sets

### 3. Connection Pool Tuning

**Monitor pool usage:**
```python
# Add to database.py
def get_pool_stats(self):
    """Get connection pool statistics"""
    return {
        'min_connections': self.connection_pool.minconn,
        'max_connections': self.connection_pool.maxconn,
        'current_connections': len(self.connection_pool._used),
        'available_connections': len(self.connection_pool._pool)
    }
```

## Scaling Strategies

### 1. Vertical Scaling
- Increase PostgreSQL memory/CPU allocation
- Use faster storage (SSD/NVMe)
- Optimize PostgreSQL configuration

### 2. Horizontal Scaling
- Read replicas for read-heavy workloads
- Connection pooling with PgBouncer
- Sharding for very large datasets

### 3. Application-Level Scaling
- Implement caching (Redis/Memcached)
- Queue heavy operations (Celery/RabbitMQ)
- Use CDN for static assets

## Security Best Practices

### 1. Network Security
- Use VPN or VPC for database access
- Restrict database port (5432) to application servers only
- Implement SSL/TLS for database connections

### 2. Database Security
- Regular security updates
- Principle of least privilege for database users
- Audit logging enabled
- Regular security scans

### 3. Application Security
- Input validation and sanitization
- Prepared statements (already implemented)
- Rate limiting for authentication endpoints
- Regular dependency updates

## Maintenance Schedule

### Daily
- Check backup completion
- Monitor disk space
- Review error logs

### Weekly
- Analyze slow queries
- Update statistics: `ANALYZE`
- Clean up old logs

### Monthly
- Performance review
- Security audit
- Update PostgreSQL minor versions

### Quarterly
- Major version upgrade planning
- Disaster recovery testing
- Capacity planning

## Troubleshooting Common Issues

### 1. High CPU Usage
```sql
-- Find problematic queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

### 2. Connection Issues
```sql
-- Check active connections
SELECT * FROM pg_stat_activity;

-- Kill idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND now() - state_change > interval '10 minutes';
```

### 3. Disk Space Issues
```sql
-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Support and Resources

- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Performance Tuning Guide**: https://wiki.postgresql.org/wiki/Performance_Optimization
- **Monitoring Tools**: Prometheus, Grafana, Datadog
- **Backup Solutions**: pgBackRest, Barman

## Emergency Contacts

Keep contact information for:
- Database administrator
- System administrator
- Application developers
- Management escalation