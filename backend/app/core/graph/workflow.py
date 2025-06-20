"""Multi-agent workflow implementation using LangGraph with database integration."""

import asyncio
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.core.graph.state import AnalysisState

# Avoid circular imports - import agents within methods
from app.core.logging import logger
from app.services.analysis_service import analysis_service
from app.models.analysis import AnalysisStatus, ReportType


class ProductAnalysisWorkflow:
    """LangGraph workflow for product analysis with database integration."""

    def __init__(self, llm_api_key: Optional[str] = None):
        """Initialize the workflow with LLM and agents.

        Args:
            llm_api_key: OpenAI API key, defaults to settings
        """
        # Initialize LLM
        api_key = llm_api_key or settings.LLM_API_KEY
        self.llm = ChatOpenAI(model=settings.LLM_MODEL, temperature=settings.DEFAULT_LLM_TEMPERATURE, api_key=api_key)

        # Initialize agents (import here to avoid circular imports)
        from app.core.agents.data_collector import DataCollectorAgent
        from app.core.agents.market_analyzer import MarketAnalyzerAgent
        from app.core.agents.optimization_advisor import OptimizationAdvisorAgent
        from app.core.agents.supervisor import SupervisorAgent

        self.data_collector = DataCollectorAgent(self.llm)
        self.market_analyzer = MarketAnalyzerAgent(self.llm)
        self.optimization_advisor = OptimizationAdvisorAgent(self.llm)
        self.supervisor = SupervisorAgent(self.llm)

        # Create the workflow graph
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create the LangGraph state graph."""
        workflow = StateGraph(AnalysisState)

        # Add nodes for each agent
        workflow.add_node("supervisor", self.supervisor)
        workflow.add_node("data_collector", self.data_collector)
        workflow.add_node("market_analyzer", self.market_analyzer)
        workflow.add_node("optimization_advisor", self.optimization_advisor)

        # Add final compilation node
        workflow.add_node("compile_results", self._compile_final_analysis)

        # Define routing function
        def route_supervisor(
            state: AnalysisState,
        ) -> Literal["data_collector", "market_analyzer", "optimization_advisor", "compile_results"]:
            """Route to the next agent based on supervisor's decision."""
            next_agent = state.get("next_agent", "").lower()

            if next_agent == "finish":
                return "compile_results"
            elif next_agent in ["data_collector", "market_analyzer", "optimization_advisor"]:
                return next_agent
            else:
                # Default to data collector if something goes wrong
                return "data_collector"

        # Set up the graph edges
        workflow.set_entry_point("supervisor")

        # Supervisor decides next agent
        workflow.add_conditional_edges(
            "supervisor",
            route_supervisor,
            {
                "data_collector": "data_collector",
                "market_analyzer": "market_analyzer",
                "optimization_advisor": "optimization_advisor",
                "compile_results": "compile_results",
            },
        )

        # Each agent goes back to supervisor
        workflow.add_edge("data_collector", "supervisor")
        workflow.add_edge("market_analyzer", "supervisor")
        workflow.add_edge("optimization_advisor", "supervisor")

        # Compile results leads to END
        workflow.add_edge("compile_results", END)

        return workflow.compile()

    def _compile_final_analysis(self, state: AnalysisState) -> AnalysisState:
        """Compile all analyses into a final report with database saving."""
        logger.info("Compiling final analysis report")

        # Update final progress
        state["progress"] = 100
        state["status"] = "completed"

        # Extract data for report compilation
        product_data = state.get("product_data", {})
        market_analysis = state.get("market_analysis", {})
        optimization_advice = state.get("optimization_advice", {})

        # Generate formatted report using new unified format
        final_report = self._generate_formatted_report(state, product_data, market_analysis, optimization_advice)

        state["final_analysis"] = final_report

        # Save report to database if task_id is available
        if state.get("task_id"):
            # Use asyncio.run to ensure the save operation completes
            try:
                import asyncio
                
                # Try to get current loop
                try:
                    asyncio.get_running_loop()
                    # If we have a running loop, create a task
                    asyncio.create_task(self._save_final_report(state, final_report))
                except RuntimeError:
                    # No running loop - run in new loop
                    asyncio.run(self._save_final_report(state, final_report))
                    
            except Exception as e:
                logger.error(f"Failed to save final report: {str(e)}")

        logger.info("Final analysis report compiled successfully")
        return state

    def _extract_product_info_for_report(self, product_data: dict) -> str:
        """Extract product information for the final report."""
        # Try structured analysis first
        if product_data.get("structured_analysis"):
            return product_data["structured_analysis"]

        # Try to format scraped data
        if product_data.get("scraped_data"):
            scraped_data = product_data["scraped_data"]
            parts = ["## Product Data Analysis"]

            # Get ASIN from state if available
            main_asin = product_data.get("main_asin")
            if main_asin:
                parts.append(f"**ASIN:** {main_asin}")

            if scraped_data.get("title"):
                parts.append(f"**Product Title:** {scraped_data['title']}")

            if scraped_data.get("price") is not None:
                price_str = "**Current Price:** "
                if scraped_data.get("currency"):
                    price_str += f"{scraped_data['currency']} {scraped_data['price']:.2f}"
                else:
                    price_str += f"${scraped_data['price']:.2f}"
                parts.append(price_str)

            if scraped_data.get("rating") is not None:
                rating_str = f"**Customer Rating:** {scraped_data['rating']:.1f}/5"
                if scraped_data.get("review_count"):
                    rating_str += f" (based on {scraped_data['review_count']:,} reviews)"
                parts.append(rating_str)

            if scraped_data.get("seller"):
                parts.append(f"**Seller:** {scraped_data['seller']}")

            if scraped_data.get("availability"):
                parts.append(f"**Availability:** {scraped_data['availability']}")

            if scraped_data.get("category"):
                parts.append(f"**Category:** {scraped_data['category']}")

            if scraped_data.get("features"):
                parts.append("**Key Features:**")
                for feature in scraped_data["features"][:8]:  # Show more features in final report
                    parts.append(f"- {feature}")

            return "\n".join(parts)

        # Fallback to LLM analysis
        if product_data.get("llm_analysis"):
            return f"## Product Information (LLM Analysis)\n{product_data['llm_analysis']}"

        # Legacy format
        if product_data.get("raw_analysis"):
            return product_data["raw_analysis"]

        return "No detailed product information available"

    def _create_metadata_section(self, state: dict, product_data: dict) -> str:
        """Create metadata section for the report."""
        url = state.get("product_url", "Unknown")
        asin = state.get("asin", "Unknown")
        iteration = state.get("iteration_count", 0)
        data_source = product_data.get("source", "unknown")

        metadata = f"""# Product Analysis Report

**ASIN:** {asin}
**Product URL:** {url}
**Analysis Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Data Source:** {data_source.replace("_", " ").title()}
**Processing Iterations:** {iteration}
**Analysis Status:** Complete"""

        if data_source == "llm_fallback":
            metadata += "\n**Note:** Analysis based on LLM inference due to scraping limitations"

        return metadata

    async def _save_final_report(self, state: AnalysisState, final_report: str):
        """Save the final report to database."""
        try:
            task_id = state.get("task_id")
            asin = state.get("asin", "unknown")

            if task_id:
                # Update task status
                from app.schemas.analysis import AnalysisTaskUpdate

                update_data = AnalysisTaskUpdate(status=AnalysisStatus.COMPLETED, progress=100)
                await analysis_service.update_analysis_task(task_id, update_data)

                # Save the final report
                await analysis_service.save_analysis_report(
                    task_id=task_id,
                    asin=asin,
                    content=final_report,
                    report_type=ReportType.FULL,
                    metadata=state.get("analysis_metadata", {}),
                )

                logger.info(f"Saved final report to database for task {task_id}")
                
                # Close any remaining RUNNING agent executions
                await self._close_running_agent_executions(task_id)

        except Exception as e:
            logger.error(f"Failed to save final report: {str(e)}")

    async def _close_running_agent_executions(self, task_id: UUID):
        """Close any remaining RUNNING agent executions for a task.
        
        Args:
            task_id: Analysis task ID
        """
        try:
            from app.models.analysis import AgentExecution, AgentStatus
            from app.services.database import database_service
            from sqlmodel import Session, select, and_
            from datetime import datetime, timezone

            with Session(database_service.engine) as session:
                # Find all RUNNING agent executions for this task
                query = select(AgentExecution).where(
                    and_(
                        AgentExecution.task_id == task_id,
                        AgentExecution.status == AgentStatus.RUNNING
                    )
                )
                
                running_executions = session.exec(query).all()
                
                # Update them to COMPLETED
                for execution in running_executions:
                    execution.status = AgentStatus.COMPLETED
                    execution.completed_at = datetime.now(timezone.utc)
                    session.add(execution)
                    
                    logger.info(f"Closed running agent execution: {execution.agent_name}", 
                              task_id=str(task_id), 
                              agent_name=execution.agent_name)
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Failed to close running agent executions: {str(e)}", task_id=str(task_id))

    async def run_analysis(
        self, product_url: str, max_iterations: int = 6, task_id: Optional[UUID] = None, user_id: Optional[UUID] = None
    ) -> str:
        """Run the complete analysis workflow.

        Args:
            product_url: Amazon product URL to analyze
            max_iterations: Maximum number of agent interactions
            task_id: Optional task ID for database tracking
            user_id: Optional user ID for the analysis

        Returns:
            Final analysis report
        """
        logger.info(f"Starting product analysis workflow for: {product_url}")

        # Extract ASIN from URL
        asin = None
        try:
            asin = self._extract_asin_from_url(product_url)
        except ValueError:
            logger.warning("Could not extract ASIN from URL")

        # Initialize state
        initial_state = {
            "task_id": task_id,
            "user_id": user_id,
            "product_url": product_url,
            "asin": asin,
            "messages": [],
            "next_agent": "",
            "product_data": {},
            "market_analysis": {},
            "optimization_advice": {},
            "competitor_candidates": [],
            "competitor_data": [],
            "analysis_phase": "main_product",
            "iteration_count": 0,
            "max_iterations": max_iterations,
            "progress": 0,
            "status": "processing",
            "error_message": None,
            "final_analysis": "",
            "analysis_metadata": {},
        }

        try:
            # Update task status to processing if task_id provided
            if task_id:
                from app.schemas.analysis import AnalysisTaskUpdate

                update_data = AnalysisTaskUpdate(status=AnalysisStatus.PROCESSING, progress=5)
                await analysis_service.update_analysis_task(task_id, update_data)

            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)

            logger.info("Product analysis workflow completed successfully")
            return final_state["final_analysis"]

        except Exception as e:
            logger.error(f"Analysis workflow failed: {str(e)}")

            # Update task status to failed if task_id provided
            if task_id:
                from app.schemas.analysis import AnalysisTaskUpdate

                update_data = AnalysisTaskUpdate(status=AnalysisStatus.FAILED, error_message=str(e))
                await analysis_service.update_analysis_task(task_id, update_data)

            raise

    def _extract_asin_from_url(self, url: str) -> str:
        """Extract ASIN from Amazon product URL."""
        import re

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

    def _generate_formatted_report(self, state: AnalysisState, product_data: dict, market_analysis: dict, optimization_advice: dict) -> str:
        """Generate formatted report using unified format standards.
        
        Args:
            state: Analysis state containing metadata
            product_data: Product information data
            market_analysis: Market analysis results
            optimization_advice: Optimization recommendations
            
        Returns:
            Formatted report string
        """
        # Extract basic information
        
        # Format basic info section
        basic_info = self._format_basic_info(state, product_data)
        
        # Format product overview section
        product_overview = self._format_product_overview(product_data)
        
        # Format market analysis section
        market_section = self._format_market_section(market_analysis)
        
        # Format optimization section
        optimization_section = self._format_optimization_section(optimization_advice)
        
        # Format executive summary
        executive_summary = self._format_executive_summary(state, product_data)
        
        # Compile final report with unified format
        final_report = f"""# Product Analysis Report

{basic_info}

---

{product_overview}

---

{market_section}

---

{optimization_section}

---

{executive_summary}"""

        return final_report

    def _format_basic_info(self, state: AnalysisState, product_data: dict) -> str:
        """Format basic information section."""
        from datetime import datetime
        
        asin = state.get("asin", "Unknown")
        product_url = state.get("product_url", "")
        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""## 📊 Basic Information

