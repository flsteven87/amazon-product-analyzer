"""
Analysis API endpoints for Amazon Product Analyzer.

This module provides RESTful API endpoints for analysis session management,
agent coordination, and result retrieval.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, HttpUrl
import uuid
from datetime import datetime

from ..core.database import get_async_db
from ..core.redis_client import redis_client
from ..models.analysis import Analysis, AnalysisSession, AnalysisStatus, AgentType
from ..models.product import Product

router = APIRouter()


# Pydantic models for request/response
class AnalysisSessionCreate(BaseModel):
    """Analysis session creation model."""
    product_url: str
    analysis_config: Optional[dict] = None


class AnalysisSessionResponse(BaseModel):
    """Analysis session response model."""
    id: int
    session_id: str
    product_id: int
    product_url: str
    status: AnalysisStatus
    overall_progress: int
    agent_progress: Optional[dict] = None
    analysis_config: Optional[dict] = None
    results_summary: Optional[dict] = None
    error_message: Optional[str] = None
    retry_count: int
    started_at: str
    completed_at: Optional[str] = None
    last_updated_at: str
    
    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    """Analysis response model."""
    id: int
    product_id: int
    session_id: Optional[int] = None
    agent_type: AgentType
    agent_version: Optional[str] = None
    analysis_data: dict
    recommendations: Optional[list] = None
    insights: Optional[list] = None
    confidence_score: Optional[float] = None
    quality_score: Optional[float] = None
    processing_time_seconds: Optional[float] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    data_sources: Optional[list] = None
    citations: Optional[list] = None
    is_validated: bool
    validation_notes: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ProgressUpdate(BaseModel):
    """Real-time progress update model."""
    agent: str
    progress: int
    status: str
    timestamp: str
    message: Optional[str] = None


@router.post("/sessions", response_model=AnalysisSessionResponse, status_code=201)
async def create_analysis_session(
    session_data: AnalysisSessionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new analysis session and start the analysis workflow.
    
    Args:
        session_data (AnalysisSessionCreate): Session configuration data.
        background_tasks (BackgroundTasks): FastAPI background tasks.
        db (AsyncSession): Database session dependency.
    
    Returns:
        AnalysisSessionResponse: Created analysis session details.
    
    Raises:
        HTTPException: If product creation or analysis startup fails.
    """
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # TODO: Extract ASIN from URL and create/get product
        # For now, create a placeholder product
        # This will be implemented in the scraper service
        placeholder_product = Product(
            asin="PLACEHOLDER",
            url=session_data.product_url,
            title="Product being analyzed..."
        )
        db.add(placeholder_product)
        await db.commit()
        await db.refresh(placeholder_product)
        
        # Create analysis session
        analysis_session = AnalysisSession(
            session_id=session_id,
            product_id=placeholder_product.id,
            product_url=session_data.product_url,
            status=AnalysisStatus.PENDING,
            analysis_config=session_data.analysis_config or {},
            agent_progress={}
        )
        
        db.add(analysis_session)
        await db.commit()
        await db.refresh(analysis_session)
        
        # TODO: Start background analysis task
        # background_tasks.add_task(start_analysis_workflow, session_id, analysis_session.id)
        
        return analysis_session
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create analysis session: {str(e)}")


