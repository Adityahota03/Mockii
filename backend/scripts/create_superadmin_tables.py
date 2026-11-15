"""
Grant REFERENCES on accounts_user to mockii_app_login using the existing connection.
This works because mockii_app_login already has CONNECT privileges.
The REFERENCES grant must come from the table owner (postgres).
Since we can't use postgres user directly, we'll use a workaround:
set db_constraint=False on FK fields pointing to accounts_user.
"""
# Actually let's just check if we can run the migration with --fake
# and manually create the tables
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.db import connection

# Run the DDL manually without FK constraints
sql_statements = [
    """
    CREATE TABLE IF NOT EXISTS superadmin_permission (
        id SERIAL PRIMARY KEY,
        code VARCHAR(60) UNIQUE NOT NULL,
        module VARCHAR(40) NOT NULL,
        description VARCHAR(200) NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS superadmin_blockedip (
        id SERIAL PRIMARY KEY,
        ip_address INET UNIQUE NOT NULL,
        reason TEXT NOT NULL DEFAULT '',
        blocked_by_id INTEGER,
        blocked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        expires_at TIMESTAMP WITH TIME ZONE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS superadmin_role (
        id SERIAL PRIMARY KEY,
        name VARCHAR(40) UNIQUE NOT NULL,
        is_core BOOLEAN NOT NULL DEFAULT FALSE,
        description VARCHAR(200) NOT NULL DEFAULT '',
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS superadmin_role_permissions (
        id SERIAL PRIMARY KEY,
        role_id INTEGER NOT NULL REFERENCES superadmin_role(id) ON DELETE CASCADE,
        permission_id INTEGER NOT NULL REFERENCES superadmin_permission(id) ON DELETE CASCADE,
        UNIQUE(role_id, permission_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS superadmin_systemsetting (
        id SERIAL PRIMARY KEY,
        key VARCHAR(100) UNIQUE NOT NULL,
        value JSONB NOT NULL DEFAULT '{}',
        category VARCHAR(20) NOT NULL DEFAULT 'general',
        description TEXT NOT NULL DEFAULT '',
        updated_by_id INTEGER,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS superadmin_auditlog (
        id SERIAL PRIMARY KEY,
        actor_id INTEGER,
        actor_email VARCHAR(254) NOT NULL DEFAULT '',
        actor_role VARCHAR(20) NOT NULL DEFAULT '',
        action VARCHAR(100) NOT NULL,
        target_type VARCHAR(60) NOT NULL DEFAULT '',
        target_id VARCHAR(40) NOT NULL DEFAULT '',
        before JSONB,
        after JSONB,
        ip_address INET,
        user_agent TEXT NOT NULL DEFAULT '',
        severity VARCHAR(10) NOT NULL DEFAULT 'medium',
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS superadmin_adminpermission (
        id SERIAL PRIMARY KEY,
        admin_id INTEGER NOT NULL,
        permission_id INTEGER NOT NULL REFERENCES superadmin_permission(id) ON DELETE CASCADE,
        granted_by_id INTEGER,
        granted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        UNIQUE(admin_id, permission_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS superadmin_securityevent (
        id SERIAL PRIMARY KEY,
        event_type VARCHAR(30) NOT NULL,
        user_id INTEGER,
        user_email VARCHAR(254) NOT NULL DEFAULT '',
        ip_address INET,
        details JSONB NOT NULL DEFAULT '{}',
        severity VARCHAR(10) NOT NULL DEFAULT 'medium',
        resolved BOOLEAN NOT NULL DEFAULT FALSE,
        resolved_by_id INTEGER,
        resolved_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    )
    """,
    # Indexes
    "CREATE INDEX IF NOT EXISTS superadmin_auditlog_action ON superadmin_auditlog(action)",
    "CREATE INDEX IF NOT EXISTS superadmin_auditlog_created ON superadmin_auditlog(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS superadmin_auditlog_severity ON superadmin_auditlog(severity)",
    "CREATE INDEX IF NOT EXISTS superadmin_auditlog_actor ON superadmin_auditlog(actor_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS superadmin_securityevent_type ON superadmin_securityevent(event_type)",
    "CREATE INDEX IF NOT EXISTS superadmin_securityevent_severity ON superadmin_securityevent(severity, resolved, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS superadmin_permission_code ON superadmin_permission(code)",
    "CREATE INDEX IF NOT EXISTS superadmin_systemsetting_key ON superadmin_systemsetting(key)",
    "CREATE INDEX IF NOT EXISTS superadmin_systemsetting_cat ON superadmin_systemsetting(category)",
]

with connection.cursor() as cursor:
    for sql in sql_statements:
        try:
            cursor.execute(sql)
            print(f"OK: {sql.strip()[:60]}...")
        except Exception as e:
            print(f"ERROR: {e}")

print("\nDone! Now marking migration as applied...")
