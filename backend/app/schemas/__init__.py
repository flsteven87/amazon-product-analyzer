"""This file contains the schemas for the application."""

from app.schemas.analysis import (
    AnalysisTaskCreate,
    AnalysisTaskUpdate,
    AnalysisTaskResponse,
    AnalysisTaskDetailResponse,
    AnalysisTaskSummary,
    AnalysisStats,
    ProductResponse,
    CompetitorResponse,
    AnalysisReportResponse,
    AgentExecutionResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
)

__all__ = [
    # Analysis schemas
    "AnalysisTaskCreate",
    "AnalysisTaskUpdate",
    "AnalysisTaskResponse",
    "AnalysisTaskDetailResponse",
    "AnalysisTaskSummary",
    "AnalysisStats",
    "ProductResponse",
    "CompetitorResponse",
    "AnalysisReportResponse",
    "AgentExecutionResponse",
    "BatchAnalysisRequest",
    "BatchAnalysisResponse",
]