**ASIN:** {asin}  
**Product URL:** {product_url}  
**Analysis Date:** {analysis_date}  
**Report Type:** Complete Analysis"""

    def _format_product_overview(self, product_data: dict) -> str:
        """Format product overview section."""
        # Check if we have synthesized content first
        if product_data.get("synthesized_analysis"):
            product_info = product_data["synthesized_analysis"]
        else:
            # Fallback to existing logic
            product_info = self._extract_product_info_for_report(product_data)
        
        return f"""## 🛍️ Product Overview

{product_info}"""

    def _format_market_section(self, market_analysis: dict) -> str:
        """Format market analysis section."""
        # Check if we have synthesized content first
        if market_analysis.get("synthesized_analysis"):
            market_info = market_analysis["synthesized_analysis"]
        else:
            # Fallback to original analysis
            market_info = market_analysis.get("analysis", "No market analysis available")
        
        return f"""## 📈 Market Analysis

{market_info}"""

    def _format_optimization_section(self, optimization_advice: dict) -> str:
        """Format optimization recommendations section."""
        # Check if we have synthesized content first
        if optimization_advice.get("synthesized_recommendations"):
            optimization_info = optimization_advice["synthesized_recommendations"]
        else:
            # Fallback to original recommendations
            optimization_info = optimization_advice.get("recommendations", "No recommendations available")
        
        return f"""## 🎯 Optimization Recommendations

