"""Analysis-related Pydantic schemas for API request/response models."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, validator

from app.models.analysis import AnalysisStatus, AgentStatus, ReportType


# Base schemas
class ProductBase(BaseModel):
    """Base product schema with common fields."""

    asin: str = Field(..., min_length=10, max_length=10, description="Amazon Standard Identification Number")
    title: str = Field(..., min_length=1, max_length=500, description="Product title")
    price: Optional[Decimal] = Field(None, ge=0, description="Product price")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code")
    rating: Optional[Decimal] = Field(None, ge=0, le=5, description="Product rating out of 5")
    review_count: int = Field(default=0, ge=0, description="Number of reviews")
    availability: Optional[str] = Field(None, description="Product availability status")
    seller: Optional[str] = Field(None, description="Product seller")
    category: Optional[str] = Field(None, description="Product category")


class CompetitorBase(BaseModel):
    """Base competitor schema with common fields."""

    competitor_asin: str = Field(..., min_length=10, max_length=10)
    title: str = Field(..., min_length=1, max_length=500)
    price: Optional[Decimal] = Field(None, ge=0)
    rating: Optional[Decimal] = Field(None, ge=0, le=5)
    review_count: Optional[int] = Field(None, ge=0)
    brand: Optional[str] = None
    source_section: Optional[str] = None
    confidence_score: Decimal = Field(default=Decimal("0.0"), ge=0, le=1)


# Request schemas
class AnalysisTaskCreate(BaseModel):
    """Schema for creating a new analysis task."""

    product_url: HttpUrl = Field(..., description="Amazon product URL to analyze")

    @validator("product_url")
    def validate_amazon_url(cls, v):
        """Validate that the URL is from Amazon."""
        url_str = str(v)
        if not any(domain in url_str.lower() for domain in ["amazon.com", "amazon.co.uk", "amazon.de"]):
            raise ValueError("URL must be from a supported Amazon domain")
        return v


class AnalysisTaskUpdate(BaseModel):
    """Schema for updating an analysis task."""

    status: Optional[AnalysisStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    error_message: Optional[str] = None


# Response schemas
class ProductResponse(ProductBase):
    """Schema for product response."""

    id: UUID
    features: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    scraped_at: datetime

    class Config:
        from_attributes = True


class CompetitorResponse(CompetitorBase):
    """Schema for competitor response."""

    id: UUID
    main_product_asin: str
    discovered_at: datetime

    class Config:
        from_attributes = True


class AnalysisReportResponse(BaseModel):
    """Schema for analysis report response."""

    id: UUID
    task_id: UUID
    asin: str
    report_type: ReportType
    content: str
    report_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class AgentExecutionResponse(BaseModel):
    """Schema for agent execution response."""

    id: UUID
    task_id: UUID
    agent_name: str
    status: AgentStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisTaskResponse(BaseModel):
    """Schema for analysis task response."""

    id: UUID
    user_id: Optional[UUID] = None
    product_url: str
    asin: str
    status: AnalysisStatus
    progress: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    # Optional nested data
    reports: Optional[List[AnalysisReportResponse]] = None
    agent_executions: Optional[List[AgentExecutionResponse]] = None

    class Config:
        from_attributes = True


class AnalysisTaskDetailResponse(AnalysisTaskResponse):
    """Detailed analysis task response with all related data."""

    product: Optional[ProductResponse] = None
    competitors: Optional[List[CompetitorResponse]] = None
    reports: List[AnalysisReportResponse] = Field(default_factory=list)
    agent_executions: List[AgentExecutionResponse] = Field(default_factory=list)


# Summary schemas for dashboard/listing views
class AnalysisTaskSummary(BaseModel):
    """Summary schema for analysis task listing."""

    id: UUID
    asin: str
    product_title: Optional[str] = None
    status: AnalysisStatus
    progress: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisStats(BaseModel):
    """Schema for analysis statistics."""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    pending_tasks: int = 0
    processing_tasks: int = 0
    avg_completion_time_minutes: Optional[float] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_tasks == 0:
            return 0.0
        return round((self.completed_tasks / self.total_tasks) * 100, 2)


# Batch operation schemas
class BatchAnalysisRequest(BaseModel):
    """Schema for batch analysis requests."""

    product_urls: List[HttpUrl] = Field(..., min_items=1, max_items=10, description="List of Amazon product URLs")

    @validator("product_urls")
    def validate_all_amazon_urls(cls, v):
        """Validate that all URLs are from Amazon."""
        for url in v:
            url_str = str(url)
            if not any(domain in url_str.lower() for domain in ["amazon.com", "amazon.co.uk", "amazon.de"]):
                raise ValueError(f"URL {url_str} must be from a supported Amazon domain")
        return v


class BatchAnalysisResponse(BaseModel):
    """Schema for batch analysis response."""

    batch_id: UUID
    task_ids: List[UUID]
    total_tasks: int
    created_at: datetime
