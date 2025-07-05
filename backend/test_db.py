from app.core.config import settings

print(f"DATABASE_URL from settings: {settings.DATABASE_URL}")

# Test direct connection
import psycopg2

try:
    conn = psycopg2.connect(
        host="127.0.0.1",
        port="5432",
        database="globegenius_db",
        user="globegenius",
        password="globegenius2024"
    )
    print("Direct psycopg2 connection: SUCCESS")
    conn.close()
except Exception as e:
    print(f"Direct psycopg2 connection: FAILED - {e}")

# Test SQLAlchemy
from sqlalchemy import create_engine

try:
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("SQLAlchemy connection: SUCCESS")
except Exception as e:
    print(f"SQLAlchemy connection: FAILED - {e}")