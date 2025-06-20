"""Market Analyzer Agent for performing market and competitive analysis."""

from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from app.core.agents.base import BaseAgent
from app.core.graph.state import AnalysisState


class MarketAnalyzerAgent(BaseAgent):
    """Agent responsible for market analysis and competitive positioning."""

    def __init__(self, llm: ChatOpenAI):
        """Initialize the Market Analyzer Agent.

        Args:
            llm: The language model instance
        """
        super().__init__(llm, "MarketAnalyzerAgent")

    def execute(self, state: AnalysisState) -> AnalysisState:
        """Execute market analysis based on collected data and competitors."""
        analysis_phase = state.get("analysis_phase", "basic_analysis")

        # Update progress
        self._update_progress(state, 60)

        if analysis_phase == "competitive_analysis":
            return self._analyze_with_competitors(state)
        else:
            return self._basic_market_analysis(state)

    def _basic_market_analysis(self, state: AnalysisState) -> AnalysisState:
        """Perform basic market analysis without competitor data."""
        product_data = state.get("product_data", {})

        self.logger.info("MarketAnalyzerAgent starting basic analysis")
        self.logger.debug(f"Product data keys: {list(product_data.keys())}")

        # Get the appropriate product data based on source
        product_info = self._extract_product_info(product_data)

        if not product_info:
            self.logger.warning("No product data available for market analysis")
            product_info = "No product data available for analysis"

        # Update progress
        self._update_progress(state, 70)

        # Create a prompt for basic market analysis
        prompt = f"""You are a market analysis expert. Based on the following product data:
        
        {product_info}
        
        Please provide:
        1. Market positioning analysis
        2. Competitive landscape overview
        3. Price competitiveness assessment
        4. Target audience identification
        5. Market trends relevant to this product
        
        Provide your analysis in a structured format. Focus on actionable insights based on the actual product data provided."""

        # Get response from LLM
        response = self.llm.invoke([HumanMessage(content=prompt)])

        # Update state
        state["messages"].append(
            HumanMessage(content="MarketAnalyzer: Analyzing market position based on collected data")
        )
        state["messages"].append(AIMessage(content=response.content))

        # Store analysis
        state["market_analysis"] = {"analysis": response.content, "status": "completed"}

        # Update progress
        self._update_progress(state, 80)

        self.logger.info("MarketAnalyzerAgent completed basic analysis")
        return state

    def _analyze_with_competitors(self, state: AnalysisState) -> AnalysisState:
        """Perform comprehensive market analysis with competitor data."""
        product_data = state.get("product_data", {})

        # Get competitor data - try detailed first, fallback to candidates
        competitor_analysis_data = self._get_competitor_data_for_analysis(state)

        self.logger.info(
            f"MarketAnalyzerAgent starting competitive analysis with {len(competitor_analysis_data)} competitors"
        )

        # Get product information
        product_info = self._extract_product_info(product_data)

        if not product_info:
            self.logger.warning("No product data available for competitive analysis")
            product_info = "No product data available for analysis"

        # Update progress
        self._update_progress(state, 70)

        # Format competitor information
        competitor_info = self._format_competitor_analysis_data(competitor_analysis_data)

        # Create comprehensive analysis prompt
        prompt = f"""You are a market analysis expert. Based on the following product and competitor data, provide a comprehensive competitive analysis.

IMPORTANT: When referencing products in your analysis, always include their ASIN (Amazon Standard Identification Number) for tracking and verification purposes.

## Main Product:
{product_info}

## Competitor Data:
{competitor_info}

Please provide a detailed analysis including:

### 1. Competitive Positioning
- How does the main product compare to competitors in terms of features, pricing, and quality?
- What is the main product's unique value proposition?
- IMPORTANT: When referencing competitors, include their ASIN for tracking purposes

### 2. Price Analysis
- Price comparison with competitors
- Pricing strategy assessment (premium, competitive, budget)
- Price-value relationship analysis

### 3. Market Position
- Market segment analysis
- Target audience comparison
- Brand positioning vs competitors

### 4. Competitive Advantages & Disadvantages
- Main product's strengths vs competitors
- Areas where competitors outperform the main product
- Market gaps and opportunities

### 5. Market Trends & Insights
- Industry trends affecting this product category
- Consumer preferences based on competitor offerings
- Market size and growth potential

### 6. Strategic Recommendations
- Key competitive threats to monitor
- Market positioning recommendations
- Differentiation strategies

Provide specific, data-driven insights based on the actual product and competitor information provided."""

        # Get response from LLM
        response = self.llm.invoke([HumanMessage(content=prompt)])

        # Update state
        state["messages"].append(
            HumanMessage(
                content=f"MarketAnalyzer: Performing competitive analysis with {len(competitor_analysis_data)} competitors"
            )
        )
        state["messages"].append(AIMessage(content=response.content))

        # Store comprehensive analysis
        state["market_analysis"] = {
            "analysis": response.content,
            "status": "completed",
            "analysis_type": "competitive",
            "competitor_count": len(competitor_analysis_data),
            "includes_competitor_data": True,
        }

        # Update progress
        self._update_progress(state, 80)

        self.logger.info("MarketAnalyzerAgent completed competitive analysis")
        return state

    def _get_competitor_data_for_analysis(self, state: AnalysisState) -> List[Dict[str, Any]]:
        """Get competitor data for analysis - detailed data first, then candidates."""
        # Try detailed competitor data first
        competitor_data = state.get("competitor_data", [])
        if competitor_data:
            self.logger.info(f"Using {len(competitor_data)} detailed competitor data for analysis")
            return competitor_data

        # Fallback to competitor candidates
        competitor_candidates = state.get("competitor_candidates", [])
        if competitor_candidates:
            self.logger.info(f"Using {len(competitor_candidates)} competitor candidates for analysis")
            return self._convert_candidates_to_analysis_format(competitor_candidates)

        self.logger.warning("No competitor data available for analysis")
        return []

    def _convert_candidates_to_analysis_format(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert competitor candidates to analysis format."""
        analysis_data = []
        for candidate in candidates:
            # Convert candidate data to analysis format
            analysis_item = {
                "asin": candidate.get("asin", ""),
                "title": candidate.get("title", ""),
                "price": candidate.get("price"),
                "rating": candidate.get("rating"),
                "review_count": candidate.get("review_count"),
                "brand": candidate.get("brand", ""),
                "source_section": candidate.get("source_section", ""),
                "confidence_score": candidate.get("confidence_score", 0.0),
                "data_source": "candidate",  # Mark as candidate data
            }
            analysis_data.append(analysis_item)

        return analysis_data

    def _format_competitor_analysis_data(self, competitor_analysis_data: List[Dict[str, Any]]) -> str:
        """Format competitor analysis data for LLM analysis."""
        if not competitor_analysis_data:
            return "No competitor data available."

        formatted_competitors = []

        for i, competitor in enumerate(competitor_analysis_data, 1):
            competitor_info = f"### Competitor {i}"

            # Handle both detailed data and candidate data
            if competitor.get("data_source") == "candidate":
                # Format candidate data
                competitor_info += f"\n**ASIN:** {competitor.get('asin', 'N/A')}"
                competitor_info += f"\n**Title:** {competitor.get('title', 'N/A')}"

                if competitor.get("price"):
                    competitor_info += f"\n**Price:** ${competitor['price']:.2f}"

                if competitor.get("rating"):
                    competitor_info += f"\n**Rating:** {competitor['rating']:.1f}/5"

                if competitor.get("review_count"):
                    competitor_info += f"\n**Reviews:** {competitor['review_count']:,}"

                if competitor.get("brand"):
                    competitor_info += f"\n**Brand:** {competitor['brand']}"

                competitor_info += f"\n**Discovery Source:** {competitor.get('source_section', 'N/A')}"
                competitor_info += f"\n**Relevance Score:** {competitor.get('confidence_score', 0.0):.2f}/1.0"
                competitor_info += "\n**Data Type:** Amazon Recommendation (Basic Info)"

            else:
                # Handle detailed scraped data
                if competitor.get("structured_analysis"):
                    competitor_info += f"\n{competitor['structured_analysis']}"
                elif competitor.get("scraped_data"):
                    competitor_asin = competitor.get("asin", "N/A")
                    competitor_info += f"\n{self._format_scraped_data(competitor['scraped_data'], competitor_asin)}"

                if competitor.get("discovery_source"):
                    competitor_info += f"\n**Discovery Source:** {competitor['discovery_source']}"

                if competitor.get("confidence_score"):
                    competitor_info += f"\n**Relevance Score:** {competitor['confidence_score']:.2f}/1.0"

                competitor_info += "\n**Data Type:** Detailed Scraping"

            formatted_competitors.append(competitor_info)

        return "\n\n".join(formatted_competitors)

    def _extract_product_info(self, product_data: dict) -> str:
        """Extract product information from different data sources."""
        # Try scraped data first (preferred)
        if product_data.get("source") == "scraper" and "structured_analysis" in product_data:
            self.logger.info("Using scraped product data for market analysis")
            return product_data["structured_analysis"]

        # Try scraped data directly
        if "scraped_data" in product_data:
            self.logger.info("Using raw scraped data for market analysis")
            scraped_data = product_data["scraped_data"]
            asin = product_data.get("main_asin")
            return self._format_scraped_data(scraped_data, asin)

        # Fallback to LLM analysis
        if "llm_analysis" in product_data:
            self.logger.info("Using LLM fallback data for market analysis")
            return product_data["llm_analysis"]

        # Legacy format
        if "raw_analysis" in product_data:
            self.logger.info("Using legacy raw analysis for market analysis")
            return product_data["raw_analysis"]

        return ""

    def _format_scraped_data(self, scraped_data: dict, asin: str = None) -> str:
        """Format scraped data for LLM consumption."""
        parts = ["## Product Information from Scraping"]

        if asin:
            parts.append(f"**ASIN:** {asin}")

        if scraped_data.get("title"):
            parts.append(f"**Title:** {scraped_data['title']}")

        if scraped_data.get("price") is not None:
            price_str = "**Price:** "
            if scraped_data.get("currency"):
                price_str += f"{scraped_data['currency']} {scraped_data['price']:.2f}"
            else:
                price_str += f"${scraped_data['price']:.2f}"
            parts.append(price_str)

        if scraped_data.get("rating") is not None:
            rating_str = f"**Rating:** {scraped_data['rating']:.1f}/5"
            if scraped_data.get("review_count"):
                rating_str += f" ({scraped_data['review_count']:,} reviews)"
            parts.append(rating_str)

        if scraped_data.get("availability"):
            parts.append(f"**Availability:** {scraped_data['availability']}")

        if scraped_data.get("seller"):
            parts.append(f"**Seller:** {scraped_data['seller']}")

        if scraped_data.get("category"):
            parts.append(f"**Category:** {scraped_data['category']}")

        if scraped_data.get("features"):
            parts.append("**Key Features:**")
            for feature in scraped_data["features"][:5]:
                parts.append(f"- {feature}")

        return "\n".join(parts)