@router.get("/sessions", response_model=List[AnalysisSessionResponse])
async def get_analysis_sessions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[AnalysisStatus] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve analysis sessions with optional filtering.
    
    Args:
        skip (int): Number of records to skip.
        limit (int): Maximum number of records to return.
        status (Optional[AnalysisStatus]): Filter by session status.
        db (AsyncSession): Database session dependency.
    
    Returns:
        List[AnalysisSessionResponse]: List of analysis sessions.
    """
    query = select(AnalysisSession)
    
    if status:
        query = query.where(AnalysisSession.status == status)
    
    query = query.offset(skip).limit(limit).order_by(AnalysisSession.started_at.desc())
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return sessions


@router.get("/sessions/{session_id}", response_model=AnalysisSessionResponse)
async def get_analysis_session(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve a specific analysis session by session ID.
    
    Args:
        session_id (str): Analysis session ID.
        db (AsyncSession): Database session dependency.
    
    Returns:
        AnalysisSessionResponse: Analysis session details.
    
    Raises:
        HTTPException: If session not found.
    """
    query = select(AnalysisSession).where(AnalysisSession.session_id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Analysis session not found")
    
    return session


@router.get("/sessions/{session_id}/progress")
async def get_analysis_progress(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get real-time analysis progress for a session.
    
    Args:
        session_id (str): Analysis session ID.
        db: Database session dependency.
    
    Returns:
        dict: Current progress information.
    
    Raises:
        HTTPException: If session not found.
    """
    # Verify session exists
    query = select(AnalysisSession).where(AnalysisSession.session_id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Analysis session not found")
    
    # Get progress from Redis cache
    progress_data = await redis_client.get_analysis_progress(session_id)
    
    if not progress_data:
        # Fallback to database
        progress_data = {
            "overall_progress": session.overall_progress,
            "agent_progress": session.agent_progress or {},
            "status": session.status.value,
            "last_updated": session.last_updated_at.isoformat()
        }
    
    return progress_data


@router.delete("/sessions/{session_id}", status_code=204)
async def cancel_analysis_session(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Cancel a running analysis session.
    
    Args:
        session_id (str): Analysis session ID to cancel.
        db (AsyncSession): Database session dependency.
    
    Raises:
        HTTPException: If session not found or cannot be cancelled.
    """
    query = select(AnalysisSession).where(AnalysisSession.session_id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Analysis session not found")
    
    if session.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel session with status: {session.status.value}"
        )
    
    # Update session status
    session.status = AnalysisStatus.CANCELLED
    session.completed_at = datetime.utcnow()
    
    await db.commit()
    
    # TODO: Signal running agents to stop
    # This would involve sending cancellation signals to the agent workflow


@router.get("/sessions/{session_id}/results", response_model=List[AnalysisResponse])
async def get_session_results(
    session_id: str,
    agent_type: Optional[AgentType] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve analysis results for a specific session.
    
    Args:
        session_id (str): Analysis session ID.
        agent_type (Optional[AgentType]): Filter by specific agent type.
        db (AsyncSession): Database session dependency.
    
    Returns:
        List[AnalysisResponse]: List of analysis results.
    
    Raises:
        HTTPException: If session not found.
    """
    # Verify session exists
    session_query = select(AnalysisSession).where(AnalysisSession.session_id == session_id)
    session_result = await db.execute(session_query)
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Analysis session not found")
    
    # Get analysis results
    results_query = select(Analysis).where(Analysis.session_id == session.id)
    
    if agent_type:
        results_query = results_query.where(Analysis.agent_type == agent_type)
    
    results_query = results_query.order_by(Analysis.created_at.desc())
    
    results_result = await db.execute(results_query)
    analyses = results_result.scalars().all()
    
    return analyses


@router.get("/results", response_model=List[AnalysisResponse])
async def get_analysis_results(
    product_id: Optional[int] = None,
    agent_type: Optional[AgentType] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve analysis results with optional filtering.
    
    Args:
        product_id (Optional[int]): Filter by product ID.
        agent_type (Optional[AgentType]): Filter by agent type.
        skip (int): Number of records to skip.
        limit (int): Maximum number of records to return.
        db (AsyncSession): Database session dependency.
    
    Returns:
        List[AnalysisResponse]: List of analysis results.
    """
    query = select(Analysis)
    
    if product_id:
        query = query.where(Analysis.product_id == product_id)
    
    if agent_type:
        query = query.where(Analysis.agent_type == agent_type)
    
    query = query.offset(skip).limit(limit).order_by(Analysis.created_at.desc())
    
    result = await db.execute(query)
    analyses = result.scalars().all()
    
    return analyses 