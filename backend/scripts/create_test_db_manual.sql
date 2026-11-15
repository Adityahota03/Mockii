-- ============================================================
-- scripts/create_test_db_manual.sql
-- Run ONCE as the 'postgres' superuser in pgAdmin Query Tool.
-- This creates the test database and grants full ownership to
-- mockii_app_login so pytest-django can run migrations freely.
-- ============================================================

-- Step 1: Create the test database owned by mockii_app_login
CREATE DATABASE test_mockii_db
    OWNER mockii_app_login
    ENCODING 'UTF8'
    LC_COLLATE 'English_India.1252'
    LC_CTYPE  'English_India.1252'
    TEMPLATE template0;

-- Step 2: Grant all privileges on the test DB to mockii_app_login
GRANT ALL PRIVILEGES ON DATABASE test_mockii_db TO mockii_app_login;

-- Step 3: Connect to the new test database and grant schema rights
\connect test_mockii_db

GRANT ALL ON SCHEMA public TO mockii_app_login;
ALTER SCHEMA public OWNER TO mockii_app_login;

-- Step 4: Verify
SELECT datname, pg_catalog.pg_get_userbyid(datdba) AS owner
FROM   pg_database
WHERE  datname = 'test_mockii_db';
