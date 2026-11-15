"""
Grant all necessary privileges using the app's own DB user.
Run: venv\Scripts\python.exe scripts\grant_app_user.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.db import connection

statements = [
    # Grant mockii_app_login full rights on the public schema
    "GRANT ALL PRIVILEGES ON SCHEMA public TO mockii_app_login",
    # Grant on all existing tables
    "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mockii_app_login",
    "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mockii_app_login",
    "GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO mockii_app_login",
]

# mockii_app_login IS the owner of accounts_user tables (it created them via migrate)
# The FK reference issue is usually about missing REFERENCES privilege
# Let's check current privileges
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name, privilege_type
        FROM information_schema.role_table_grants
        WHERE grantee = 'mockii_app_login'
        AND table_name LIKE 'accounts%'
        ORDER BY table_name, privilege_type
        LIMIT 20
    """)
    rows = cursor.fetchall()
    print("Current privileges on accounts tables:")
    for row in rows:
        print(f"  {row[0]}: {row[1]}")

    # Check table ownership
    cursor.execute("""
        SELECT tablename, tableowner
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename LIKE 'accounts%'
    """)
    rows = cursor.fetchall()
    print("\nTable ownership:")
    for row in rows:
        print(f"  {row[0]}: owner={row[1]}")

    # The issue: migration tries to add FK on accounts_user.
    # Since mockii_app_login may not be the owner, we need REFERENCES.
    cursor.execute("""
        SELECT tablename, tableowner
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)
    rows = cursor.fetchall()
    print("\nAll table ownership:")
    for row in rows:
        print(f"  {row[0]}: owner={row[1]}")
