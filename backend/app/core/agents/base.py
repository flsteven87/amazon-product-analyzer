"""Base agent class for the multi-agent system."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID

from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.graph.state import AnalysisState, AgentExecutionContext
from app.core.logging import logger
from app.services.analysis_service import analysis_service
from app.models.analysis import AgentStatus


class BaseAgent:
    """Base class for all agents in the multi-agent system."""

    def __init__(self, llm: ChatOpenAI, agent_name: str):
        """Initialize the base agent.

        Args:
            llm: The language model instance
            agent_name: Name identifier for this agent
        """
        self.llm = llm
        self.agent_name = agent_name
        self.logger = logger

    def __call__(self, state: AnalysisState) -> AnalysisState:
        """Execute the agent with database tracking.

        Args:
            state: Current analysis state

        Returns:
            Updated analysis state
        """
        # Create execution context for database tracking
        context = None
        if state.get("task_id"):
            context = AgentExecutionContext(task_id=state["task_id"], agent_name=self.agent_name)
            context.start_time = datetime.now(timezone.utc)
            context.input_data = self._extract_input_data(state)

        try:
            # Log agent start
            self.logger.info(
                f"{self.agent_name} starting execution",
                task_id=str(state.get("task_id")),
                agent_name=self.agent_name,
                iteration=state.get("iteration_count", 0),
            )
            
            # Save initial RUNNING status
            if context:
                self._save_agent_execution_sync(context, AgentStatus.RUNNING)

            # Execute agent logic
            updated_state = self.execute(state)

            # Track successful completion
            if context:
                context.end_time = datetime.now(timezone.utc)
                context.output_data = self._extract_output_data(updated_state)
                self._save_agent_execution_sync(context, AgentStatus.COMPLETED)

            self.logger.info(
                f"{self.agent_name} completed successfully",
                task_id=str(state.get("task_id")),
                agent_name=self.agent_name,
            )

            return updated_state

        except Exception as e:
            # Track failed execution
            error_msg = f"{self.agent_name} execution failed: {str(e)}"
            self.logger.error(error_msg, task_id=str(state.get("task_id")), agent_name=self.agent_name, error=str(e))

            if context:
                context.end_time = datetime.now(timezone.utc)
                context.error_message = str(e)
                self._save_agent_execution_sync(context, AgentStatus.FAILED)

            # Update state with error information
            state["error_message"] = error_msg
            state["status"] = "failed"

            return state

    def execute(self, state: AnalysisState) -> AnalysisState:
        """Execute the main agent logic. Must be implemented by subclasses.

        Args:
            state: Current analysis state

        Returns:
            Updated analysis state
        """
        raise NotImplementedError("Subclasses must implement execute method")

    def _extract_input_data(self, state: AnalysisState) -> Dict[str, Any]:
        """Extract relevant input data for logging.

        Args:
            state: Current analysis state

        Returns:
            Dictionary of input data
        """
        return {
            "product_url": state.get("product_url"),
            "asin": state.get("asin"),
            "analysis_phase": state.get("analysis_phase"),
            "iteration_count": state.get("iteration_count"),
            "next_agent": state.get("next_agent"),
        }

    def _extract_output_data(self, state: AnalysisState) -> Dict[str, Any]:
        """Extract relevant output data for logging.

        Args:
            state: Updated analysis state

        Returns:
            Dictionary of output data
        """
        return {
            "next_agent": state.get("next_agent"),
            "analysis_phase": state.get("analysis_phase"),
            "progress": state.get("progress"),
            "status": state.get("status"),
            "has_product_data": bool(state.get("product_data")),
            "has_market_analysis": bool(state.get("market_analysis")),
            "has_optimization_advice": bool(state.get("optimization_advice")),
            "competitor_count": len(state.get("competitor_data", [])),
        }

    async def _save_agent_execution(self, context: AgentExecutionContext, status: AgentStatus):
        """Save agent execution data to database.

        Args:
            context: Agent execution context
            status: Final execution status
        """
        try:
            from app.models.analysis import AgentExecution
            from app.services.database import database_service
            from sqlmodel import Session

            with Session(database_service.engine) as session:
                execution = AgentExecution(
                    task_id=context.task_id,
                    agent_name=context.agent_name,
                    status=status,
                    input_data=context.input_data,
                    output_data=context.output_data,
                    error_message=context.error_message,
                    execution_time_ms=context._calculate_execution_time(),
                    started_at=context.start_time,
                    completed_at=context.end_time,
                )

                session.add(execution)
                session.commit()
                session.refresh(execution)

                context.execution_id = execution.id

        except Exception as e:
            self.logger.error(
                f"Failed to save agent execution data: {str(e)}",
                agent_name=self.agent_name,
                task_id=str(context.task_id),
            )

    def _update_progress(self, state: AnalysisState, progress: int):
        """Update analysis progress.

        Args:
            state: Current analysis state
            progress: Progress percentage (0-100)
        """
        state["progress"] = min(100, max(0, progress))

        # Update database if task_id is available
        if state.get("task_id"):
            # Use sync update method to ensure progress is saved
            self._update_task_progress_sync(state["task_id"], progress)
            
            # Also emit WebSocket progress update
            self._emit_websocket_progress_update_sync(state["task_id"], progress)

    async def _update_task_progress(self, task_id: UUID, progress: int):
        """Update task progress in database.

        Args:
            task_id: Analysis task ID
            progress: Progress percentage
        """
        try:
            from app.schemas.analysis import AnalysisTaskUpdate

            update_data = AnalysisTaskUpdate(progress=progress)
            await analysis_service.update_analysis_task(task_id, update_data)

        except Exception as e:
            self.logger.error(f"Failed to update task progress: {str(e)}", task_id=str(task_id), progress=progress)

    def _update_task_progress_sync(self, task_id: UUID, progress: int):
        """Update task progress in database synchronously.

        Args:
            task_id: Analysis task ID
            progress: Progress percentage
        """
        try:
            import asyncio
            from app.schemas.analysis import AnalysisTaskUpdate

            update_data = AnalysisTaskUpdate(progress=progress)

            # Try to get current loop
            try:
                asyncio.get_running_loop()
                # If we have a running loop, create a task
                asyncio.create_task(analysis_service.update_analysis_task(task_id, update_data))
            except RuntimeError:
                # No running loop - run in new loop like we do for saving products
                asyncio.run(analysis_service.update_analysis_task(task_id, update_data))
                
            self.logger.debug(f"Updated task progress to {progress}%", task_id=str(task_id), progress=progress)

        except Exception as e:
            self.logger.error(f"Failed to update task progress synchronously: {str(e)}", task_id=str(task_id), progress=progress)

    def _emit_websocket_progress_update_sync(self, task_id: UUID, progress: int):
        """Emit WebSocket progress update synchronously.

        Args:
            task_id: Analysis task ID
            progress: Progress percentage (0-100)
        """
        try:
            import asyncio
            
            # Try to get current loop
            try:
                asyncio.get_running_loop()
                # If we have a running loop, create a task
                asyncio.create_task(self._emit_websocket_progress_update_async(task_id, progress))
            except RuntimeError:
                # No running loop - run in new loop
                asyncio.run(self._emit_websocket_progress_update_async(task_id, progress))
                
            self.logger.debug(f"Triggered WebSocket progress update to {progress}%", task_id=str(task_id), progress=progress)

        except Exception as e:
            self.logger.error(f"Failed to emit WebSocket progress update synchronously: {str(e)}", task_id=str(task_id), progress=progress)

    async def _emit_websocket_progress_update_async(self, task_id: UUID, progress: int):
        """Emit WebSocket progress update directly.

        Args:
            task_id: Analysis task ID
            progress: Progress percentage (0-100)
        """
        try:
            # Import WebSocket manager directly
            from app.core.websocket_simple import simple_ws_manager
            
            # Determine status based on progress
            if progress == 100:
                status = "completed"
            elif progress > 0:
                status = "processing"
            else:
                status = "pending"
            
            # Emit progress update directly via WebSocket
            await simple_ws_manager.emit_progress_update(
                task_id=str(task_id),
                progress=progress,
                status=status,
                agent_name=self.agent_name,
                message=f"{self.agent_name} progress: {progress}%"
            )
            
            self.logger.info(f"WebSocket progress update emitted: {progress}% for task {task_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to emit WebSocket progress update: {str(e)}", task_id=str(task_id), progress=progress)

    def _save_agent_execution_sync(self, context: AgentExecutionContext, status: AgentStatus):
        """Save agent execution data to database synchronously.

        Args:
            context: Agent execution context
            status: Execution status
        """
        try:
            import asyncio
            
            # Try to get current loop
            try:
                asyncio.get_running_loop()
                # If we have a running loop, create a task
                asyncio.create_task(self._save_agent_execution(context, status))
            except RuntimeError:
                # No running loop - run in new loop
                asyncio.run(self._save_agent_execution(context, status))
                
            self.logger.debug(f"Saved agent execution with status {status.value}", 
                            task_id=str(context.task_id), 
                            agent_name=context.agent_name,
                            status=status.value)

        except Exception as e:
            self.logger.error(f"Failed to save agent execution synchronously: {str(e)}", 
                            task_id=str(context.task_id), 
                            agent_name=context.agent_name,
                            error=str(e))


