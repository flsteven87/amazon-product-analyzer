#!/usr/bin/env python3
"""Command-line interface for database operations."""

import click
from sqlmodel import Session, delete, text, select

from app.core.config import settings
from app.core.logging import logger
from app.models.analysis import (
    AgentExecution,
    AnalysisReport,
    AnalysisTask,
    Competitor,
    Product,
)
from app.services.database import database_service


@click.group()
def cli():
    """Amazon Product Analyzer CLI commands."""
    pass


@cli.command()
def db_stats():
    """Show database statistics."""
    click.echo("📊 Database Statistics")
    click.echo("=" * 30)
    
    try:
        with Session(database_service.engine) as session:
            tables = [
                ("Tasks", AnalysisTask),
                ("Products", Product),
                ("Competitors", Competitor),
                ("Reports", AnalysisReport),
                ("Agent Executions", AgentExecution),
            ]
            
            stats = {}
            for name, model in tables:
                count = len(session.exec(select(model)).all())
                stats[name] = count
                click.echo(f"{name:20}: {count:>6}")
            
            click.echo("=" * 30)
            total = sum(stats.values())
            click.echo(f"{'Total Records':20}: {total:>6}")
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
@click.confirmation_option(
    prompt="⚠️  Are you sure you want to delete ALL data from the database?"
)
def db_truncate():
    """Truncate all database tables (DANGEROUS!)."""
    click.echo("🗑️  Truncating all database tables...")
    
    try:
        with Session(database_service.engine) as session:
            # Order matters due to foreign key constraints
            tables_to_truncate = [
                AgentExecution,
                AnalysisReport,
                Competitor,
                Product,
                AnalysisTask,
            ]
            
            for table_model in tables_to_truncate:
                table_name = table_model.__tablename__
                stmt = delete(table_model)
                result = session.exec(stmt)
                click.echo(f"  Deleted {result.rowcount} rows from {table_name}")
            
            session.commit()
            
        click.echo("✅ All tables have been truncated successfully")
        logger.info("database_truncated", environment=settings.ENVIRONMENT.value)
        
    except Exception as e:
        click.echo(f"❌ Failed to truncate tables: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--asin', help='Delete data for specific ASIN')
@click.option('--task-id', help='Delete data for specific task ID')
def db_delete(asin, task_id):
    """Delete specific analysis data."""
    if not asin and not task_id:
        click.echo("❌ Must provide either --asin or --task-id", err=True)
        raise click.Abort()
    
    if asin and task_id:
        click.echo("❌ Provide only one of --asin or --task-id", err=True)
        raise click.Abort()
    
    target = f"ASIN {asin}" if asin else f"Task {task_id}"
    click.echo(f"🗑️  Deleting data for {target}...")
    
    try:
        with Session(database_service.engine) as session:
            deleted_items = []
            
            if task_id:
                # Delete by task ID
                # Delete agent executions
                stmt = delete(AgentExecution).where(AgentExecution.task_id == task_id)
                result = session.exec(stmt)
                if result.rowcount > 0:
                    deleted_items.append(f"Agent executions: {result.rowcount}")
                
                # Delete reports
                stmt = delete(AnalysisReport).where(AnalysisReport.task_id == task_id)
                result = session.exec(stmt)
                if result.rowcount > 0:
                    deleted_items.append(f"Reports: {result.rowcount}")
                
                # Delete task
                stmt = delete(AnalysisTask).where(AnalysisTask.id == task_id)
                result = session.exec(stmt)
                if result.rowcount > 0:
                    deleted_items.append(f"Tasks: {result.rowcount}")
            
            elif asin:
                # Delete by ASIN
                # First find all tasks for this ASIN
                tasks = session.exec(
                    select(AnalysisTask.id).where(AnalysisTask.asin == asin)
                ).all()
                
                if tasks:
                    task_ids = [str(task) for task in tasks]
                    
                    # Delete agent executions
                    stmt = delete(AgentExecution).where(AgentExecution.task_id.in_(task_ids))
                    result = session.exec(stmt)
                    if result.rowcount > 0:
                        deleted_items.append(f"Agent executions: {result.rowcount}")
                    
                    # Delete reports
                    stmt = delete(AnalysisReport).where(AnalysisReport.asin == asin)
                    result = session.exec(stmt)
                    if result.rowcount > 0:
                        deleted_items.append(f"Reports: {result.rowcount}")
                    
                    # Delete tasks
                    stmt = delete(AnalysisTask).where(AnalysisTask.asin == asin)
                    result = session.exec(stmt)
                    if result.rowcount > 0:
                        deleted_items.append(f"Tasks: {result.rowcount}")
                
                # Delete competitors
                stmt = delete(Competitor).where(Competitor.main_product_asin == asin)
                result = session.exec(stmt)
                if result.rowcount > 0:
                    deleted_items.append(f"Competitors: {result.rowcount}")
                
                # Delete product
                stmt = delete(Product).where(Product.asin == asin)
                result = session.exec(stmt)
                if result.rowcount > 0:
                    deleted_items.append(f"Products: {result.rowcount}")
            
            session.commit()
            
            if deleted_items:
                click.echo(f"✅ Deleted: {', '.join(deleted_items)}")
            else:
                click.echo("ℹ️ No data found to delete")
                
    except Exception as e:
        click.echo(f"❌ Failed to delete data: {str(e)}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()