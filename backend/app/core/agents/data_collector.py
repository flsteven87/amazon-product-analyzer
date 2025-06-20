"""Data Collector Agent for scraping and collecting product data."""

import asyncio
import re
from datetime import datetime
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from sqlmodel import select

from app.core.agents.base import BaseAgent
from app.core.graph.state import AnalysisState
from app.core.tools import ProductScraper, ProductData, AmazonCompetitorExtractor
from app.core.tools.scraper import ScrapingError


class DataCollectorAgent(BaseAgent):
    """Agent responsible for collecting product data and discovering competitors."""

    def __init__(self, llm: ChatOpenAI):
        """Initialize the Data Collector Agent.

        Args:
            llm: The language model instance
        """
        super().__init__(llm, "DataCollectorAgent")
        self.scraper = None  # Will be initialized when needed

    async def _get_scraper(self) -> ProductScraper:
        """Get or create scraper instance."""
        if self.scraper is None:
            self.scraper = ProductScraper()
        return self.scraper

    def execute(self, state: AnalysisState) -> AnalysisState:
        """Execute data collection based on analysis phase."""
        analysis_phase = state.get("analysis_phase", "main_product")

        # Update progress
        self._update_progress(state, 10)

        if analysis_phase == "competitor_collection":
            return asyncio.run(self._collect_competitor_data(state))
        else:
            return self._collect_main_product_data(state)

    def _collect_main_product_data(self, state: AnalysisState) -> AnalysisState:
        """Collect main product data and discover competitors using Amazon recommendations."""
        product_url = state["product_url"]

        self.logger.info(f"DataCollectorAgent starting collection for: {product_url}")

        # Add initial message
        state["messages"].append(HumanMessage(content=f"DataCollector: Starting analysis of {product_url}"))

        # Extract ASIN if not already done
        if not state.get("asin"):
            try:
                state["asin"] = self._extract_asin_from_url(product_url)
            except ValueError as e:
                self.logger.warning(f"Could not extract ASIN: {str(e)}")

        # Update progress
        self._update_progress(state, 20)

        try:
            # Use scrape_with_competitors method for enhanced data collection
            scraping_result = self._run_async_scraping(product_url)

            main_product = scraping_result["main_product"]
            competitor_candidates = scraping_result["competitor_candidates"]
            main_asin = scraping_result["main_asin"]

            # Update progress
            self._update_progress(state, 40)

            if main_product and main_product.is_valid():
                # Perform comprehensive data validation
                quality_score = main_product.get_quality_score()
                validation_issues = main_product.get_validation_issues()
                
                # Log validation results
                self.logger.info(f"Successfully scraped: {main_product.title}")
                self.logger.info(f"Data quality score: {quality_score:.2f}/1.0")
                self.logger.info(f"Discovered {len(competitor_candidates)} competitor candidates")
                
                if validation_issues:
                    self.logger.warning(f"Data validation issues: {len(validation_issues)} found")
                    for issue in validation_issues[:3]:  # Log first 3 issues
                        self.logger.warning(f"  - {issue}")
                    if len(validation_issues) > 3:
                        self.logger.warning(f"  - ... and {len(validation_issues) - 3} more issues")

                # Create structured analysis for LLM
                structured_analysis = self._format_scraped_data_for_llm(main_product, main_asin)

                # Store both raw scraped data and LLM analysis with validation metadata
                state["product_data"] = {
                    "scraped_data": main_product.to_dict(),
                    "structured_analysis": structured_analysis,
                    "source": "scraper",
                    "status": "collected",
                    "main_asin": main_asin,
                    "quality_score": quality_score,
                    "validation_issues": validation_issues,
                    "data_completeness": self._calculate_data_completeness(main_product),
                }

                # Update ASIN in state if found
                if main_asin:
                    state["asin"] = main_asin

                # Store competitor candidates for later processing
                competitor_candidates_data = []
                for candidate in competitor_candidates:
                    competitor_candidates_data.append(
                        {
                            "asin": candidate.asin,
                            "title": candidate.title,
                            "price": candidate.price,
                            "rating": candidate.rating,
                            "review_count": candidate.review_count,
                            "brand": candidate.brand,
                            "url": candidate.url,
                            "source_section": candidate.source_section,
                            "confidence_score": candidate.confidence_score,
                        }
                    )

                state["competitor_candidates"] = competitor_candidates_data

                # Save competitor candidates to database (as they are discovered)
                if main_asin and competitor_candidates_data:
                    self._save_competitors_sync(competitor_candidates_data, main_asin)

                # Update progress
                self._update_progress(state, 50)

                state["messages"].append(
                    AIMessage(
                        content=f"DataCollector: Successfully scraped product data and found {len(competitor_candidates)} competitors\n\n{structured_analysis}"
                    )
                )

                # Save product data to database synchronously
                if state.get("asin"):
                    self._save_product_data_sync(state["product_data"], state["asin"])

            else:
                # Fallback to LLM-based analysis
                self.logger.warning("Scraping failed, falling back to LLM analysis")
                state = self._fallback_to_llm_analysis(state, product_url)

        except Exception as e:
            self.logger.error(f"Error in data collection: {str(e)}")
            # Fallback to LLM-based analysis
            state = self._fallback_to_llm_analysis(state, product_url)

        return state

    def _run_async_scraping(self, product_url: str) -> Dict[str, Any]:
        """Run async scraping in a safe way that handles event loop contexts."""
        try:
            # Check if we're already in an async context
            asyncio.get_running_loop()
            # If there's a running loop, we can't use asyncio.run()
            # Fall back to a simpler sync approach for now
            self.logger.warning("Running in async context, using simplified scraping")

            # For now, return minimal data to trigger LLM fallback
            # TODO: Implement proper async handling in future
            return {"main_product": None, "competitor_candidates": [], "main_asin": None}
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(self._scrape_with_competitors(product_url))

    async def _scrape_with_competitors(self, product_url: str) -> Dict[str, Any]:
        """Scrape product data and discover competitors using scraper's built-in method."""
        scraper = await self._get_scraper()

        try:
            # Use scraper's built-in scrape_with_competitors method like developing version
            async with scraper:
                result = await scraper.scrape_with_competitors(product_url)
            
            # Log detailed results
            main_product = result.get("main_product")
            competitor_candidates = result.get("competitor_candidates", [])
            
            self.logger.info(f"Scraping completed - Product: {main_product.title if main_product else 'None'}")
            self.logger.info(f"Discovered {len(competitor_candidates)} competitor candidates")
            
            if competitor_candidates:
                for i, comp in enumerate(competitor_candidates[:3]):
                    self.logger.info(f"Competitor {i+1}: {comp.asin} - {comp.title[:50]}...")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in scrape_with_competitors: {str(e)}")
            # Return empty result on failure
            return {"main_product": None, "competitor_candidates": [], "main_asin": None}

    async def _collect_competitor_data(self, state: AnalysisState) -> AnalysisState:
        """Collect detailed competitor data."""
        competitor_candidates = state.get("competitor_candidates", [])

        if not competitor_candidates:
            self.logger.info("No competitor candidates to process")
            state["competitor_data"] = []
            return state

        self.logger.info(f"Processing {len(competitor_candidates)} competitor candidates")

        # Update progress
        self._update_progress(state, 60)

        collected_competitors = []
        scraper = await self._get_scraper()

        # Process top competitors (limit to avoid too many requests)
        top_candidates = competitor_candidates[:5]  # Process top 5 competitors

        for i, candidate in enumerate(top_candidates):
            try:
                competitor_url = candidate.get("url")
                if competitor_url:
                    # Scrape competitor product data
                    competitor_product = await scraper.scrape(competitor_url)

                    if competitor_product and competitor_product.is_valid():
                        collected_competitors.append(
                            {
                                "asin": candidate["asin"],
                                "title": competitor_product.title,
                                "price": competitor_product.price,
                                "currency": competitor_product.currency,
                                "rating": competitor_product.rating,
                                "review_count": competitor_product.review_count,
                                "brand": candidate.get("brand"),
                                "source_section": candidate.get("source_section"),
                                "confidence_score": candidate.get("confidence_score", 0.0),
                                "scraped_data": competitor_product.to_dict(),
                            }
                        )

                        self.logger.info(f"Successfully scraped competitor: {competitor_product.title}")

                # Update progress incrementally
                progress = 60 + int((i + 1) / len(top_candidates) * 20)
                self._update_progress(state, progress)

            except Exception as e:
                self.logger.error(f"Error scraping competitor {candidate.get('asin')}: {str(e)}")
                continue

        state["competitor_data"] = collected_competitors

        # Save competitor data to database synchronously
        main_asin = state.get("asin")
        if main_asin and collected_competitors:
            self._save_competitors_sync(collected_competitors, main_asin)

        self.logger.info(f"Collected data for {len(collected_competitors)} competitors")

        state["messages"].append(
            AIMessage(content=f"DataCollector: Collected detailed data for {len(collected_competitors)} competitors")
        )

        return state

    def _format_scraped_data_for_llm(self, product_data: ProductData, asin: str = None) -> str:
        """Format scraped data into a structured analysis for LLM processing."""
        analysis_parts = ["## Product Data Analysis"]

        if asin:
            analysis_parts.append(f"**ASIN:** {asin}")

        analysis_parts.append(f"**Product Title:** {product_data.title}")

        if product_data.price is not None:
            price_str = f"**Price:** {product_data.currency or 'USD'} {product_data.price:.2f}"
            analysis_parts.append(price_str)

        if product_data.rating is not None:
            rating_str = f"**Rating:** {product_data.rating:.1f}/5"
            if product_data.review_count:
                rating_str += f" ({product_data.review_count:,} reviews)"
            analysis_parts.append(rating_str)

        if product_data.availability:
            analysis_parts.append(f"**Availability:** {product_data.availability}")

        if product_data.seller:
            analysis_parts.append(f"**Seller:** {product_data.seller}")

        if product_data.category:
            analysis_parts.append(f"**Category:** {product_data.category}")

        if product_data.features:
            analysis_parts.append("**Key Features:**")
            for feature in product_data.features[:5]:  # Show top 5 features
                analysis_parts.append(f"- {feature}")

        if product_data.images:
            analysis_parts.append(f"**Images Found:** {len(product_data.images)} product images")

        return "\n".join(analysis_parts)

    def _fallback_to_llm_analysis(self, state: AnalysisState, product_url: str) -> AnalysisState:
        """Fallback to LLM-based analysis when scraping fails."""
        self.logger.info("Using LLM fallback for product analysis")

        # Update progress
        self._update_progress(state, 30)

        try:
            prompt = f"""
            Analyze this Amazon product URL and provide a comprehensive product analysis: {product_url}
            
            Please provide:
            1. Product title (inferred from URL if possible)
            2. Likely price range
            3. Product category
            4. Key features (inferred)
            5. Target audience
            6. Market positioning
            
            Format your response as a structured analysis.
            """

            response = self.llm.invoke([HumanMessage(content=prompt)])

            state["product_data"] = {"llm_analysis": response.content, "source": "llm_fallback", "status": "analyzed"}

            # Update progress
            self._update_progress(state, 50)

            state["messages"].append(
                AIMessage(content=f"DataCollector: Generated LLM-based analysis\n\n{response.content}")
            )

        except Exception as e:
            self.logger.error(f"LLM fallback also failed: {str(e)}")
            state["product_data"] = {"error": str(e), "source": "failed", "status": "failed"}
            state["error_message"] = f"Data collection failed: {str(e)}"

        return state

    def _extract_asin_from_url(self, url: str) -> str:
        """Extract ASIN from Amazon product URL."""
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

    async def _save_product_data_to_db(self, product_data: Dict[str, Any], asin: str):
        """Save product data to database."""
        try:
            from app.services.analysis_service import analysis_service

            scraped_data = product_data.get("scraped_data", {})
            await analysis_service.save_product_data(scraped_data, asin)

            self.logger.info(f"Saved product data to database: {asin}")

        except Exception as e:
            self.logger.error(f"Failed to save product data: {str(e)}")

    async def _save_competitors_to_db(self, competitors: List[Dict[str, Any]], main_asin: str):
        """Save competitor data to database."""
        try:
            from app.services.analysis_service import analysis_service

            await analysis_service.save_competitors_data(competitors, main_asin)

            self.logger.info(f"Saved {len(competitors)} competitors to database")

        except Exception as e:
            self.logger.error(f"Failed to save competitor data: {str(e)}")
    
    def _save_product_data_sync(self, product_data: Dict[str, Any], asin: str):
        """Save product data to database synchronously."""
        try:
            from app.models.analysis import Product
            from app.services.database import database_service
            from sqlmodel import Session
            from decimal import Decimal
            
            scraped_data = product_data.get("scraped_data", {})
            
            with Session(database_service.engine) as session:
                # Check if product already exists
                existing = session.exec(
                    select(Product).where(Product.asin == asin)
                ).first()
                
                if existing:
                    # Update existing product
                    for key, value in scraped_data.items():
                        if hasattr(existing, key) and value is not None:
                            setattr(existing, key, value)
                    existing.scraped_at = datetime.utcnow()
                else:
                    # Create new product
                    product = Product(
                        asin=asin,
                        title=scraped_data.get("title", ""),
                        price=Decimal(str(scraped_data.get("price", 0))) if scraped_data.get("price") else None,
                        currency=scraped_data.get("currency", "USD"),
                        rating=Decimal(str(scraped_data.get("rating", 0))) if scraped_data.get("rating") else None,
                        review_count=scraped_data.get("review_count", 0),
                        availability=scraped_data.get("availability"),
                        seller=scraped_data.get("seller"),
                        category=scraped_data.get("category"),
                        features=scraped_data.get("features", []),
                        images=scraped_data.get("images", []),
                        raw_data=scraped_data.get("raw_data", {}),
                    )
                    session.add(product)
                
                session.commit()
                
                if hasattr(self, 'logger'):
                    self.logger.info(f"Saved product data to database: {asin}")
                else:
                    print(f"Saved product data to database: {asin}")
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to save product data: {str(e)}")
            else:
                print(f"Failed to save product data: {str(e)}")
                raise
    
    def _save_competitors_sync(self, competitors: List[Dict[str, Any]], main_asin: str):
        """Save competitor data to database synchronously."""
        try:
            from app.models.analysis import Competitor
            from app.services.database import database_service
            from sqlmodel import Session
            from decimal import Decimal
            
            with Session(database_service.engine) as session:
                saved_count = 0
                
                for comp_data in competitors:
                    try:
                        competitor_asin = comp_data.get("asin")
                        if not competitor_asin:
                            continue
                        
                        # Check if competitor already exists
                        existing = session.exec(
                            select(Competitor).where(
                                Competitor.main_product_asin == main_asin,
                                Competitor.competitor_asin == competitor_asin
                            )
                        ).first()
                        
                        if not existing:
                            competitor = Competitor(
                                main_product_asin=main_asin,
                                competitor_asin=competitor_asin,
                                title=comp_data.get("title", ""),
                                price=Decimal(str(comp_data.get("price", 0))) if comp_data.get("price") else None,
                                rating=Decimal(str(comp_data.get("rating", 0))) if comp_data.get("rating") else None,
                                review_count=comp_data.get("review_count"),
                                brand=comp_data.get("brand"),
                                source_section=comp_data.get("source_section"),
                                confidence_score=Decimal(str(comp_data.get("confidence_score", 0.0))),
                            )
                            session.add(competitor)
                            saved_count += 1
                    
                    except Exception as e:
                        if hasattr(self, 'logger'):
                            self.logger.error(f"Failed to save competitor {comp_data.get('asin')}: {str(e)}")
                        else:
                            print(f"Failed to save competitor {comp_data.get('asin')}: {str(e)}")
                        continue
                
                session.commit()
                
                if hasattr(self, 'logger'):
                    self.logger.info(f"Saved {saved_count} competitors to database")
                else:
                    print(f"Saved {saved_count} competitors to database")
                
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to save competitor data: {str(e)}")
            else:
                print(f"Failed to save competitor data: {str(e)}")
                raise
    
    def _calculate_data_completeness(self, product_data) -> Dict[str, Any]:
        """Calculate detailed data completeness metrics."""
        # Define expected fields and their importance
        critical_fields = ["url", "title", "price"]
        important_fields = ["rating", "review_count", "availability", "currency"]
        optional_fields = ["seller", "category", "features", "images"]
        
        completeness = {
            "critical_fields": {
                "total": len(critical_fields),
                "present": 0,
                "missing": [],
                "score": 0.0
            },
            "important_fields": {
                "total": len(important_fields),
                "present": 0,
                "missing": [],
                "score": 0.0
            },
            "optional_fields": {
                "total": len(optional_fields),
                "present": 0,
                "missing": [],
                "score": 0.0
            },
            "overall_score": 0.0,
            "total_fields": len(critical_fields) + len(important_fields) + len(optional_fields),
            "present_fields": 0
        }
        
        # Check critical fields
        for field in critical_fields:
            value = getattr(product_data, field, None)
            if value is not None and value != "" and value != []:
                completeness["critical_fields"]["present"] += 1
                completeness["present_fields"] += 1
            else:
                completeness["critical_fields"]["missing"].append(field)
        
        # Check important fields  
        for field in important_fields:
            value = getattr(product_data, field, None)
            if value is not None and value != "" and value != []:
                completeness["important_fields"]["present"] += 1
                completeness["present_fields"] += 1
            else:
                completeness["important_fields"]["missing"].append(field)
                
        # Check optional fields
        for field in optional_fields:
            value = getattr(product_data, field, None)
            if value is not None and value != "" and value != []:
                completeness["optional_fields"]["present"] += 1
                completeness["present_fields"] += 1
            else:
                completeness["optional_fields"]["missing"].append(field)
        
        # Calculate scores
        completeness["critical_fields"]["score"] = completeness["critical_fields"]["present"] / completeness["critical_fields"]["total"]
        completeness["important_fields"]["score"] = completeness["important_fields"]["present"] / completeness["important_fields"]["total"]
        completeness["optional_fields"]["score"] = completeness["optional_fields"]["present"] / completeness["optional_fields"]["total"]
        
        # Overall score with weighted importance
        # Critical: 60%, Important: 30%, Optional: 10%
        completeness["overall_score"] = (
            completeness["critical_fields"]["score"] * 0.6 +
            completeness["important_fields"]["score"] * 0.3 +
            completeness["optional_fields"]["score"] * 0.1
        )
        
        return completeness
