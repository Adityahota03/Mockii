"""
config/settings_test.py
=========================
Thin test-only settings that inherit everything from settings.py but
removes the "-c role=mockii_app" session-role switch that prevents
pytest-django from creating / migrating the test database.

Usage (already set in pytest.ini):
    DJANGO_SETTINGS_MODULE = config.settings_test
"""
from config.settings import *   # noqa: F401, F403

# Remove the role-switch option so pytest-django can CREATE DATABASE
# as mockii_app_login (which has CREATEDB).  All other DB parameters
# (host, port, user, password) are inherited from settings.py.
DATABASES["default"]["OPTIONS"] = {}   # noqa: F405
