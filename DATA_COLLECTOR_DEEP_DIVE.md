# 🕷️ Data Collector Agent - Deep Implementation Dive

## Why This Agent?

The Data Collector Agent is our most sophisticated piece of engineering. It's the agent that does the heavy lifting when it comes to gathering real-world data from Amazon's complex web pages. This deep dive shows how we handle all the messy, unpredictable challenges that come with web scraping at scale.

## What Makes This Agent Special

Looking at our `data_collector.py`, this agent has to deal with:
- Amazon's constantly changing page layouts
- Anti-bot detection systems
- Network failures and timeouts
- Different product page structures
- Finding competitors automatically
- Quality control for scraped data

And it has to do all this while playing nicely with LangGraph's synchronous execution model.

## The Multi-Phase Architecture

### Phase-Based Execution

The agent is smart about what it does based on where we are in the analysis:

```python
def execute(self, state: AnalysisState) -> AnalysisState:
    analysis_phase = state.get("analysis_phase", "main_product")
    
    if analysis_phase == "competitor_collection":
        return asyncio.run(self._collect_competitor_data(state))
    elif analysis_phase == "competitor_retry":
        return self._retry_competitor_discovery(state)
    else:
        return self._collect_main_product_data(state)
```

This design lets us handle different scenarios:
- **Main Product Phase**: Get the core product data
- **Competitor Collection**: Focus on finding similar products
- **Retry Phase**: When competitor discovery fails the first time

## The Smart Scraping Strategy

### Multi-Layer Fallback System

Here's where things get interesting. Our scraping doesn't just try once and give up:

```python
def _collect_main_product_data(self, state: AnalysisState) -> AnalysisState:
    try:
        # Primary strategy: Full scraping with competitor discovery
        scraping_result = self._run_async_scraping(product_url)
        
        main_product = scraping_result["main_product"]
        competitor_candidates = scraping_result["competitor_candidates"]
        
        if main_product and main_product.is_valid():
            # Success! Process the data...
        else:
            # Fallback to LLM analysis
            state = self._fallback_to_llm_analysis(state, product_url)
            
    except Exception as e:
        # Ultimate fallback
        state = self._fallback_to_llm_analysis(state, product_url)
```

When scraping fails (and it does fail quite often), we don't just crash. We fall back to having the LLM analyze what it can infer from the URL and its training data.

### Async/Sync Bridge Magic

One of the trickiest parts was handling LangGraph's synchronous execution while needing async scraping:

```python
def _run_async_scraping(self, product_url: str) -> Dict[str, Any]:
    """Run async scraping in a safe way that handles event loop contexts."""
    try:
        # Check if we're already in an async context
        loop = asyncio.get_running_loop()
        # If there's a running loop, create a task instead of using asyncio.run
        self.logger.info("Running in async context, creating task for scraping")
        
        # Create a task and run it synchronously
        task = loop.create_task(self._scrape_with_competitors(product_url))
        
        # Wait for the task to complete
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._run_task_sync, task)
            return future.result(timeout=30)  # 30 second timeout
            
    except RuntimeError:
        # No running loop, safe to use asyncio.run
        self.logger.info("No running loop, using asyncio.run for scraping")
        return asyncio.run(self._scrape_with_competitors(product_url))
```

This was actually pretty tricky to get right. You can't just call `asyncio.run()` when you're already inside an async context, so we had to detect the current state and handle it appropriately.

## Data Quality Assessment

### Real-Time Quality Scoring

We don't just scrape data and hope it's good. We actively measure and score the quality using the `ProductData` class methods:

```python
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
```

### Quality Score Calculation

The `get_quality_score()` method in `ProductData` uses a sophisticated scoring system:

```python
def get_quality_score(self) -> float:
    """Calculate data quality score (0.0-1.0) based on completeness and validity."""
    score = 0.0
    
    # Basic requirements (0.4 points)
    if self.url and self.title:
        score += 0.4
    
    # Pricing information (0.2 points)
    if self.price is not None and self.price > 0:
        score += 0.15
    if self.currency:
        score += 0.05
        
    # Rating and reviews (0.2 points)
    if self.rating is not None and 0 <= self.rating <= 5:
        score += 0.1
    if self.review_count is not None and self.review_count > 0:
        score += 0.1
```

### Data Completeness Tracking

We also track how complete our scraped data is with detailed metrics:

```python
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
```

The `_calculate_data_completeness()` method categorizes fields by importance:

```python
def _calculate_data_completeness(self, product_data) -> Dict[str, Any]:
    # Define expected fields and their importance
    critical_fields = ["url", "title", "price"]
    important_fields = ["rating", "review_count", "availability", "currency"]
    optional_fields = ["seller", "category", "features", "images"]
```

## Competitor Discovery Algorithm

### Smart Competitor Detection

Finding competitors isn't just random - we use Amazon's own recommendation systems through our scraper:

```python
# Store competitor candidates for later processing
competitor_candidates_data = []
for candidate in competitor_candidates:
    competitor_candidates_data.append({
        "asin": candidate.asin,
        "title": candidate.title,
        "price": candidate.price,
        "rating": candidate.rating,
        "review_count": candidate.review_count,
        "brand": candidate.brand,
        "url": candidate.url,
        "source_section": candidate.source_section,  # Where we found it
        "confidence_score": candidate.confidence_score,  # How sure we are
    })
```

The `source_section` tells us where we found each competitor (like "customers also viewed" or "compare with similar items"), and the `confidence_score` helps us rank how relevant each competitor actually is.

### Retry Logic for Competitor Discovery

