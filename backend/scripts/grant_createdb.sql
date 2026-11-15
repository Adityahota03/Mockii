-- Run this in pgAdmin Query Tool connected as 'postgres' superuser
-- Step 1: Grant CREATEDB to the app login role
ALTER ROLE mockii_app_login CREATEDB;

-- Step 2: Verify (should show rolcreatedb = true)
SELECT rolname, rolcreatedb FROM pg_roles WHERE rolname = 'mockii_app_login';
