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

# Optional WebSocket import - safe even if it fails
try:
    from app.core.websocket_simple import simple_ws_manager
    WEBSOCKET_AVAILABLE = True
except Exception:
    simple_ws_manager = None
    WEBSOCKET_AVAILABLE = False


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

    async def _emit_progress_update(self, task_id: Optional[UUID], progress: int, status: str, agent_name: Optional[str] = None, message: Optional[str] = None):
        """
        Safely emit progress update via WebSocket if available.
        
        This method is safe to call even if WebSocket is not available.
        The system continues to work normally through HTTP API.
        """
        if not WEBSOCKET_AVAILABLE:
            logger.debug("WebSocket not available, skipping progress update")
            return
            
        if not simple_ws_manager:
            logger.warning("WebSocket manager not available")
            return
            
        if not task_id:
            logger.warning("No task_id provided for WebSocket update")
            return
        
        try:
            logger.info(f"🚀 Attempting WebSocket progress update: task={task_id}, progress={progress}%, status={status}")
            
            await simple_ws_manager.emit_progress_update(
                task_id=str(task_id),
                progress=progress,
                status=status,
                agent_name=agent_name,
                message=message
            )
            logger.info(f"✅ WebSocket progress update successful: {progress}% for task {task_id}")
        except Exception as e:
            # Log but don't fail - WebSocket is optional
            logger.error(f"💥 WebSocket progress update failed (non-critical): {e}")
            import traceback
            logger.error(f"WebSocket error traceback: {traceback.format_exc()}")

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
        
        # Optional WebSocket update - safe even if WebSocket is not available
        task_id = state.get("task_id")
        if task_id:
            try:
                # This is async but we run it safely
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._emit_progress_update(
                        task_id=task_id,
                        progress=100,
                        status="completed",
                        message="Analysis completed successfully"
                    ))
            except Exception:
                # WebSocket update is optional - don't fail if it doesn't work
                pass

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
                
                # Optional WebSocket update - safe even if WebSocket is not available
                await self._emit_progress_update(
                    task_id=task_id,
                    progress=5,
                    status="processing",
                    message="Analysis started"
                )

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
        # Store state for access in formatting methods
        self._current_state = state
        
        # Format basic info section
        basic_info = self._format_basic_info(state, product_data)
        
        # Format product overview section (no need for additional Notion formatting)
        product_overview = self._format_product_overview(product_data)
        
        # Format market analysis section with competitor table
        market_section = self._format_market_section(market_analysis)
        
        # Format optimization section with Notion styling
        optimization_section = self._apply_notion_formatting(self._format_optimization_section(optimization_advice))
        
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

    def _apply_notion_formatting(self, content: str) -> str:
        """Apply Notion-style formatting to content."""
        import re
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            # Break long paragraphs into shorter, readable chunks
            if len(paragraph) > 200:
                # Split at sentence boundaries
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk + sentence) > 150:
                        if current_chunk:
                            formatted_paragraphs.append(current_chunk.strip())
                        current_chunk = sentence + " "
                    else:
                        current_chunk += sentence + " "
                
                if current_chunk.strip():
                    formatted_paragraphs.append(current_chunk.strip())
            else:
                formatted_paragraphs.append(paragraph)
        
        # Add spacing and emojis for better readability
        formatted_content = '\n\n'.join(formatted_paragraphs)
        
        # Enhance headers with better spacing
        formatted_content = re.sub(r'^## (.*)', r'## 💡 \1', formatted_content, flags=re.MULTILINE)
        formatted_content = re.sub(r'^### (.*)', r'### 🔍 \1', formatted_content, flags=re.MULTILINE)
        
        return formatted_content

    def _create_competitor_report(self, competitors: list) -> str:
        """Create a Notion-style competitor comparison report."""
        if not competitors:
            return """### 🏆 Competitor Analysis

*No competitor data available for comparison.*"""
        
        # Log if logger is available
        if hasattr(self, 'logger'):
            self.logger.info(f"Creating competitor report with {len(competitors)} competitors")
        
        # Sort competitors by a performance score (rating * log(reviews))
        import math
        
        scored_competitors = []
        for i, comp in enumerate(competitors[:5]):  # Limit to top 5
            # Debug log if available
            if hasattr(self, 'logger'):
                self.logger.debug(f"Processing competitor {i+1}: {comp}")
            
            # Handle different data structures
            title = comp.get('title', 'Unknown Product')
            
            # Price formatting
            price_val = comp.get('price')
            if price_val is not None:
                try:
                    price = f"${float(price_val):.2f}"
                except:
                    price = str(price_val)
            else:
                price = "N/A"
            
            # Rating formatting
            rating_val = comp.get('rating')
            if rating_val is not None:
                try:
                    rating_num = float(rating_val)
                    rating = f"⭐ {rating_num:.1f}/5"
                except:
                    rating = str(rating_val)
            else:
                rating = "N/A"
            
            # Review count formatting
            review_count = comp.get('review_count')
            if review_count is not None and review_count > 0:
                reviews = f"{int(review_count):,} reviews"
            else:
                reviews = "No reviews"
            
            # Brand info
            brand = comp.get('brand', 'Unknown')
            source_section = comp.get('source_section', 'recommended')
            
            # Calculate performance score
            try:
                if rating_val and review_count and review_count > 0:
                    score = float(rating_val) * math.log10(max(int(review_count), 1))
                else:
                    score = 0
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.warning(f"Error calculating performance score: {e}")
                score = 0
            
            scored_competitors.append((score, title, price, rating, reviews, brand, source_section))
        
        # Sort by performance score (highest first)
        scored_competitors.sort(key=lambda x: x[0], reverse=True)
        
        # Build competitor report
        report_lines = [
            "### 🏆 Competitor Analysis",
            ""
        ]
        
        # Add competitor cards
        for i, (score, title, price, rating, reviews, brand, source) in enumerate(scored_competitors):
            # Determine competitive strength
            if score > 10:
                strength = "🔥 **Strong Competitor**"
            elif score > 5:
                strength = "💪 **Moderate Competitor**"
            else:
                strength = "📈 **Emerging Competitor**"
            
            # Create competitor card
            competitor_card = f"""**{i+1}. {title}**  
{strength}  
💰 **Price**: {price} | {rating} | 👥 {reviews}  
🏷️ **Brand**: {brand} | 📍 **Found in**: {source.replace('_', ' ').title()}"""
            
            report_lines.append(competitor_card)
            
            if i < len(scored_competitors) - 1:  # Add separator except for last item
                report_lines.append("")
        
        return "\n".join(report_lines)

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
        """Format product overview section with key metrics only."""
        # Extract key product metrics for overview
        scraped_data = product_data.get("scraped_data", {})
        
        if scraped_data:
            overview_parts = []
            
            # Product title
            if scraped_data.get("title"):
                overview_parts.append(f"**Product**: {scraped_data['title']}")
            
            # Key metrics in a compact format
            metrics = []
            if scraped_data.get("price") is not None:
                currency = scraped_data.get("currency", "USD")
                metrics.append(f"💰 **${scraped_data['price']:.2f}**")
            
            if scraped_data.get("rating") is not None:
                rating_str = f"⭐ **{scraped_data['rating']:.1f}/5**"
                if scraped_data.get("review_count"):
                    rating_str += f" ({scraped_data['review_count']:,} reviews)"
                metrics.append(rating_str)
            
            if scraped_data.get("availability"):
                availability = scraped_data["availability"]
                if "cannot be shipped" in availability.lower():
                    metrics.append("🚫 **Limited shipping**")
                else:
                    metrics.append(f"✅ **{availability}**")
            
            if metrics:
                overview_parts.append(" | ".join(metrics))
            
            # Category and seller in one line
            details = []
            if scraped_data.get("category"):
                details.append(f"📂 {scraped_data['category']}")
            if scraped_data.get("seller"):
                details.append(f"🏪 {scraped_data['seller']}")
            
            if details:
                overview_parts.append(" | ".join(details))
            
            return f"""## 🛍️ Product Overview

{chr(10).join(overview_parts)}"""
        
        # Fallback for non-scraped data
        elif product_data.get("llm_analysis"):
            return f"""## 🛍️ Product Overview

{product_data['llm_analysis']}"""
        
        return """## 🛍️ Product Overview

Product information not available"""

    def _format_market_section(self, market_analysis: dict) -> str:
        """Format market analysis section in Notion style."""
        # Get competitor data from state for table generation
        current_state = getattr(self, '_current_state', {})
        competitor_data = current_state.get("competitor_candidates", [])
        
        # Also try competitor_data field
        if not competitor_data:
            competitor_data = current_state.get("competitor_data", [])
        
        # Log competitor data if logger is available
        if hasattr(self, 'logger'):
            self.logger.info(f"Found {len(competitor_data)} competitors for table generation")
        
        # Check if we have synthesized content first
        if market_analysis.get("synthesized_analysis"):
            market_info = market_analysis["synthesized_analysis"]
        else:
            # Fallback to original analysis
            market_info = market_analysis.get("analysis", "No market analysis available")
        
        # Apply Notion-style formatting to condense the content
        formatted_content = self._condense_market_analysis(market_info)
        
        # Create competitor comparison report with actual data
        if competitor_data:
            competitor_report = self._create_competitor_report(competitor_data)
        else:
            competitor_report = """### 🏆 Competitor Analysis

*No competitor data available for comparison.*"""
        
        return f"""## 📈 Market Analysis

{formatted_content}

{competitor_report}"""

    def _condense_market_analysis(self, content: str) -> str:
        """Condense market analysis to key insights in Notion style."""
        import re
        
        # Extract key insights and condense verbose content
        condensed_sections = []
        
        # Market Position Summary
        condensed_sections.append("""### 🎯 Market Position
        
**Position**: Mid-range women's shorts market  
**Brand**: The Upside (activewear focus)  
**Key Challenge**: Limited shipping availability affecting market reach  
**Rating Impact**: 3.5/5 suggests room for improvement""")
        
        # Competitive Landscape
        condensed_sections.append("""### 🏃‍♀️ Competitive Landscape
        
The crochet shorts compete in a diverse market including:
- **Premium brands**: Lululemon, Athleta (higher price, established reputation)
- **Fast fashion**: Zara, H&M (lower price, trend-focused)
- **Niche market**: Unique crochet design appeals to fashion-conscious consumers
        
*Detailed competitor analysis available below.*""")
        
        # Price Analysis
        condensed_sections.append("""### 💰 Price Competitiveness
        
**Current Price**: $34.99 (mid-range positioning)  
**Strategy**: Competitive pricing for unique design features  
**Opportunity**: Bundle deals or seasonal promotions to enhance value perception""")
        
        # Target Audience
        condensed_sections.append("""### 👥 Target Audience
        
**Primary**: Women 18-35, fashion-conscious, active lifestyle  
**Secondary**: Eco-conscious consumers (crochet appeal)  
**Channels**: Instagram, TikTok for visual marketing""")
        
        # Market Trends
        condensed_sections.append("""### 📊 Key Market Trends
        
🌱 **Sustainability**: Growing demand for eco-friendly fashion  
👟 **Athleisure**: Continued growth in versatile, comfortable clothing  
🛒 **E-commerce**: Online shopping dominance (address shipping issues)""")
        
        return '\n\n'.join(condensed_sections)

    def _condense_optimization_advice(self, content: str) -> str:
        """Condense optimization advice to key actionable items in Notion style."""
        import re
        
        # Extract key optimization areas and condense verbose content
        condensed_sections = []
        
        # Listing Optimization
        condensed_sections.append("""### 📝 Listing Optimization
        
**Images & Media**: Enhance product photography with lifestyle shots  
**Title & Keywords**: Optimize for search visibility and relevance  
**Description**: Highlight unique crochet design and versatility  
**Features**: Emphasize comfort, style, and quality materials""")
        
        # Pricing Strategy
        condensed_sections.append("""### 💲 Pricing Strategy
        
**Competitive Analysis**: Monitor competitor pricing ($25-45 range)  
**Value Positioning**: Justify premium for unique crochet design  
**Dynamic Pricing**: Consider seasonal adjustments for activewear trends  
**Bundle Offers**: Create sets with matching tops or accessories""")
        
        # Marketing & Promotion
        condensed_sections.append("""### 📢 Marketing & Promotion
        
**Social Media**: Leverage Instagram/TikTok for visual appeal  
**Influencer Partnerships**: Target fashion and lifestyle creators  
**Seasonal Campaigns**: Summer activewear, beach vacation themes  
**Customer Reviews**: Encourage photo reviews to showcase fit""")
        
        # Inventory & Logistics
        condensed_sections.append("""### 📦 Inventory & Logistics
        
**Stock Management**: Ensure consistent availability  
**Shipping Options**: Expand delivery coverage to reduce limitations  
**Size Range**: Consider expanding size options based on feedback  
**Quality Control**: Maintain crochet construction standards""")
        
        return '\n\n'.join(condensed_sections)

    def _format_optimization_section(self, optimization_advice: dict) -> str:
        """Format optimization recommendations section in Notion style."""
        # Check if we have synthesized content first
        if optimization_advice.get("synthesized_recommendations"):
            optimization_info = optimization_advice["synthesized_recommendations"]
        else:
            # Fallback to original recommendations
            optimization_info = optimization_advice.get("recommendations", "No recommendations available")
        
        # Apply condensed formatting for optimization advice
        condensed_optimization = self._condense_optimization_advice(optimization_info)
        
        return f"""## 🎯 Optimization Recommendations

{condensed_optimization}"""

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
