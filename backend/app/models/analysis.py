"""
Analysis-related SQLAlchemy models for the Amazon Product Analyzer.

This module defines the Analysis and AnalysisSession models for tracking
AI agent analysis results and session management.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped

from ..core.database import Base


class AnalysisStatus(str, Enum):
    """
    Enumeration for analysis session status.
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    """
    Enumeration for different types of analysis agents.
    """
    SUPERVISOR = "supervisor"
    DATA_COLLECTOR = "data_collector"
    MARKET_ANALYZER = "market_analyzer"
    OPTIMIZATION_ADVISOR = "optimization_advisor"


class AnalysisSession(Base):
    """
    Analysis session model representing a complete analysis workflow.
    
    Tracks the overall progress and results of a multi-agent analysis
    for a specific product.
    """
    
    __tablename__ = "analysis_sessions"
    
    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to product
    product_id: Mapped[int] = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Session identification
    session_id: Mapped[str] = Column(String(100), unique=True, index=True, nullable=False)
    product_url: Mapped[str] = Column(Text, nullable=False)
    
    # Session status and progress
    status: Mapped[AnalysisStatus] = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING)
    overall_progress: Mapped[int] = Column(Integer, default=0)  # 0-100 percentage
    
    # Agent progress tracking
    agent_progress: Mapped[Optional[dict]] = Column(JSON, nullable=True)  # {agent_name: {progress: int, status: str}}
    
    # Analysis configuration
    analysis_config: Mapped[Optional[dict]] = Column(JSON, nullable=True)  # Configuration parameters
    
    # Results summary
    results_summary: Mapped[Optional[dict]] = Column(JSON, nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = Column(Text, nullable=True)
    retry_count: Mapped[int] = Column(Integer, default=0)
    
    # Timestamps
    started_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    last_updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="analysis_sessions")
    analyses: Mapped[List["Analysis"]] = relationship("Analysis", back_populates="session")
    
    def __repr__(self) -> str:
        return f"<AnalysisSession(id={self.id}, session_id='{self.session_id}', status='{self.status}')>"


class Analysis(Base):
    """
    Analysis model representing individual agent analysis results.
    
    Stores the specific analysis data, recommendations, and metadata
    from each specialized agent.
    """
    
    __tablename__ = "analyses"
    
    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    product_id: Mapped[int] = Column(Integer, ForeignKey("products.id"), nullable=False)
    session_id: Mapped[Optional[int]] = Column(Integer, ForeignKey("analysis_sessions.id"), nullable=True)
    
    # Agent information
    agent_type: Mapped[AgentType] = Column(SQLEnum(AgentType), nullable=False)
    agent_version: Mapped[Optional[str]] = Column(String(50), nullable=True)
    
    # Analysis data
    analysis_data: Mapped[dict] = Column(JSON, nullable=False)  # Core analysis results
    recommendations: Mapped[Optional[list]] = Column(JSON, nullable=True)  # Agent recommendations
    insights: Mapped[Optional[list]] = Column(JSON, nullable=True)  # Key insights
    
    # Metrics and scoring
    confidence_score: Mapped[Optional[float]] = Column(Float, nullable=True)  # 0-1 confidence
    quality_score: Mapped[Optional[float]] = Column(Float, nullable=True)  # 0-1 quality assessment
    
    # Processing metadata
    processing_time_seconds: Mapped[Optional[float]] = Column(Float, nullable=True)
    tokens_used: Mapped[Optional[int]] = Column(Integer, nullable=True)  # For AI models
    model_used: Mapped[Optional[str]] = Column(String(100), nullable=True)  # AI model identifier
    
    # Data sources and citations
    data_sources: Mapped[Optional[list]] = Column(JSON, nullable=True)  # Sources used for analysis
    citations: Mapped[Optional[list]] = Column(JSON, nullable=True)  # Reference citations
    
    # Validation and review
    is_validated: Mapped[bool] = Column(Integer, default=False)
    validation_notes: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product")
    session: Mapped[Optional["AnalysisSession"]] = relationship("AnalysisSession", back_populates="analyses")
    
    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, agent_type='{self.agent_type}', confidence_score={self.confidence_score})>"


class AnalysisMetric(Base):
    """
    Analysis metrics model for tracking performance and quality metrics.
    
    Stores detailed metrics about analysis performance, accuracy,
    and business impact.
    """
    
    __tablename__ = "analysis_metrics"
    
    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to analysis
    analysis_id: Mapped[int] = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    
    # Metric information
    metric_name: Mapped[str] = Column(String(100), nullable=False)
    metric_value: Mapped[float] = Column(Float, nullable=False)
    metric_unit: Mapped[Optional[str]] = Column(String(50), nullable=True)
    
    # Metric metadata
    metric_category: Mapped[Optional[str]] = Column(String(100), nullable=True)  # e.g., "performance", "accuracy"
    benchmark_value: Mapped[Optional[float]] = Column(Float, nullable=True)
    is_improvement: Mapped[Optional[bool]] = Column(Integer, nullable=True)
    
    # Timestamps
    recorded_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis")
    
    def __repr__(self) -> str:
        return f"<AnalysisMetric(id={self.id}, name='{self.metric_name}', value={self.metric_value})>" 