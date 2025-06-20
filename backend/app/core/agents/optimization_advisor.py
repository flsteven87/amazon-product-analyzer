"""Optimization Advisor Agent for providing actionable e-commerce recommendations."""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from app.core.agents.base import BaseAgent
from app.core.graph.state import AnalysisState


class OptimizationAdvisorAgent(BaseAgent):
    """Agent responsible for providing optimization recommendations."""

    def __init__(self, llm: ChatOpenAI):
        """Initialize the Optimization Advisor Agent.

        Args:
            llm: The language model instance
        """
        super().__init__(llm, "OptimizationAdvisorAgent")

    def execute(self, state: AnalysisState) -> AnalysisState:
        """Provide optimization advice based on all collected data."""
        product_data = state.get("product_data", {})
        market_analysis = state.get("market_analysis", {})

        self.logger.info("OptimizationAdvisorAgent starting recommendation generation")
        self.logger.debug(f"Product data keys: {list(product_data.keys())}")
        self.logger.debug(f"Market analysis keys: {list(market_analysis.keys())}")

        # Update progress
        self._update_progress(state, 85)

        # Get product information using the same logic as MarketAnalyzer
        product_info = self._extract_product_info(product_data)
        market_info = market_analysis.get("analysis", "No market analysis available")

        if not product_info:
            self.logger.warning("No product data available for optimization advice")
            product_info = "No product data available"

        # Create a prompt for optimization advice
        prompt = f"""You are an e-commerce optimization expert. Based on the following data:
        
        Product Data:
        {product_info}
        
        Market Analysis:
        {market_info}
        
        Please provide specific, actionable recommendations for:
        1. Title optimization suggestions (based on the actual product title)
        2. Pricing strategy recommendations (considering current price and market position)
        3. Description improvement ideas (enhancing the existing features)
        4. Keyword optimization suggestions (relevant to this specific product)
        5. Competitive positioning advice (based on the market analysis)
        
        Provide actionable recommendations with expected impact. Be specific and reference the actual product data where applicable."""

        # Get response from LLM
        response = self.llm.invoke([HumanMessage(content=prompt)])

        # Update state
        state["messages"].append(
            HumanMessage(content="OptimizationAdvisor: Generating recommendations based on product and market data")
        )
        state["messages"].append(AIMessage(content=response.content))

        # Store advice
        state["optimization_advice"] = {"recommendations": response.content, "status": "completed"}

        # Update progress
        self._update_progress(state, 95)

        self.logger.info("OptimizationAdvisorAgent completed recommendation generation")
        return state

    def _extract_product_info(self, product_data: dict) -> str:
        """Extract product information from different data sources."""
        # Try scraped data first (preferred)
        if product_data.get("source") == "scraper" and "structured_analysis" in product_data:
            self.logger.info("Using scraped product data for optimization advice")
            return product_data["structured_analysis"]

        # Try scraped data directly
        if "scraped_data" in product_data:
            self.logger.info("Using raw scraped data for optimization advice")
            scraped_data = product_data["scraped_data"]
            asin = product_data.get("main_asin")
            return self._format_scraped_data(scraped_data, asin)

        # Fallback to LLM analysis
        if "llm_analysis" in product_data:
            self.logger.info("Using LLM fallback data for optimization advice")
            return product_data["llm_analysis"]

        # Legacy format
        if "raw_analysis" in product_data:
            self.logger.info("Using legacy raw analysis for optimization advice")
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
