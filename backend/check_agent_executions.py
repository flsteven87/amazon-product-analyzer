#!/usr/bin/env python3
"""Script to check agent execution records in the database."""

import os
import sys
from datetime import datetime
from typing import List

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from sqlmodel import Session, select
from app.core.config import settings
from app.services.database import database_service
from app.models.analysis import AgentExecution, AnalysisTask, AgentStatus


def check_agent_executions():
    """Check agent execution records in the database."""
    try:
        with Session(database_service.engine) as session:
            print("=" * 60)
            print("AGENT EXECUTION RECORDS CHECK")
            print("=" * 60)
            
            # 1. Check total count of agent executions
            total_executions = session.exec(select(AgentExecution)).all()
            print(f"\n1. Total Agent Executions: {len(total_executions)}")
            
            if len(total_executions) == 0:
                print("   No agent execution records found in the database.")
                return
            
            # 2. Check status distribution
            status_counts = {}
            for execution in total_executions:
                status = execution.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print("\n2. Agent Execution Status Distribution:")
            for status, count in status_counts.items():
                print(f"   {status.upper()}: {count}")
            
            # 3. Check for currently running agents
            running_executions = session.exec(
                select(AgentExecution).where(AgentExecution.status == AgentStatus.RUNNING)
            ).all()
            
            print(f"\n3. Currently Running Agents: {len(running_executions)}")
            if running_executions:
                for execution in running_executions:
                    print(f"   - {execution.agent_name} (ID: {execution.id}, Started: {execution.started_at})")
            
            # 4. Show recent executions (last 10)
            recent_executions = session.exec(
                select(AgentExecution)
                .order_by(AgentExecution.started_at.desc())
                .limit(10)
            ).all()
            
            print("\n4. Recent Agent Executions (Last 10):")
            if recent_executions:
                print(f"   {'Agent Name':<20} {'Status':<12} {'Started':<20} {'Duration (ms)':<15}")
                print(f"   {'-' * 20} {'-' * 12} {'-' * 20} {'-' * 15}")
                
                for execution in recent_executions:
                    duration = execution.execution_time_ms if execution.execution_time_ms else "N/A"
                    started_str = execution.started_at.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"   {execution.agent_name:<20} {execution.status.value:<12} {started_str:<20} {duration:<15}")
            else:
                print("   No recent executions found.")
            
            # 5. Check agent execution context creation
            print("\n5. Agent Execution Context Analysis:")
            
            # Group by agent name
            agent_counts = {}
            for execution in total_executions:
                agent_name = execution.agent_name
                agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1
            
            if agent_counts:
                print("   Executions by Agent Type:")
                for agent_name, count in sorted(agent_counts.items()):
                    print(f"   - {agent_name}: {count} executions")
            
            # 6. Check for executions with errors
            failed_executions = session.exec(
                select(AgentExecution).where(AgentExecution.status == AgentStatus.FAILED)
            ).all()
            
            print(f"\n6. Failed Agent Executions: {len(failed_executions)}")
            if failed_executions:
                for execution in failed_executions:
                    error_msg = execution.error_message[:100] + "..." if execution.error_message and len(execution.error_message) > 100 else execution.error_message
                    print(f"   - {execution.agent_name}: {error_msg}")
            
            # 7. Check task association
            executions_with_tasks = session.exec(
                select(AgentExecution, AnalysisTask)
                .join(AnalysisTask, AgentExecution.task_id == AnalysisTask.id)
                .limit(5)
            ).all()
            
            print("\n7. Agent Execution - Task Association (Sample):")
            if executions_with_tasks:
                for execution, task in executions_with_tasks:
                    print(f"   - Agent: {execution.agent_name}, Task: {task.asin}, Task Status: {task.status.value}")
            else:
                print("   No agent executions with associated tasks found.")
            
            print("\n" + "=" * 60)
            print("DATABASE CHECK COMPLETED")
            print("=" * 60)
            
    except Exception as e:
        print(f"Error checking agent executions: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_agent_executions()