"""
scripts/bootstrap_test_db.py
==============================
Creates and migrates the test database without requiring CREATEDB
on the session role.  Connects as mockii_app_login directly (no role switch)
so the CREATEDB privilege we already granted is used.

Run once: venv\Scripts\python.exe scripts\bootstrap_test_db.py
"""
import os
import sys
import subprocess
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DB_USER = os.environ.get("DB_USER", "mockii_app_login")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
TEST_DB = os.environ.get("TEST_DB_NAME", "test_mockii_db")

# ── Step 1: Create the test database via psycopg (no role switch) ──────────

try:
    import psycopg
except ImportError:
    sys.exit("psycopg not installed in venv")

print(f"[1/3] Connecting as {DB_USER} (no role switch) …")
try:
    # autocommit=True required for CREATE DATABASE
    conn = psycopg.connect(
        dbname="postgres",   # connect to template DB
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        autocommit=True,
        # NO options="-c role=mockii_app" here — keep login role
    )
except Exception as e:
    sys.exit(f"Connection failed: {e}")

print(f"[2/3] Creating database '{TEST_DB}' …")
with conn.cursor() as cur:
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB,))
    if cur.fetchone():
        print(f"  ✓ '{TEST_DB}' already exists, skipping CREATE.")
    else:
        cur.execute(f'CREATE DATABASE "{TEST_DB}" OWNER {DB_USER} ENCODING \'UTF8\'')
        print(f"  ✓ Database '{TEST_DB}' created.")

conn.close()

# ── Step 2: Run Django migrations on the test database ────────────────────

print(f"[3/3] Running migrations on '{TEST_DB}' …")
backend_dir = Path(__file__).parent.parent
env = {
    **os.environ,
    "DJANGO_SETTINGS_MODULE": "config.settings",
    "PYTHONPATH": str(backend_dir),
    # Override DB_NAME so manage.py targets the test DB directly
    "DB_NAME": TEST_DB,
    # No role switch for this bootstrap run
    "PGAPPNAME": "mockii_test_bootstrap",
}

# Temporarily patch settings to not use -c role=mockii_app
# by pointing to a thin wrapper settings module
result = subprocess.run(
    [str(backend_dir / "venv" / "Scripts" / "python.exe"),
     "manage.py", "migrate", "--run-syncdb", "--no-input"],
    cwd=backend_dir,
    env=env,
    capture_output=True,
    text=True,
)
print(result.stdout[-3000:] if result.stdout else "(no stdout)")
if result.returncode != 0:
    print("STDERR:", result.stderr[-2000:])
    sys.exit(f"Migration failed (exit {result.returncode})")

print("\n✅ Test database is ready. Run: venv\\Scripts\\python.exe -m pytest tests\\phase9\\ -v")
