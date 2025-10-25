"""
Migration runner for FinSight database
Executes SQL migration files against Supabase database
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.utils import logger
from database.supabase_client import get_supabase_client


def run_migration(migration_file: str):
    """
    Run a specific migration file.

    Args:
        migration_file: Path to the SQL migration file
    """
    logger.info(f"Starting migration: {migration_file}")

    # Read migration SQL
    migration_path = Path(__file__).parent / "migrations" / migration_file

    if not migration_path.exists():
        logger.error(f"Migration file not found: {migration_path}")
        return False

    with open(migration_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Get Supabase client
    try:
        supabase = get_supabase_client()
        logger.info("Connected to Supabase")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return False

    # Execute migration using PostgreSQL REST API
    # Note: Supabase Python client doesn't directly support raw SQL execution
    # You'll need to run this through the Supabase SQL Editor or use psycopg2

    logger.warning("=" * 80)
    logger.warning("MIGRATION EXECUTION INSTRUCTIONS")
    logger.warning("=" * 80)
    logger.warning("")
    logger.warning("The Supabase Python client doesn't support direct SQL execution.")
    logger.warning("Please execute this migration using one of these methods:")
    logger.warning("")
    logger.warning("METHOD 1: Supabase Dashboard (Recommended)")
    logger.warning("-" * 80)
    logger.warning("1. Go to your Supabase project dashboard")
    logger.warning("2. Navigate to 'SQL Editor' in the left sidebar")
    logger.warning("3. Click 'New query'")
    logger.warning(f"4. Copy and paste the contents of: {migration_path}")
    logger.warning("5. Click 'Run' to execute the migration")
    logger.warning("")
    logger.warning("METHOD 2: Using psycopg2 (Advanced)")
    logger.warning("-" * 80)
    logger.warning("1. Install psycopg2: pip install psycopg2-binary")
    logger.warning("2. Get your database connection string from Supabase dashboard")
    logger.warning("3. Use psycopg2 to execute the SQL file directly")
    logger.warning("")
    logger.warning("=" * 80)
    logger.warning(f"Migration file location: {migration_path.absolute()}")
    logger.warning("=" * 80)

    # Display the SQL for easy copy-paste
    print("\n\n" + "=" * 80)
    print("MIGRATION SQL (Copy this to Supabase SQL Editor)")
    print("=" * 80)
    print(sql)
    print("=" * 80)

    return True


def run_all_migrations():
    """Run all pending migrations in order."""
    migrations_dir = Path(__file__).parent / "migrations"

    if not migrations_dir.exists():
        logger.error(f"Migrations directory not found: {migrations_dir}")
        return

    # Get all .sql files sorted by name
    migration_files = sorted([f.name for f in migrations_dir.glob("*.sql")])

    if not migration_files:
        logger.info("No migration files found")
        return

    logger.info(f"Found {len(migration_files)} migration(s)")

    for migration_file in migration_files:
        success = run_migration(migration_file)
        if not success:
            logger.error(f"Migration failed: {migration_file}")
            break


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "--migration",
        type=str,
        help="Specific migration file to run (e.g., 001_create_memory_tables.sql)",
    )

    args = parser.parse_args()

    if args.migration:
        run_migration(args.migration)
    else:
        run_all_migrations()
