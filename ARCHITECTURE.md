# 🏗️ System Architecture - Amazon Product Analyzer

## Overview

We built this Amazon Product Analyzer in 3 days using a **LangGraph multi-agent system** as the core architecture. This project demonstrates how thoughtful technical choices and focused feature design can create a practical analysis tool within tight time constraints.

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js UI    │────▶│  FastAPI Backend │────▶│ Supabase        │
│   (React 19)    │     │   + LangGraph    │     │ PostgreSQL      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                        │
         │                        ▼
         │              ┌─────────────────┐
         └─────────────▶│   Multi-Agent   │
           WebSocket    │   Orchestrator  │
                        └─────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌───────────────┐      ┌──────────────┐      ┌──────────────────┐
│ Data Collector│      │Market Analyzer│      │Optimization Advisor│
└───────────────┘      └──────────────┘      └──────────────────┘
```

## Multi-Agent Design

### State Management Architecture

Based on `backend/app/core/graph/state.py`, our system uses a shared state model:

```python
class AnalysisState(TypedDict):
    # Database integration
    task_id: Optional[UUID]
    user_id: Optional[UUID]
    
    # Product information
    product_url: str
    asin: Optional[str]
    
    # Inter-agent communication
    messages: Annotated[List[AnyMessage], add_messages]
    next_agent: str
    
    # Agent outputs
    product_data: Dict[str, Any]
    market_analysis: Dict[str, Any]
    optimization_advice: Dict[str, Any]
    
    # Competitor data
    competitor_candidates: List[Dict[str, Any]]
    competitor_data: List[Dict[str, Any]]
    
    # Analysis control
    analysis_phase: str  # "main_product", "competitor_collection", "analysis"
    iteration_count: int
    max_iterations: int
    
    # Progress tracking
    progress: int  # 0-100
    status: str   # "pending", "processing", "completed", "failed"
    final_analysis: str
```

### Agent Architecture

We implemented 4 specialized agents, each handling different aspects of the analysis:

1. **Supervisor Agent** (`supervisor.py`)
   - Orchestrates the entire workflow
   - Decides which agent should execute next
   - **Compiles all analysis results into the final report**
   - Controls iteration limits and termination

2. **Data Collector Agent** (`data_collector.py`)
   - Scrapes Amazon product data
   - Discovers competitor products automatically
   - Falls back to LLM analysis when scraping fails

3. **Market Analyzer Agent** (`market_analyzer.py`)
   - Analyzes competitive landscape
   - Performs market positioning analysis
   - Generates market insights

4. **Optimization Advisor Agent** (`optimization_advisor.py`)
   - Creates product optimization recommendations
   - Analyzes pricing strategies
   - Provides actionable improvement suggestions

## Technical Decisions

### Why LangGraph?

We chose LangGraph for multi-agent orchestration because it provided exactly what we needed:
- Built-in state management that works perfectly with our `AnalysisState` design
- Conditional routing that lets the Supervisor make smart decisions about what to do next
- Clean message passing between agents
- Error recovery and retry mechanisms out of the box

### WebSocket Evolution

We initially tried Socket.IO but ran into FastAPI compatibility issues (403 errors). Switching to native WebSocket turned out to be cleaner:
- Seamless integration with FastAPI
- Simpler code with fewer dependencies
- We implemented reconnection and task subscriptions ourselves, giving us more control

### Database Choice

We use Supabase PostgreSQL with SQLModel:
- Stores analysis task progress
- Persists product data
- Logs agent execution details
- Manages real-time state updates

### Frontend Architecture

Next.js 14 with TypeScript gives us:
- App Router structure (`app/layout.tsx`, `app/page.tsx`)
- Real-time updates via WebSocket with polling fallback
- Beautiful Notion-style report rendering (`components/ui/notion-report.tsx`)
- Type-safe API client (`services/api.ts`)

## How the Workflow Works

The analysis follows a clear flow based on our `workflow.py` implementation:

```
1. Supervisor Agent starts
   ↓ (decides to collect data first)
2. Data Collector Agent runs
   ↓ (scrapes product data & finds competitors)
3. Back to Supervisor Agent  
   ↓ (decides to analyze market)
4. Market Analyzer Agent runs
   ↓ (analyzes competitive landscape)
5. Back to Supervisor Agent
   ↓ (decides to generate recommendations)
6. Optimization Advisor Agent runs
   ↓ (creates optimization suggestions)
7. Back to Supervisor Agent
   ↓ (decides analysis is complete)
8. Supervisor compiles the final report
```

### How State Management Works

- **Starting Point**: The Supervisor agent kicks everything off
- **Decision Making**: Supervisor looks at the `next_agent` field to decide what to do next
- **Completion**: When the Supervisor decides everything is done, it compiles the final report
- **Error Handling**: If something goes wrong, we have fallback strategies and retry logic

## Real-time Updates

### WebSocket System

We built a simple but effective WebSocket system in `websocket_simple.py`:

```python
class SimpleWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.task_subscribers: Dict[str, Set[str]] = {}
    
    async def emit_progress_update(self, task_id: str, progress: int, status: str):
        # Broadcasts progress to subscribed clients
```

The frontend connects via `websocket_native.ts` and subscribes to specific analysis tasks. If WebSocket fails, it gracefully falls back to polling the API.

## API Structure

Our main API endpoints in `product_analysis.py`:

- `POST /api/v1/analysis/analyze` - Kicks off a new analysis
- `GET /api/v1/analysis/{task_id}/status` - Checks progress  
- `GET /api/v1/analysis/{task_id}/report` - Gets the final report
- `WS /api/v1/websocket/ws` - Real-time progress updates

## How Data Collection Works

The Data Collector Agent is pretty smart about gathering information:

1. **Primary Strategy**: Uses BeautifulSoup to scrape product pages
2. **Competitor Discovery**: Finds similar products from Amazon's recommendations
3. **Backup Plan**: When scraping fails, we use LLM to infer product details
4. **Quality Control**: Validates and scores the data we collect

## What We Built vs What We Didn't

### ✅ What We Actually Built
- Complete multi-agent system with LangGraph orchestration
- Real-time WebSocket communication with polling fallback
- Full-stack Next.js + FastAPI application
- Smart scraping with LLM fallbacks when things go wrong
- Beautiful Notion-style reports that look professional
- Supabase PostgreSQL for reliable data storage
- Solid error handling throughout the system

### ❌ What We Left Out (Time Constraints)
- Redis caching layer (would improve performance)
- Database migrations with Alembic (using SQLModel auto-create instead)
- Comprehensive test suite (focused on core functionality)
- User authentication system
- Advanced monitoring and analytics

## System Reliability

### Error Handling
We put a lot of thought into what happens when things go wrong:
- Agents fail gracefully and try fallback strategies
- WebSocket automatically reconnects if the connection drops
- Scraping failures trigger LLM-based analysis
- Comprehensive logging helps us understand issues

### Current Limitations
- Single FastAPI instance (fine for demo, would need load balancing for scale)
- WebSocket state is in-memory (would need Redis for multiple servers)
- No horizontal scaling yet (but the architecture supports it)

## Key Takeaways

This project shows what you can accomplish in 3 days with the right approach:
- **Smart Tool Choice**: LangGraph saved us weeks of custom orchestration code
- **Focus on Core Value**: We built what matters most for product analysis
- **Production Mindset**: Even in 3 days, we thought about error handling and reliability
- **Good Architecture**: The multi-agent design makes the system easy to understand and extend

The LangGraph multi-agent approach gives us a solid foundation that can handle complex analysis tasks while keeping the code clean and maintainable.