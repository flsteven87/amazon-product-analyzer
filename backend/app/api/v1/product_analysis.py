"""Product analysis API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.core.graph import create_analysis_workflow
from app.core.logging import logger
from app.schemas.analysis import (
    AnalysisTaskCreate,
    AnalysisTaskDetailResponse,
    AnalysisTaskResponse,
    AnalysisTaskSummary,
    AnalysisStats,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
)
from app.services.analysis_service import analysis_service

router = APIRouter()


@router.post("/analyze", response_model=AnalysisTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    task_data: AnalysisTaskCreate,
    background_tasks: BackgroundTasks,
) -> AnalysisTaskResponse:
    """Create a new product analysis task.

    Args:
        task_data: Product analysis request data
        background_tasks: FastAPI background tasks

    Returns:
        Created analysis task
    """
    try:
        logger.info("create_analysis_requested", product_url=str(task_data.product_url))

        # Create the analysis task in database
        task = await analysis_service.create_analysis_task(task_data)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create analysis task"
            )

        # Start the analysis workflow in background
        background_tasks.add_task(run_analysis_workflow_sync, task.id, str(task_data.product_url))

        logger.info("analysis_task_created", task_id=str(task.id), asin=task.asin)

        # Create response manually to avoid SQLAlchemy session issues
        return AnalysisTaskResponse(
            id=task.id,
            user_id=task.user_id,
            product_url=task.product_url,
            asin=task.asin,
            status=task.status,
            progress=task.progress,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
        )

    except Exception as e:
        logger.error("create_analysis_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create analysis: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=AnalysisTaskDetailResponse)
async def get_analysis_task(task_id: UUID) -> AnalysisTaskDetailResponse:
    """Get detailed analysis task information.

    Args:
        task_id: Analysis task ID

    Returns:
        Detailed analysis task information
    """
    try:
        logger.info("get_analysis_task_requested", task_id=str(task_id))

        task = await analysis_service.get_analysis_task_with_details(task_id)

        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis task not found")

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_analysis_task_failed", task_id=str(task_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get analysis task: {str(e)}"
        )


@router.get("/tasks/{task_id}/status", response_model=dict)
async def get_analysis_status(task_id: UUID) -> dict:
    """Get analysis task status and progress.

    Args:
        task_id: Analysis task ID

    Returns:
        Task status and progress information
    """
    try:
        logger.info("get_analysis_status_requested", task_id=str(task_id))

        task = await analysis_service.get_analysis_task(task_id)

        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis task not found")

        # Get currently running agent
        current_agent = await analysis_service.get_current_running_agent(task_id)
        
        return {
            "task_id": str(task.id),
            "product_url": task.product_url,
            "status": task.status.value,
            "progress": task.progress,
            "current_agent": current_agent,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_analysis_status_failed", task_id=str(task_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get analysis status: {str(e)}"
        )


@router.get("/tasks", response_model=List[AnalysisTaskSummary])
async def list_analysis_tasks(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of tasks to return"),
    offset: int = Query(default=0, ge=0, description="Number of tasks to skip"),
    status_filter: Optional[str] = Query(default=None, description="Filter by task status"),
) -> List[AnalysisTaskSummary]:
    """List analysis tasks with pagination and filtering.

    Args:
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        status_filter: Optional status filter

    Returns:
        List of analysis task summaries
    """
    try:
        logger.info("list_analysis_tasks_requested", limit=limit, offset=offset, status_filter=status_filter)

        tasks = await analysis_service.list_analysis_tasks(limit=limit, offset=offset, status_filter=status_filter)

        return tasks

    except Exception as e:
        logger.error("list_analysis_tasks_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list analysis tasks: {str(e)}"
        )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis_task(task_id: UUID):
    """Delete an analysis task and all related data.

    Args:
        task_id: Analysis task ID
    """
    try:
        logger.info("delete_analysis_task_requested", task_id=str(task_id))

        success = await analysis_service.delete_analysis_task(task_id)

        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis task not found")

        logger.info("analysis_task_deleted", task_id=str(task_id))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_analysis_task_failed", task_id=str(task_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete analysis task: {str(e)}"
        )


@router.get("/stats", response_model=AnalysisStats)
async def get_analysis_stats() -> AnalysisStats:
    """Get analysis statistics and metrics.

    Returns:
        Analysis statistics
    """
    try:
        logger.info("get_analysis_stats_requested")

        stats = await analysis_service.get_analysis_stats()

        return stats

    except Exception as e:
        logger.error("get_analysis_stats_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get analysis statistics: {str(e)}"
        )


@router.post("/batch", response_model=BatchAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_batch_analysis(
    batch_data: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
) -> BatchAnalysisResponse:
    """Create multiple analysis tasks in batch.

    Args:
        batch_data: Batch analysis request data
        background_tasks: FastAPI background tasks

    Returns:
        Batch analysis response with task IDs
    """
    try:
        logger.info("create_batch_analysis_requested", url_count=len(batch_data.product_urls))

        # Create all tasks in database
        task_ids = []
        for product_url in batch_data.product_urls:
            task_data = AnalysisTaskCreate(product_url=product_url)
            task = await analysis_service.create_analysis_task(task_data)

            if task:
                task_ids.append(task.id)
                # Start analysis workflow in background
                background_tasks.add_task(run_analysis_workflow_sync, task.id, str(product_url))

        # Create batch response
        from datetime import datetime, timezone
        from uuid import uuid4

        batch_response = BatchAnalysisResponse(
            batch_id=uuid4(), task_ids=task_ids, total_tasks=len(task_ids), created_at=datetime.now(timezone.utc)
        )

        logger.info("batch_analysis_created", batch_id=str(batch_response.batch_id), task_count=len(task_ids))

        return batch_response

    except Exception as e:
        logger.error("create_batch_analysis_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create batch analysis: {str(e)}"
        )


def run_analysis_workflow_sync(task_id: UUID, product_url: str):
    """Background task wrapper to run the async analysis workflow.

    Args:
        task_id: Analysis task ID
        product_url: Product URL to analyze
    """
    import asyncio
    
    try:
        # Create new event loop for background task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async workflow
        loop.run_until_complete(_run_analysis_workflow_async(task_id, product_url))
        
    except Exception as e:
        logger.error("analysis_workflow_sync_wrapper_failed", task_id=str(task_id), error=str(e))
    finally:
        try:
            loop.close()
        except Exception:
            pass


async def _run_analysis_workflow_async(task_id: UUID, product_url: str):
    """Internal async function to run the analysis workflow.

    Args:
        task_id: Analysis task ID
        product_url: Product URL to analyze
    """
    try:
        logger.info("analysis_workflow_started", task_id=str(task_id), product_url=product_url)

        # Create and run the analysis workflow
        workflow = create_analysis_workflow()

        # Run the analysis workflow
        final_report = await workflow.run_analysis(product_url=product_url, max_iterations=6, task_id=task_id)

        logger.info("analysis_workflow_completed", task_id=str(task_id), report_length=len(final_report))

    except Exception as e:
        logger.error("analysis_workflow_failed", task_id=str(task_id), error=str(e))

        # Update task status to failed
        from app.schemas.analysis import AnalysisTaskUpdate
        from app.models.analysis import AnalysisStatus

        try:
            update_data = AnalysisTaskUpdate(status=AnalysisStatus.FAILED, error_message=str(e))
            await analysis_service.update_analysis_task(task_id, update_data)
        except Exception as update_error:
            logger.error("failed_to_update_task_status", task_id=str(task_id), error=str(update_error))
