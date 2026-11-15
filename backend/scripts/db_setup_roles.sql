-- =============================================================
-- db_setup_roles.sql
-- PostgreSQL least-privilege role setup for Mockii
--
-- Run ONCE as a superuser (postgres) against the mockii_db database:
--   psql -U postgres -d mockii_db -f scripts/db_setup_roles.sql
--
-- Security principle:
--   The Django application (mockii_app) gets only the permissions
--   it needs — no CREATEDB, no SUPERUSER, no DDL on existing tables.
--   The DBA role retains full administrative access.
-- =============================================================

-- ---------------------------------------------------------------
-- 1. Create the application role (idempotent)
-- ---------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mockii_app') THEN
        CREATE ROLE mockii_app
            NOLOGIN          -- login is granted via the mockii_app_login user
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT;
        RAISE NOTICE 'Role mockii_app created.';
    ELSE
        RAISE NOTICE 'Role mockii_app already exists — skipping creation.';
    END IF;
END
$$;

-- ---------------------------------------------------------------
-- 2. Create the login user (idempotent)
--    Set a strong password: replace CHANGEME with a real secret
--    and store it in .env as DB_PASSWORD (never commit this file).
-- ---------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mockii_app_login') THEN
        CREATE ROLE mockii_app_login
            LOGIN
            PASSWORD 'CHANGEME_USE_ENV_VAR'
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            CONNECTION LIMIT 30;
        RAISE NOTICE 'Login role mockii_app_login created.';
    ELSE
        RAISE NOTICE 'Login role mockii_app_login already exists — skipping creation.';
    END IF;
END
$$;

-- Assign the application role to the login user
GRANT mockii_app TO mockii_app_login;

-- ---------------------------------------------------------------
-- 3. Schema-level privileges
--    mockii_app can use the public schema (create tables during
--    migrations, then only DML afterwards).
-- ---------------------------------------------------------------
GRANT USAGE ON SCHEMA public TO mockii_app;

-- Allow Django migrations to create/alter tables
-- NOTE: After initial migration you can REVOKE CREATEDB from
--       the login role if you want to lock down further.
GRANT CREATE ON SCHEMA public TO mockii_app;

-- ---------------------------------------------------------------
-- 4. Default privileges for future tables
--    Any table created by the DBA (postgres) or migrations will
--    automatically be accessible by mockii_app.
-- ---------------------------------------------------------------
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mockii_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO mockii_app;

-- ---------------------------------------------------------------
-- 5. Grant DML on all EXISTING tables and sequences
--    (needed after first run if tables already exist)
-- ---------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE, DELETE
    ON ALL TABLES IN SCHEMA public
    TO mockii_app;

GRANT USAGE, SELECT
    ON ALL SEQUENCES IN SCHEMA public
    TO mockii_app;

-- ---------------------------------------------------------------
-- 6. Explicitly revoke dangerous privileges (defence-in-depth)
-- ---------------------------------------------------------------
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- ---------------------------------------------------------------
-- 7. Verification query — run to confirm role setup
-- ---------------------------------------------------------------
SELECT
    rolname,
    rolsuper,
    rolinherit,
    rolcreatedb,
    rolcreaterole,
    rolcanlogin,
    rolconnlimit
FROM pg_roles
WHERE rolname IN ('mockii_app', 'mockii_app_login')
ORDER BY rolname;
