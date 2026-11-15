"""
Run this script to grant all necessary privileges to mockii_app_login.
This connects as mockii_app_login (which has CREATEDB from earlier setup).
We'll use a direct SQL grant approach via Django's ORM connection instead.
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.db import connection

sql = """
ALTER TABLE superadmin_auditlog OWNER TO mockii_app_login;
ALTER TABLE superadmin_systemsetting OWNER TO mockii_app_login;
ALTER TABLE superadmin_permission OWNER TO mockii_app_login;
ALTER TABLE superadmin_role OWNER TO mockii_app_login;
ALTER TABLE superadmin_role_permissions OWNER TO mockii_app_login;
ALTER TABLE superadmin_adminpermission OWNER TO mockii_app_login;
ALTER TABLE superadmin_securityevent OWNER TO mockii_app_login;
ALTER TABLE superadmin_blockedip OWNER TO mockii_app_login;
"""

print("This approach requires superuser. Trying via manage.py migrate with superuser DB config instead.")
print("Please run the following SQL as postgres superuser:")
print()
print("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mockii_app_login;")
print("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mockii_app_login;")
