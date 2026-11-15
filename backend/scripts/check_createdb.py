import django
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT rolcreatedb FROM pg_roles WHERE rolname = %s", ['mockii_app_login'])
    row = cursor.fetchone()
    if row:
        print('CREATEDB:', row[0])
    else:
        print('Role not found')
