#!/usr/bin/env python
"""
scripts/pre_migrate.py
======================
Pre-migration safety check for Mockii.

Run this BEFORE every `manage.py migrate` call in production:

    python scripts/pre_migrate.py

The script fails with exit code 1 if any safety check fails, so it
can be placed at the start of a CI/CD deploy pipeline step.

Checks performed
----------------
1. DEBUG must be False in production (skipped in dev mode).
2. Database is reachable with the configured credentials.
3. All pending migrations are listed so the operator can review them.
4. A point-in-time backup reminder is printed.
5. Confirmation prompt (skippable with --yes for automation).

Usage
-----
    # Interactive (production deploy)
    python scripts/pre_migrate.py

    # Non-interactive (CI/CD, already reviewed)
    python scripts/pre_migrate.py --yes

    # Development (skips DEBUG and production guards)
    python scripts/pre_migrate.py --dev
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap Django so we can use its ORM and migration framework
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Load .env before Django setup so env vars are populated
try:
    from dotenv import load_dotenv
    load_dotenv(BACKEND_DIR / ".env")
except ImportError:
    pass  # python-dotenv not installed; rely on shell environment

import django  # noqa: E402
django.setup()

from django.conf import settings  # noqa: E402
from django.db import connections, OperationalError  # noqa: E402
from django.db.migrations.executor import MigrationExecutor  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def section(title: str) -> None:
    width = 60
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def ok(msg: str) -> None:
    print(f"  [OK]  {msg}")


def warn(msg: str) -> None:
    print(f"  [!!]  {msg}", file=sys.stderr)


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def check_debug(dev_mode: bool) -> None:
    section("1. DEBUG safety check")
    if settings.DEBUG and not dev_mode:
        fail(
            "DEBUG=True detected in a non-dev run. "
            "Set DEBUG=False in your production .env and re-run."
        )
    elif settings.DEBUG:
        warn("DEBUG=True — running in dev mode, check skipped.")
    else:
        ok("DEBUG=False — production mode confirmed.")


def check_db_connection() -> None:
    section("2. Database connectivity")
    conn = connections["default"]
    try:
        conn.ensure_connection()
        db_cfg = settings.DATABASES["default"]
        ok(
            f"Connected to PostgreSQL  "
            f"host={db_cfg.get('HOST')}  "
            f"db={db_cfg.get('NAME')}  "
            f"user={db_cfg.get('USER')}"
        )
    except OperationalError as exc:
        fail(f"Cannot connect to database: {exc}")


def check_pending_migrations() -> tuple[list, list]:
    """Return (pending, applied) migration lists."""
    section("3. Pending migrations")
    connection = connections["default"]
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

    if not plan:
        ok("No pending migrations — database is up to date.")
        return [], []

    pending = []
    for migration, backwards in plan:
        direction = "BACKWARDS" if backwards else "forwards"
        label = f"{migration.app_label}.{migration.name}  [{direction}]"
        pending.append(label)
        print(f"  [-]  {label}")

    warn(
        f"{len(pending)} pending migration(s) found. "
        "Review the list above before proceeding."
    )
    return pending, plan


def backup_reminder() -> None:
    section("4. Backup reminder")
    db_cfg = settings.DATABASES["default"]
    print(
        f"""
  Before running migrations on production you SHOULD have a recent
  database backup. Example pg_dump command:

      pg_dump \\
        -h {db_cfg.get('HOST', 'localhost')} \\
        -U {db_cfg.get('USER', 'mockii_app_login')} \\
        -d {db_cfg.get('NAME', 'mockii_db')} \\
        --format=custom \\
        -f backup_$(date +%Y%m%d_%H%M%S).dump

  Store the backup securely BEFORE migrating.
"""
    )


def confirm(yes: bool) -> None:
    section("5. Confirmation")
    if yes:
        ok("--yes flag provided — skipping interactive prompt.")
        return
    try:
        answer = input("  Proceed with migrate? [yes/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        fail("Aborted by user.")
    if answer != "yes":
        fail("Migration aborted — operator did not confirm.")
    ok("Confirmed.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Mockii pre-migration safety check")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip interactive confirmation (for CI/CD pipelines)",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Relax production guards (for local development)",
    )
    args = parser.parse_args()

    print("\nMockii Pre-Migration Safety Check")
    print("=" * 60)

    check_debug(dev_mode=args.dev)
    check_db_connection()
    pending, _ = check_pending_migrations()
    backup_reminder()
    confirm(yes=args.yes)

    section("Ready")
    if pending:
        print(
            "\n  Run:  python manage.py migrate\n"
            "  Then: python manage.py check --deploy\n"
        )
    else:
        ok("Nothing to migrate.")

    sys.exit(0)


if __name__ == "__main__":
    main()
