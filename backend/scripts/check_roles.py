"""Check CREATEDB for both roles and current_user during connection."""
import os, psycopg
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

conn = psycopg.connect(
    dbname=os.environ.get('DB_NAME', 'mockii_db'),
    user=os.environ.get('DB_USER', 'mockii_app_login'),
    password=os.environ.get('DB_PASSWORD', ''),
    host=os.environ.get('DB_HOST', 'localhost'),
    port=os.environ.get('DB_PORT', '5432'),
    options="-c role=mockii_app",   # simulate what Django does
)
with conn.cursor() as cur:
    cur.execute("SELECT current_user, session_user")
    row = cur.fetchone()
    print(f"current_user={row[0]}, session_user={row[1]}")
    cur.execute(
        "SELECT rolname, rolcreatedb FROM pg_roles WHERE rolname IN ('mockii_app','mockii_app_login')"
    )
    for r in cur.fetchall():
        print(f"  role={r[0]} createdb={r[1]}")
conn.close()
