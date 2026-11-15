"""Verify settings_test connects correctly and doesn't switch roles."""
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_test'
django.setup()

from django.db import connection
with connection.cursor() as cur:
    cur.execute("SELECT current_user, session_user")
    row = cur.fetchone()
    print("current_user:", row[0])
    print("session_user:", row[1])
    cur.execute("SELECT rolcreatedb FROM pg_roles WHERE rolname = %s", [row[0]])
    r = cur.fetchone()
    print("CREATEDB for current_user:", r[0] if r else "N/A")
