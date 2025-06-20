#!/usr/bin/env python3
"""Database migration script for analysis schema.

This script creates the necessary tables for the product analysis system.
Run this script to set up the database schema for the new multi-agent analysis system.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the path
app_dir = Path(__file__).parent.parent
sys.path.append(str(app_dir))

from sqlmodel import SQLModel, create_engine
from app.core.config import settings
from app.core.logging import logger
from app.models.analysis import AnalysisTask, Product, Competitor, AnalysisReport, AgentExecution


def create_analysis_tables():
    """Create analysis-related tables in the database."""
    logger.info("Starting database migration for analysis schema")

    try:
        # Create engine
        engine = create_engine(settings.POSTGRES_URL, pool_pre_ping=True, echo=True if settings.DEBUG else False)

        logger.info(
            "Created database engine",
            url=settings.POSTGRES_URL.split("@")[1] if "@" in settings.POSTGRES_URL else "***",
        )

        # Create all tables
        SQLModel.metadata.create_all(engine)

        logger.info("Successfully created analysis tables")

        # Verify tables were created
        with engine.connect() as conn:
            # Check if our main tables exist
            tables_to_check = ["analysis_tasks", "products", "competitors", "analysis_reports", "agent_executions"]

            from sqlalchemy import text

            for table_name in tables_to_check:
                result = conn.execute(text(f"SELECT to_regclass('public.{table_name}')"))
                table_exists = result.fetchone()[0] is not None

                if table_exists:
                    logger.info(f"✅ Table '{table_name}' created successfully")
                else:
                    logger.error(f"❌ Table '{table_name}' was not created")

        logger.info("Database migration completed successfully")

    except Exception as e:
        logger.error("Database migration failed", error=str(e))
        raise


def drop_analysis_tables():
    """Drop analysis-related tables (use with caution!)."""
    logger.warning("⚠️  Starting to drop analysis tables - THIS WILL DELETE ALL DATA!")

    try:
        engine = create_engine(settings.POSTGRES_URL, pool_pre_ping=True, echo=True if settings.DEBUG else False)

        # Drop tables in reverse dependency order
        drop_statements = [
            "DROP TABLE IF EXISTS agent_executions CASCADE;",
            "DROP TABLE IF EXISTS analysis_reports CASCADE;",
            "DROP TABLE IF EXISTS competitors CASCADE;",
            "DROP TABLE IF EXISTS products CASCADE;",
            "DROP TABLE IF EXISTS analysis_tasks CASCADE;",
        ]

        with engine.connect() as conn:
            from sqlalchemy import text

            for statement in drop_statements:
                logger.info(f"Executing: {statement}")
                conn.execute(text(statement))
                conn.commit()

        logger.info("Successfully dropped all analysis tables")

    except Exception as e:
        logger.error("Failed to drop analysis tables", error=str(e))
        raise


def check_migration_status():
    """Check the current status of the migration."""
    logger.info("Checking migration status")

    try:
        engine = create_engine(settings.POSTGRES_URL, pool_pre_ping=True)

        tables_info = []
        tables_to_check = ["analysis_tasks", "products", "competitors", "analysis_reports", "agent_executions"]

        with engine.connect() as conn:
            from sqlalchemy import text

            for table_name in tables_to_check:
                # Check if table exists
                result = conn.execute(text(f"SELECT to_regclass('public.{table_name}')"))
                table_exists = result.fetchone()[0] is not None

                if table_exists:
                    # Get row count
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = count_result.fetchone()[0]
                    tables_info.append(f"✅ {table_name}: {row_count} rows")
                else:
                    tables_info.append(f"❌ {table_name}: NOT FOUND")

        logger.info("Migration status check completed")
        print("\n📊 Analysis Schema Status:")
        print("=" * 40)
        for info in tables_info:
            print(info)
        print("=" * 40)

    except Exception as e:
        logger.error("Migration status check failed", error=str(e))
        raise


def main():
    """Main migration function with command line interface."""
    if len(sys.argv) < 2:
        print("🗃️  Analysis Schema Migration Tool")
        print("=" * 40)
        print("Usage:")
        print("  python migrate_analysis_schema.py create   # Create tables")
        print("  python migrate_analysis_schema.py drop     # Drop tables (⚠️  DANGER)")
        print("  python migrate_analysis_schema.py status   # Check status")
        print("  python migrate_analysis_schema.py reset    # Drop and recreate")
        return

    command = sys.argv[1].lower()

    if command == "create":
        print("🏗️  Creating analysis tables...")
        create_analysis_tables()
        check_migration_status()

    elif command == "drop":
        confirm = input("⚠️  Are you sure you want to DROP ALL analysis tables? Type 'DELETE' to confirm: ")
        if confirm == "DELETE":
            drop_analysis_tables()
            print("🗑️  All analysis tables have been dropped.")
        else:
            print("❌ Operation cancelled.")

    elif command == "status":
        check_migration_status()

    elif command == "reset":
        confirm = input("⚠️  Are you sure you want to RESET ALL analysis tables? Type 'RESET' to confirm: ")
        if confirm == "RESET":
            print("🗑️  Dropping existing tables...")
            drop_analysis_tables()
            print("🏗️  Creating new tables...")
            create_analysis_tables()
            check_migration_status()
            print("✅ Database reset completed!")
        else:
            print("❌ Operation cancelled.")

    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: create, drop, status, reset")


if __name__ == "__main__":
    main()
