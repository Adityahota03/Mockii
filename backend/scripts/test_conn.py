"""Test connection with mockii_app user"""
import os
os.environ['DB_USER'] = 'mockii_app'
os.environ['DB_PASSWORD'] = 'Mockii@2026Aditya'

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT current_user, session_user")
    print("Connected as:", cursor.fetchone())
    cursor.execute("SELECT pg_has_role(current_user, 'mockii_app_login', 'member')")
    print("Is member of mockii_app_login:", cursor.fetchone())
