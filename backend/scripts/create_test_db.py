import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg.connect(
    dbname=os.environ.get('DB_NAME', 'mockii_db'),
    user=os.environ.get('DB_USER', 'mockii_app_login'),
    password=os.environ.get('DB_PASSWORD', ''),
    host=os.environ.get('DB_HOST', 'localhost'),
    port=os.environ.get('DB_PORT', '5432'),
    options='-c role=mockii_app'
)
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute("SELECT current_user")
    print('Current user:', cur.fetchone())
    cur.execute("SELECT rolname, rolcreatedb FROM pg_roles WHERE rolname IN ('mockii_app_login', 'mockii_app')")
    print('Roles:', cur.fetchall())
    # Try to create test db
    try:
        cur.execute("CREATE DATABASE test_mockii_db OWNER mockii_app_login")
        print("Test DB created successfully")
    except Exception as e:
        print(f"Cannot create DB: {e}")
conn.close()
