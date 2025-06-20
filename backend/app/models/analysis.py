"""Analysis-related database models."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, Field, JSON, Relationship, SQLModel
from sqlalchemy import Index, Text, UniqueConstraint


class AnalysisStatus(str, Enum):
    """Analysis task status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStatus(str, Enum):
    """Agent execution status enumeration."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportType(str, Enum):
    """Report type enumeration."""

    FULL = "full"
    MARKET = "market"
    OPTIMIZATION = "optimization"


class AnalysisTask(SQLModel, table=True):
    """Analysis task model for tracking product analysis requests."""

    __tablename__ = "analysis_tasks"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, index=True)
    product_url: str = Field(max_length=2048)
    asin: str = Field(max_length=10, index=True)
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING, index=True)
    progress: int = Field(default=0, ge=0, le=100)
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    reports: List["AnalysisReport"] = Relationship(back_populates="task")
    agent_executions: List["AgentExecution"] = Relationship(back_populates="task")

    def __repr__(self) -> str:
        return f"<AnalysisTask(id={self.id}, asin={self.asin}, status={self.status})>"


class Product(SQLModel, table=True):
    """Product model for storing scraped product data."""

    __tablename__ = "products"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    asin: str = Field(max_length=10, unique=True, index=True)
    title: str = Field(sa_column=Column(Text))
    price: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    rating: Optional[Decimal] = Field(default=None, max_digits=2, decimal_places=1)
    review_count: int = Field(default=0)
    availability: Optional[str] = Field(default=None)
    seller: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    features: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    images: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    raw_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    scraped_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<Product(asin={self.asin}, title={self.title[:50]}...)>"


class Competitor(SQLModel, table=True):
    """Competitor model for storing competitor product data."""

    __tablename__ = "competitors"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    main_product_asin: str = Field(max_length=10, index=True)
    competitor_asin: str = Field(max_length=10, index=True)
    title: str = Field(sa_column=Column(Text))
    price: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    rating: Optional[Decimal] = Field(default=None, max_digits=2, decimal_places=1)
    review_count: Optional[int] = Field(default=None)
    brand: Optional[str] = Field(default=None)
    source_section: Optional[str] = Field(default=None)
    confidence_score: Decimal = Field(default=Decimal("0.0"), max_digits=3, decimal_places=2)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (UniqueConstraint("main_product_asin", "competitor_asin"),)

    def __repr__(self) -> str:
        return f"<Competitor(main={self.main_product_asin}, competitor={self.competitor_asin})>"


class AnalysisReport(SQLModel, table=True):
    """Analysis report model for storing generated reports."""

    __tablename__ = "analysis_reports"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="analysis_tasks.id", index=True)
    asin: str = Field(max_length=10, index=True)
    report_type: ReportType = Field(default=ReportType.FULL, index=True)
    content: str = Field(sa_column=Column(Text))
    report_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    task: Optional[AnalysisTask] = Relationship(back_populates="reports")

    def __repr__(self) -> str:
        return f"<AnalysisReport(id={self.id}, asin={self.asin}, type={self.report_type})>"


class AgentExecution(SQLModel, table=True):
    """Agent execution model for tracking individual agent performance."""

    __tablename__ = "agent_executions"

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="analysis_tasks.id", index=True)
    agent_name: str = Field(max_length=50, index=True)
    status: AgentStatus = Field(default=AgentStatus.RUNNING)
    input_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    output_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    execution_time_ms: Optional[int] = Field(default=None)
    started_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    task: Optional[AnalysisTask] = Relationship(back_populates="agent_executions")

    def __repr__(self) -> str:
        return f"<AgentExecution(id={self.id}, agent={self.agent_name}, status={self.status})>"