Sometimes Amazon doesn't show competitor recommendations on the first try. We built retry logic:

```python
def _retry_competitor_discovery(self, state: AnalysisState) -> AnalysisState:
    product_url = state["product_url"]
    retry_count = state.get("competitor_retry_count", 0)
    
    self.logger.info(f"Retrying competitor discovery (attempt {retry_count}) for: {product_url}")
    
    try:
        # Use enhanced scraping with more aggressive competitor detection
        scraping_result = self._run_async_scraping(product_url)
        
        competitor_candidates = scraping_result.get("competitor_candidates", [])
        
        if competitor_candidates:
            # Success! Update state with found competitors
            # ... process the data
        else:
            # Still no luck, but that's okay
            self.logger.warning(f"Retry {retry_count} failed - no competitors found")
```

### Detailed Competitor Collection

When we have competitor candidates, we can collect detailed data about them:

```python
async def _collect_competitor_data(self, state: AnalysisState) -> AnalysisState:
    competitor_candidates = state.get("competitor_candidates", [])
    
    # Process top competitors (limit to avoid too many requests)
    top_candidates = competitor_candidates[:5]  # Process top 5 competitors
    
    for i, candidate in enumerate(top_candidates):
        try:
            competitor_url = candidate.get("url")
            if competitor_url:
                # Scrape competitor product data
                competitor_product = await scraper.scrape(competitor_url)
                
                if competitor_product and competitor_product.is_valid():
                    collected_competitors.append({
                        "asin": candidate["asin"],
                        "title": competitor_product.title,
                        "price": competitor_product.price,
                        # ... more fields
                    })
```

## Database Integration Challenges

### Sync Database Operations in Async Context

Since LangGraph agents run synchronously but we're in a broader async application, database operations needed special handling:

```python
# Save product data to database synchronously
if state.get("asin"):
    self._save_product_data_sync(state["product_data"], state["asin"])

# Save competitor candidates to database (as they are discovered)
if main_asin and competitor_candidates_data:
    self._save_competitors_sync(competitor_candidates_data, main_asin)
```

The actual `_save_product_data_sync` method handles Supabase PostgreSQL integration:

```python
def _save_product_data_sync(self, product_data: Dict[str, Any], asin: str):
    """Save product data to database synchronously."""
    try:
        from app.models.analysis import Product
        from app.services.database import database_service
        from sqlmodel import Session
        
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
            else:
                # Create new product
                product = Product(asin=asin, title=scraped_data.get("title", ""), ...)
```

## Progress Tracking Integration

### Real-Time User Feedback

The agent provides detailed progress updates throughout its execution:

```python
# Update progress
self._update_progress(state, 10)  # Starting
# ... do some work
self._update_progress(state, 40)  # Main scraping done
# ... process competitors
self._update_progress(state, 50)  # Ready for next agent
```

These updates flow through our WebSocket system to give users real-time feedback about what's happening.

## Error Handling Philosophy

### Graceful Degradation

The key insight with the Data Collector is that partial success is often better than total failure:

```python
except Exception as e:
    self.logger.error(f"Error in data collection: {str(e)}")
    # Fallback to LLM-based analysis
    state = self._fallback_to_llm_analysis(state, product_url)
```

Even when scraping completely fails, we can still provide valuable analysis using the LLM's knowledge about Amazon products and market trends.

### LLM Fallback Implementation

When everything else fails, we get creative:

```python
def _fallback_to_llm_analysis(self, state: AnalysisState, product_url: str) -> AnalysisState:
    self.logger.info("Using LLM fallback for product analysis")
    
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
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        
        state["product_data"] = {
            "llm_analysis": response.content, 
            "source": "llm_fallback", 
            "status": "analyzed"
        }
```

This ensures the analysis can continue even when we can't scrape anything.

## Structured Data Processing

### LLM-Ready Formatting

We format scraped data for downstream LLM processing:

```python
def _format_scraped_data_for_llm(self, product_data: ProductData, asin: str = None) -> str:
    """Format scraped data into a structured analysis for LLM processing."""
    analysis_parts = ["## Product Data Analysis"]
    
    if asin:
        analysis_parts.append(f"**ASIN:** {asin}")
    
    analysis_parts.append(f"**Product Title:** {product_data.title}")
    
    if product_data.price is not None:
        price_str = f"**Price:** {product_data.currency or 'USD'} {product_data.price:.2f}"
        analysis_parts.append(price_str)
    
    if product_data.features:
        analysis_parts.append("**Key Features:**")
        for feature in product_data.features[:5]:  # Show top 5 features
            analysis_parts.append(f"- {feature}")
    
    return "\n".join(analysis_parts)
```

## Memory and Resource Management

The agent is careful about resource usage:
- Lazy initialization of the scraper (`self.scraper = None` until needed)
- Proper cleanup of async event loops
- Database sessions are opened and closed quickly
- Limits competitor processing to top 5 to avoid excessive requests

## Why This Shows Depth

This agent demonstrates:
- **Complex Error Handling**: Multiple fallback strategies with graceful degradation
- **Architecture Integration**: Careful handling of async/sync boundaries  
- **Real-World Resilience**: Dealing with the unpredictable nature of web scraping
- **Quality Engineering**: Data validation, quality scoring, and completeness tracking
- **User Experience**: Real-time progress updates and meaningful error messages
- **Database Integration**: Proper handling of data persistence in async/sync contexts

The Data Collector Agent isn't just about scraping web pages - it's about building a robust, production-ready system that handles real-world complexity while maintaining clean, maintainable code.