{optimization_info}"""

    def _format_executive_summary(self, state: AnalysisState, product_data: dict) -> str:
        """Format executive summary section."""
        source = product_data.get("source", "Unknown").replace("_", " ").title()
        iteration_count = state.get("iteration_count", 0)
        
        # Check if report synthesis was performed
        synthesis_performed = state.get("analysis_phase") == "report_synthesis"
        synthesis_note = "Enhanced with AI-powered content synthesis" if synthesis_performed else "Standard multi-agent analysis"
        
        return f"""## 📋 Executive Summary

This comprehensive analysis report is based on real product data, combining product information, market analysis, and optimization recommendations to provide actionable insights for e-commerce optimization.

**Key Highlights:**
• **Data Quality:** {source}  
• **Analysis Depth:** Complete (Product Data + Market Analysis + Optimization)  
• **Processing Iterations:** {iteration_count}  
• **Content Quality:** {synthesis_note}
• **Recommendation Type:** Customized recommendations for specific product and market positioning"""




# Factory function for creating workflow instances
def create_analysis_workflow(llm_api_key: Optional[str] = None) -> ProductAnalysisWorkflow:
    """Create a new product analysis workflow instance.

    Args:
        llm_api_key: Optional OpenAI API key

    Returns:
        ProductAnalysisWorkflow instance
    """
    return ProductAnalysisWorkflow(llm_api_key)
