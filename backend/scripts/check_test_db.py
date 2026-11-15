"""
Check if test_mockii_db already exists by trying to connect to it.
"""
import os
import sys

# Use mockii_app_login credentials from .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

try:
    import psycopg
    conn = psycopg.connect(
        dbname='test_mockii_db',
        user=os.environ.get('DB_USER', 'mockii_app_login'),
        password=os.environ.get('DB_PASSWORD', ''),
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432'),
    )
    conn.close()
    print("SUCCESS: test_mockii_db exists and is accessible!")
except Exception as e:
    print(f"FAILED: {e}")
    print("\nYou need to create test_mockii_db manually.")
    print("Open pgAdmin -> Query Tool (connected as postgres) and run:")
    print("  d:\\Mockii\\backend\\scripts\\create_test_db_manual.sql")
    print("\nOR grant CREATEDB privilege:")
    print("  ALTER ROLE mockii_app_login CREATEDB;")
