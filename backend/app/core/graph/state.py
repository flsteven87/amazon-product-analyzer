"""State definitions for the multi-agent product analysis system."""

from typing import List, Dict, Any, Annotated, TypedDict, Optional
from uuid import UUID

from langgraph.graph.message import AnyMessage, add_messages


class AnalysisState(TypedDict):
    """The state of the multi-agent product analysis system.

    This state is shared between all agents and the supervisor.
    Extends the original AgentState with database integration capabilities.
    """

    # Database integration
    task_id: Optional[UUID]  # Analysis task ID for database tracking
    user_id: Optional[UUID]  # User ID if authenticated

    # Product information
    product_url: str
    asin: Optional[str]  # Extracted ASIN

    # Inter-agent communication (using LangGraph's message handling)
    messages: Annotated[List[AnyMessage], add_messages]

    # Current agent that should act next
    next_agent: str

    # Agent output data
    product_data: Dict[str, Any]
    market_analysis: Dict[str, Any]
    optimization_advice: Dict[str, Any]

    # Competitor data
    competitor_candidates: List[Dict[str, Any]]
    competitor_data: List[Dict[str, Any]]

    # Analysis phase control
    analysis_phase: str  # "main_product", "competitor_collection", "analysis"

    # Workflow control
    iteration_count: int
    max_iterations: int

    # Progress tracking
    progress: int  # 0-100
    status: str  # "pending", "processing", "completed", "failed"
    error_message: Optional[str]

    # Final analysis result
    final_analysis: str

    # Metadata for reporting
    analysis_metadata: Dict[str, Any]


class AgentExecutionContext:
    """Context for individual agent execution with database integration."""

    def __init__(self, task_id: UUID, agent_name: str):
        self.task_id = task_id
        self.agent_name = agent_name
        self.start_time = None
        self.end_time = None
        self.input_data = None
        self.output_data = None
        self.error_message = None
        self.execution_id = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for database storage."""
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "execution_time_ms": self._calculate_execution_time(),
        }

    def _calculate_execution_time(self) -> Optional[int]:
        """Calculate execution time in milliseconds."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return None
