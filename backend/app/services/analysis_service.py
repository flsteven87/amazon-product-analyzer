"""Analysis service for managing product analysis operations."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, and_, desc, func, select

from app.core.config import settings
from app.core.logging import logger
from app.models.analysis import (
    AgentExecution,
    AnalysisReport,
    AnalysisStatus,
    AnalysisTask,
    Competitor,
    Product,
    ReportType,
)
from app.schemas.analysis import AnalysisStats, AnalysisTaskCreate, AnalysisTaskUpdate, BatchAnalysisRequest
from app.services.database import database_service


class AnalysisService:
    """Service for managing product analysis operations."""

    def __init__(self):
        """Initialize the analysis service."""
        self.db_service = database_service

    async def create_analysis_task(
        self, task_data: AnalysisTaskCreate, user_id: Optional[UUID] = None
    ) -> AnalysisTask:
        """Create a new analysis task.

        Args:
            task_data: Analysis task creation data
            user_id: Optional user ID for the task

        Returns:
            AnalysisTask: The created analysis task
        """
        try:
            with Session(self.db_service.engine) as session:
                # Extract ASIN from URL
                asin = self._extract_asin_from_url(str(task_data.product_url))

                # Create new task
                task = AnalysisTask(
                    user_id=user_id, product_url=str(task_data.product_url), asin=asin, status=AnalysisStatus.PENDING
                )

                session.add(task)
                session.commit()
                session.refresh(task)

                logger.info(
                    "analysis_task_created", task_id=str(task.id), asin=asin, user_id=str(user_id) if user_id else None
                )
                return task

        except SQLAlchemyError as e:
            logger.error("analysis_task_creation_failed", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to create analysis task")

    async def get_analysis_task(self, task_id: UUID) -> Optional[AnalysisTask]:
        """Get an analysis task by ID.

        Args:
            task_id: The task ID

        Returns:
            Optional[AnalysisTask]: The analysis task if found
        """
        try:
            with Session(self.db_service.engine) as session:
                task = session.get(AnalysisTask, task_id)
                return task
        except SQLAlchemyError as e:
            logger.error("analysis_task_retrieval_failed", task_id=str(task_id), error=str(e))
            return None

    async def update_analysis_task(self, task_id: UUID, update_data: AnalysisTaskUpdate) -> Optional[AnalysisTask]:
        """Update an analysis task.

        Args:
            task_id: The task ID to update
            update_data: The update data

        Returns:
            Optional[AnalysisTask]: The updated task if successful
        """
        try:
            with Session(self.db_service.engine) as session:
                task = session.get(AnalysisTask, task_id)
                if not task:
                    return None

                # Apply updates
                if update_data.status is not None:
                    task.status = update_data.status
                if update_data.progress is not None:
                    task.progress = update_data.progress
                if update_data.error_message is not None:
                    task.error_message = update_data.error_message

                task.updated_at = datetime.now(timezone.utc)

                # Set completion time if status is completed or failed
                if update_data.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
                    task.completed_at = datetime.now(timezone.utc)

                session.add(task)
                session.commit()
                session.refresh(task)

                logger.info("analysis_task_updated", task_id=str(task_id), status=task.status, progress=task.progress)
                return task

        except SQLAlchemyError as e:
            logger.error("analysis_task_update_failed", task_id=str(task_id), error=str(e))
            return None

    async def get_user_analysis_tasks(self, user_id: UUID, limit: int = 50, offset: int = 0) -> List[AnalysisTask]:
        """Get analysis tasks for a user.

        Args:
            user_id: The user ID
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip

        Returns:
            List[AnalysisTask]: List of user's analysis tasks
        """
        try:
            with Session(self.db_service.engine) as session:
                statement = (
                    select(AnalysisTask)
                    .where(AnalysisTask.user_id == user_id)
                    .order_by(desc(AnalysisTask.created_at))
                    .limit(limit)
                    .offset(offset)
                )
                tasks = session.exec(statement).all()
                return list(tasks)
        except SQLAlchemyError as e:
            logger.error("user_analysis_tasks_retrieval_failed", user_id=str(user_id), error=str(e))
            return []

    async def save_product_data(self, product_data: Dict, asin: str) -> Optional[Product]:
        """Save product data to database.

        Args:
            product_data: Product data dictionary
            asin: Product ASIN

        Returns:
            Optional[Product]: The saved product if successful
        """
        try:
            with Session(self.db_service.engine) as session:
                # Check if product already exists
                existing_product = session.exec(select(Product).where(Product.asin == asin)).first()

                if existing_product:
                    # Update existing product
                    product = existing_product
                else:
                    # Create new product
                    product = Product(asin=asin)
                    session.add(product)

                # Update product fields
                product.title = product_data.get("title", "")
                product.price = product_data.get("price")
                product.currency = product_data.get("currency", "USD")
                product.rating = product_data.get("rating")
                product.review_count = product_data.get("review_count", 0)
                product.availability = product_data.get("availability")
                product.seller = product_data.get("seller")
                product.category = product_data.get("category")
                product.features = product_data.get("features", [])
                product.images = product_data.get("images", [])
                product.raw_data = product_data.get("raw_data", {})
                product.scraped_at = datetime.now(timezone.utc)

                session.commit()
                session.refresh(product)

                logger.info("product_data_saved", asin=asin, title=product.title[:50])
                return product

        except SQLAlchemyError as e:
            logger.error("product_data_save_failed", asin=asin, error=str(e))
            return None

    async def save_competitors_data(self, competitors_data: List[Dict], main_asin: str) -> List[Competitor]:
        """Save competitors data to database.

        Args:
            competitors_data: List of competitor data dictionaries
            main_asin: Main product ASIN

        Returns:
            List[Competitor]: List of saved competitors
        """
        saved_competitors = []

        try:
            with Session(self.db_service.engine) as session:
                for comp_data in competitors_data:
                    competitor_asin = comp_data.get("asin")
                    if not competitor_asin:
                        continue

                    # Check if competitor relationship already exists
                    existing_competitor = session.exec(
                        select(Competitor).where(
                            and_(
                                Competitor.main_product_asin == main_asin,
                                Competitor.competitor_asin == competitor_asin,
                            )
                        )
                    ).first()

                    if existing_competitor:
                        competitor = existing_competitor
                    else:
                        competitor = Competitor(main_product_asin=main_asin, competitor_asin=competitor_asin)
                        session.add(competitor)

                    # Update competitor fields
                    competitor.title = comp_data.get("title", "")
                    competitor.price = comp_data.get("price")
                    competitor.rating = comp_data.get("rating")
                    competitor.review_count = comp_data.get("review_count")
                    competitor.brand = comp_data.get("brand")
                    competitor.source_section = comp_data.get("source_section")
                    competitor.confidence_score = comp_data.get("confidence_score", 0.0)
                    competitor.discovered_at = datetime.now(timezone.utc)

                    saved_competitors.append(competitor)

                session.commit()

                logger.info("competitors_data_saved", main_asin=main_asin, count=len(saved_competitors))
                return saved_competitors

        except SQLAlchemyError as e:
            logger.error("competitors_data_save_failed", main_asin=main_asin, error=str(e))
            return saved_competitors

    async def save_analysis_report(
        self,
        task_id: UUID,
        asin: str,
        content: str,
        report_type: ReportType = ReportType.FULL,
        metadata: Optional[Dict] = None,
    ) -> Optional[AnalysisReport]:
        """Save analysis report to database.

        Args:
            task_id: Analysis task ID
            asin: Product ASIN
            content: Report content
            report_type: Type of report
            metadata: Optional metadata

        Returns:
            Optional[AnalysisReport]: The saved report if successful
        """
        try:
            with Session(self.db_service.engine) as session:
                report = AnalysisReport(
                    task_id=task_id,
                    asin=asin,
                    report_type=report_type,
                    content=content,
                    report_metadata=metadata or {},
                )

                session.add(report)
                session.commit()
                session.refresh(report)

                logger.info("analysis_report_saved", task_id=str(task_id), asin=asin, report_type=report_type)
                return report

        except SQLAlchemyError as e:
            logger.error("analysis_report_save_failed", task_id=str(task_id), error=str(e))
            return None

    async def get_analysis_stats(self, user_id: Optional[UUID] = None) -> AnalysisStats:
        """Get analysis statistics.

        Args:
            user_id: Optional user ID to filter stats

        Returns:
            AnalysisStats: Analysis statistics
        """
        try:
            with Session(self.db_service.engine) as session:
                # Base query
                base_query = select(AnalysisTask)
                if user_id:
                    base_query = base_query.where(AnalysisTask.user_id == user_id)

                # Get total tasks
                total_tasks = len(session.exec(base_query).all())

                # Get status counts
                status_counts = {}
                for status in AnalysisStatus:
                    count_query = base_query.where(AnalysisTask.status == status)
                    status_counts[status] = len(session.exec(count_query).all())

                # Calculate average completion time
                completion_query = base_query.where(
                    and_(
                        AnalysisTask.status == AnalysisStatus.COMPLETED,
                        AnalysisTask.completed_at.is_not(None),
                        AnalysisTask.created_at.is_not(None),
                    )
                )
                completed_tasks = session.exec(completion_query).all()

                avg_completion_time_minutes = None
                if completed_tasks:
                    total_duration = sum(
                        (task.completed_at - task.created_at).total_seconds() / 60
                        for task in completed_tasks
                        if task.completed_at and task.created_at
                    )
                    avg_completion_time_minutes = round(total_duration / len(completed_tasks), 2)

                return AnalysisStats(
                    total_tasks=total_tasks,
                    completed_tasks=status_counts.get(AnalysisStatus.COMPLETED, 0),
                    failed_tasks=status_counts.get(AnalysisStatus.FAILED, 0),
                    pending_tasks=status_counts.get(AnalysisStatus.PENDING, 0),
                    processing_tasks=status_counts.get(AnalysisStatus.PROCESSING, 0),
                    avg_completion_time_minutes=avg_completion_time_minutes,
                )

        except SQLAlchemyError as e:
            logger.error("analysis_stats_retrieval_failed", error=str(e))
            return AnalysisStats()

    def _extract_asin_from_url(self, url: str) -> str:
        """Extract ASIN from Amazon product URL.

        Args:
            url: Amazon product URL

        Returns:
            str: Extracted ASIN

        Raises:
            ValueError: If ASIN cannot be extracted
        """
        import re

        # Common Amazon URL patterns
        patterns = [
            r"/dp/([A-Z0-9]{10})",
            r"/gp/product/([A-Z0-9]{10})",
            r"asin=([A-Z0-9]{10})",
            r"/product/([A-Z0-9]{10})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        raise ValueError(f"Could not extract ASIN from URL: {url}")

    async def get_analysis_task_with_details(self, task_id: UUID):
        """Get analysis task with all related details.

        Args:
            task_id: Analysis task ID

        Returns:
            Detailed analysis task with reports and executions
        """
        try:
            with Session(self.db_service.engine) as session:
                # Get the main task
                task = session.get(AnalysisTask, task_id)
                if not task:
                    return None

                # Get related reports
                reports_query = select(AnalysisReport).where(AnalysisReport.task_id == task_id)
                reports = session.exec(reports_query).all()

                # Get related agent executions
                executions_query = (
                    select(AgentExecution).where(AgentExecution.task_id == task_id).order_by(AgentExecution.started_at)
                )
                executions = session.exec(executions_query).all()

                # Get product data
                product = None
                if task.asin:
                    product = session.exec(select(Product).where(Product.asin == task.asin)).first()

                # Get competitors
                competitors = []
                if task.asin:
                    competitors_query = select(Competitor).where(Competitor.main_product_asin == task.asin)
                    competitors = session.exec(competitors_query).all()

                # Create response object
                from app.schemas.analysis import (
                    AnalysisTaskDetailResponse,
                    AnalysisReportResponse,
                    AgentExecutionResponse,
                    ProductResponse,
                    CompetitorResponse,
                )

                response = AnalysisTaskDetailResponse(
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
                    product=ProductResponse.model_validate(product) if product else None,
                    competitors=[CompetitorResponse.model_validate(comp) for comp in competitors],
                    reports=[AnalysisReportResponse.model_validate(report) for report in reports],
                    agent_executions=[AgentExecutionResponse.model_validate(execution) for execution in executions],
                )

                return response

        except SQLAlchemyError as e:
            logger.error("analysis_task_details_retrieval_failed", task_id=str(task_id), error=str(e))
            return None

    async def list_analysis_tasks(
        self, limit: int = 50, offset: int = 0, status_filter: Optional[str] = None, user_id: Optional[UUID] = None
    ):
        """List analysis tasks with pagination and filtering.

        Args:
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            status_filter: Optional status filter
            user_id: Optional user ID filter

        Returns:
            List of analysis task summaries
        """
        try:
            with Session(self.db_service.engine) as session:
                # Build query
                query = select(AnalysisTask)

                # Apply filters
                if user_id:
                    query = query.where(AnalysisTask.user_id == user_id)

                if status_filter:
                    try:
                        status_enum = AnalysisStatus(status_filter)
                        query = query.where(AnalysisTask.status == status_enum)
                    except ValueError:
                        logger.warning("invalid_status_filter", status_filter=status_filter)

                # Add ordering and pagination
                query = query.order_by(desc(AnalysisTask.created_at)).limit(limit).offset(offset)

                tasks = session.exec(query).all()

                # Convert to summary format
                from app.schemas.analysis import AnalysisTaskSummary

                summaries = []
                for task in tasks:
                    # Get product title if available
                    product_title = None
                    if task.asin:
                        product = session.exec(select(Product).where(Product.asin == task.asin)).first()
                        product_title = product.title if product else None

                    summary = AnalysisTaskSummary(
                        id=task.id,
                        asin=task.asin,
                        product_title=product_title,
                        status=task.status,
                        progress=task.progress,
                        created_at=task.created_at,
                        completed_at=task.completed_at,
                    )
                    summaries.append(summary)

                return summaries

        except SQLAlchemyError as e:
            logger.error("analysis_tasks_listing_failed", error=str(e))
            return []

    async def delete_analysis_task(self, task_id: UUID) -> bool:
        """Delete an analysis task and all related data.

        Args:
            task_id: Analysis task ID

        Returns:
            bool: True if deletion was successful
        """
        try:
            with Session(self.db_service.engine) as session:
                # Get the task
                task = session.get(AnalysisTask, task_id)
                if not task:
                    return False

                # Delete related data (due to foreign key constraints, we need to delete in order)

                # Delete agent executions
                executions_query = select(AgentExecution).where(AgentExecution.task_id == task_id)
                executions = session.exec(executions_query).all()
                for execution in executions:
                    session.delete(execution)

                # Delete analysis reports
                reports_query = select(AnalysisReport).where(AnalysisReport.task_id == task_id)
                reports = session.exec(reports_query).all()
                for report in reports:
                    session.delete(report)

                # Delete the task itself
                session.delete(task)
                session.commit()

                logger.info("analysis_task_deleted", task_id=str(task_id))
                return True

        except SQLAlchemyError as e:
            logger.error("analysis_task_deletion_failed", task_id=str(task_id), error=str(e))
            return False

    async def get_current_running_agent(self, task_id: UUID) -> Optional[Dict[str, str]]:
        """Get the currently running agent for a task.
        
        Args:
            task_id: Analysis task ID
            
        Returns:
            Dictionary with current agent info or None
        """
        try:
            with Session(self.db_service.engine) as session:
                # Get the most recent RUNNING agent execution
                from app.models.analysis import AgentStatus
                
                query = (
                    select(AgentExecution)
                    .where(
                        and_(
                            AgentExecution.task_id == task_id,
                            AgentExecution.status == AgentStatus.RUNNING
                        )
                    )
                    .order_by(desc(AgentExecution.started_at))
                    .limit(1)
                )
                
                running_agent = session.exec(query).first()
                
                if running_agent:
                    return {
                        "agent_name": running_agent.agent_name,
                        "display_name": self._get_agent_display_name(running_agent.agent_name),
                        "started_at": running_agent.started_at.isoformat(),
                        "status": running_agent.status.value
                    }
                
                return None
                
        except SQLAlchemyError as e:
            logger.error("get_current_running_agent_failed", task_id=str(task_id), error=str(e))
            return None

    def _get_agent_display_name(self, agent_name: str) -> str:
        """Convert agent names to user-friendly display names.
        
        Args:
            agent_name: Internal agent name
            
        Returns:
            User-friendly display name
        """
        display_names = {
            "SupervisorAgent": "Coordinating Analysis",
            "DataCollectorAgent": "Data Collector",
            "MarketAnalyzerAgent": "Market Analyzer", 
            "OptimizationAdvisorAgent": "Optimization Advisor"
        }
        return display_names.get(agent_name, agent_name)


# Create a singleton instance
analysis_service = AnalysisService()
