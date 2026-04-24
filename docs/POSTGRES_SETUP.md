# PostgreSQL Setup for SmartRU

This document provides instructions for setting up PostgreSQL for the SmartRU project.

## Prerequisites

1. Docker and Docker Compose installed
2. Python 3.11 or higher
3. PostgreSQL client tools (optional, for manual database access)

## Quick Start with Docker

### 1. Automated Setup

```bash
# Run the setup script
python setup.py

# Or manually copy environment template
cp .env.example .env

# Edit .env file with your settings (optional)
# nano .env
```

### 2. Start PostgreSQL and Application

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

### 3. Access PostgreSQL

```bash
# Access PostgreSQL container
docker exec -it smartru-postgres psql -U smartru_user -d smartru_db

# Or connect from host (if port 5432 is exposed)
psql -h localhost -p 5432 -U smartru_user -d smartru_db
```

## Manual PostgreSQL Setup (without Docker)

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download and install from [postgresql.org](https://www.postgresql.org/download/windows/)

### 2. Create Database and User

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE smartru_db;
CREATE USER smartru_user WITH PASSWORD 'smartru_password';
GRANT ALL PRIVILEGES ON DATABASE smartru_db TO smartru_user;

# Exit
\q
```

### 3. Initialize Schema

```bash
# Apply schema
psql -h localhost -U smartru_user -d smartru_db -f database/schema.sql
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL connection details
```

### 6. Run Application

```bash
python main.py
```

## Data Migration from SQLite

If you have existing data in SQLite that needs to be preserved:

```bash
# Make sure PostgreSQL is running
python database/migrate_sqlite_to_postgres.py
```

The script will:
1. Create a backup of your SQLite database
2. Migrate all data to PostgreSQL
3. Update PostgreSQL sequences

## Connection Pool Configuration

For high volume (>1000 users), adjust these settings in `.env`:

```env
# Connection Pool Settings
DB_POOL_MIN_CONNECTIONS=5
DB_POOL_MAX_CONNECTIONS=50
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DB` | Database name | `smartru_db` |
| `POSTGRES_USER` | Database user | `smartru_user` |
| `POSTGRES_PASSWORD` | Database password | `smartru_password` |
| `DB_POOL_MIN_CONNECTIONS` | Minimum connections in pool | `1` |
| `DB_POOL_MAX_CONNECTIONS` | Maximum connections in pool | `20` |
| `DB_POOL_TIMEOUT` | Connection timeout (seconds) | `30` |
| `DB_POOL_RECYCLE` | Connection recycle time (seconds) | `3600` |
| `APP_ENV` | Application environment | `development` |
| `APP_DEBUG` | Debug mode | `True` |

## Testing the Connection

### Simple Test (No Curses Required)

```bash
# Test PostgreSQL connection without curses
python test_postgres_simple.py
```

### Full Test (Requires Curses Dependencies)

```bash
# Test with full functionality
python test_postgres.py
```

### Manual Test Script

Create a test script `test_manual.py`:

```python
from database import DataBase

db = DataBase()
try:
    db.initialize_database()
    print("✓ PostgreSQL connection successful")
    
    # Test a simple query
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()
    print(f"✓ PostgreSQL version: {version[0]}")
    
    db.connection_pool.putconn(conn)
    db.close()
    print("✓ Connection pool closed successfully")
    
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

## Troubleshooting

### 1. Python Dependencies Issues
```bash
# Run the setup script for automated troubleshooting
python setup.py

# Or manually install dependencies
pip install -r requirements.txt
```

### 2. Curses Module Not Found (Windows/Linux/macOS)
```bash
# Linux (Debian/Ubuntu)
sudo apt-get install libncurses5-dev libncursesw5-dev

# macOS
brew install ncurses

# Windows - Consider using WSL or check Windows curses alternatives
```

### 3. Connection Refused
```bash
# Check if PostgreSQL is running
docker ps  # For Docker
# or
sudo systemctl status postgresql  # For systemd
```

### 4. Authentication Failed
- Verify username/password in `.env`
- Check PostgreSQL user permissions

### 5. Database Doesn't Exist
```bash
# Create database manually
createdb -U postgres smartru_db
```

### 6. Port Already in Use
```bash
# Change port in .env or docker-compose.yml
POSTGRES_PORT=5433
```

### 7. Docker Volume Issues
```bash
# Remove and recreate volumes
docker-compose down -v
docker-compose up -d
```

### 8. ModuleNotFoundError for dotenv
```bash
# Install missing package
pip install python-dotenv
```

## Performance Tips

1. **Indexes**: The schema includes indexes for common queries (cpf, email, dates)
2. **Connection Pooling**: Configure pool size based on expected concurrent users
3. **Monitoring**: Use `pg_stat_activity` to monitor active connections
4. **Backup**: Regular backups with `pg_dump`

## Backup and Restore

```bash
# Backup
docker exec smartru-postgres pg_dump -U smartru_user smartru_db > backup.sql

# Restore
docker exec -i smartru-postgres psql -U smartru_user smartru_db < backup.sql
```

## Security Considerations

1. Use strong passwords in production
2. Restrict network access to PostgreSQL
3. Use SSL/TLS for production connections
4. Regular security updates
5. Monitor logs for suspicious activity