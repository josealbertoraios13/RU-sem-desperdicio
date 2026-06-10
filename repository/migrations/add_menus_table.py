"""
Migration: Add menus table for weekly menu uploads.
Usage:
    python -m smartru.repository.migrations.add_menus_table
This script applies the menus table schema to an existing database.
The same schema is also included in src/smartru/repository/schema.sql for fresh installs.
"""
import os

from dotenv import load_dotenv
from psycopg2 import pool

load_dotenv()

SQL = """
CREATE TABLE IF NOT EXISTS menus (
    id BIGSERIAL PRIMARY KEY,
    image_url TEXT NOT NULL,
    filename TEXT NOT NULL,
    lunch_image_url TEXT,
    lunch_filename TEXT,
    dinner_image_url TEXT,
    dinner_filename TEXT,
    uploaded_by BIGINT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
);
ALTER TABLE menus ADD COLUMN IF NOT EXISTS lunch_image_url TEXT;
ALTER TABLE menus ADD COLUMN IF NOT EXISTS lunch_filename TEXT;
ALTER TABLE menus ADD COLUMN IF NOT EXISTS dinner_image_url TEXT;
ALTER TABLE menus ADD COLUMN IF NOT EXISTS dinner_filename TEXT;
UPDATE menus
SET lunch_image_url = COALESCE(lunch_image_url, image_url),
    lunch_filename = COALESCE(lunch_filename, filename)
WHERE lunch_image_url IS NULL OR lunch_filename IS NULL;
CREATE INDEX IF NOT EXISTS idx_menus_uploaded_at ON menus(uploaded_at DESC);
"""


def run_migration():
    conn_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=1,
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "smart_ru"),
        user=os.getenv("POSTGRES_USER", "smart_ru_user"),
        password=os.getenv("POSTGRES_PASSWORD"),
        connect_timeout=30,
    )
    conn = conn_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(SQL)
        conn.commit()
        print("Migration applied: menus table created successfully.")  # noqa: T201
    finally:
        conn_pool.putconn(conn)


if __name__ == "__main__":
    run_migration()
