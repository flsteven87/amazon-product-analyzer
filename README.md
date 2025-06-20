# 🚀 Amazon Product Analyzer

AI-powered Amazon product analysis and optimization platform using LangGraph Multi-Agent architecture.

## 📋 Project Overview

Amazon Product Analyzer 是一個整合 LangGraph Multi-Agent 架構的全端應用，用於分析 Amazon 產品並提供優化建議。系統採用 hierarchical multi-agent design pattern，支援即時 workflow visualization 與 comprehensive product analysis。

## 🏗️ Architecture

### Multi-Agent System Design

```
ProductAnalysisSystem (Supervisor Agent)
├── DataCollectorAgent     # 產品與競品數據收集 specialist
├── MarketAnalyzerAgent    # 競爭分析與市場定位 specialist
└── OptimizationAdvisorAgent # 產品優化建議 specialist
```

### Technology Stack

**Backend:**
- Python 3.9+ with FastAPI
- LangGraph for Multi-Agent orchestration
- Supabase PostgreSQL for data storage
- BeautifulSoup & HTTPX for web scraping
- Pydantic for data validation
- Streamlit for testing interface

**Frontend:**
- Next.js 14+ with TypeScript
- Tailwind CSS for styling
- React Query for state management
- Socket.io for real-time communication

**AI/Data:**
- OpenAI API (GPT models)
- LangChain for AI toolchain
- Pandas for data processing

## 📂 Project Structure

```
amazon-product-analyzer/
├── backend/                    # FastAPI 後端服務
│   ├── app/
│   │   ├── api/               # FastAPI Routes
│   │   │   └── v1/           # API v1 endpoints
│   │   │       ├── api.py    # Main API router
│   │   │       └── product_analysis.py # Product analysis endpoints
│   │   ├── core/              # 核心服務配置
│   │   │   ├── config.py     # Application configuration
│   │   │   ├── logging.py    # Structured logging setup
│   │   │   ├── agents/       # Multi-Agent implementation
│   │   │   │   ├── base.py   # Base agent class
│   │   │   │   ├── supervisor.py # Supervisor agent
│   │   │   │   ├── data_collector.py # Data collection agent
│   │   │   │   ├── market_analyzer.py # Market analysis agent
│   │   │   │   └── optimization_advisor.py # Optimization agent
│   │   │   ├── graph/        # LangGraph workflow
│   │   │   │   ├── state.py  # Graph state definition
│   │   │   │   └── workflow.py # Main workflow implementation
│   │   │   └── tools/        # Agent tools
│   │   │       ├── scraper.py # Web scraping tools
│   │   │       ├── product_parser.py # Product data parser
│   │   │       └── competitor_extractor.py # Competitor discovery
│   │   ├── models/           # SQLModel/SQLAlchemy Models
│   │   │   ├── base.py       # Base model classes
│   │   │   └── analysis.py   # Analysis models
│   │   ├── schemas/          # Pydantic schemas
│   │   │   └── analysis.py   # Analysis request/response schemas
│   │   ├── services/         # Business logic services
│   │   │   ├── database.py   # Database service layer
│   │   │   └── analysis_service.py # Analysis orchestration
│   │   ├── utils/            # 工具函數
│   │   │   └── __init__.py   # Utility functions
│   │   ├── cli.py           # Command line interface
│   │   └── main.py          # FastAPI App Entry
│   ├── streamlit_app.py     # Streamlit testing interface
│   ├── evals/               # LLM evaluation framework
│   │   ├── evaluator.py     # Main evaluation engine
│   │   ├── metrics/         # Evaluation metrics
│   │   └── schemas.py       # Evaluation schemas
│   ├── grafana/             # Grafana dashboards
│   ├── prometheus/          # Prometheus configuration
│   ├── scripts/             # Deployment and utility scripts
│   ├── logs/                # Application logs
│   ├── Dockerfile           # Container configuration
│   ├── docker-compose.yml   # Multi-container setup
│   ├── Makefile             # Development commands
│   ├── pyproject.toml       # uv 專案配置
│   └── uv.lock             # uv 依賴鎖定檔案
├── frontend/                # Next.js 前端應用
│   ├── app/                 # Next.js App Router
│   │   ├── layout.tsx       # Root layout
│   │   ├── page.tsx         # Homepage
│   │   └── analysis/        # Analysis pages
│   ├── components/          # React components
│   │   ├── analysis/        # Analysis-specific components
│   │   ├── layout/          # Layout components
│   │   └── ui/             # UI components
│   ├── lib/                 # Utilities and providers
│   ├── services/            # API services
│   ├── types/               # TypeScript types
│   ├── package.json         # Node dependencies
│   └── tsconfig.json        # TypeScript configuration
└── README.md               # 此文檔
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend)
- PostgreSQL
- uv (Python package manager)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd amazon-product-analyzer
   ```

2. **Backend development**
   ```bash
   cd backend
   
   # Install dependencies with uv
   uv sync
   
   # Activate virtual environment
   source .venv/bin/activate
   
   # Or run with uv directly
   uv run python app/main.py
   ```

3. **Environment configuration**
   ```bash
   # Create environment file
   cp .env.example .env
   
   # Edit environment variables
   # Add your OpenAI API key, database URLs, etc.
   ```

4. **Database setup**
   ```bash
   # Set up PostgreSQL database
   # Update POSTGRES_URL in .env file
   
   # Run database migrations if needed
   # uv run alembic upgrade head
   ```

5. **Start the backend server**
   ```bash
   # Development mode
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or using the main script
   uv run python app/main.py
   ```

### Frontend Setup

1. **Frontend development**
   ```bash
   cd frontend
   
   # Install dependencies
   npm install
   
   # Start development server
   npm run dev
   ```

2. **Access the applications**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **Streamlit Testing Interface**: `uv run streamlit run streamlit_app.py`

### API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔧 Development

### Code Quality Tools

```bash
# Code formatting
uv run black app/
uv run isort app/

# Type checking
uv run mypy app/

# Linting
uv run ruff check app/

# Testing
uv run pytest
```

### Using the CLI

```bash
# Run analysis via CLI
uv run python app/cli.py analyze "https://amazon.com/dp/PRODUCT_ID"

# Check system status
uv run python app/cli.py status
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
```

## 📊 Core Features

### 1. Product Analysis Workflow
- Amazon product data extraction using web scraping
- Competitor discovery and analysis
- Market positioning insights
- Product optimization recommendations

### 2. Multi-Agent Coordination
- Supervisor agent orchestration
- Specialized agent coordination (Data Collection, Market Analysis, Optimization)
- Real-time progress tracking
- Error handling and recovery

### 3. Multiple Interfaces
- **Next.js Frontend**: Modern web interface for production use
- **Streamlit Interface**: Testing and development interface
- **FastAPI Backend**: RESTful API for all operations
- **CLI Interface**: Command-line tool for batch operations

### 4. Real-time Features
- WebSocket-based progress updates
- Dynamic result streaming
- Task status monitoring
- Comprehensive reporting

## 🔑 API Key Configuration

You'll need API keys for:
- **OpenAI API**: For GPT models

Add these to your `.env` file:
```env
LLM_API_KEY=your_openai_api_key_here
POSTGRES_URL=postgresql://user:password@localhost:5432/dbname
```

## 🐳 Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up --build

# Development mode
docker-compose -f docker-compose.dev.yml up
```

## 📊 Monitoring & Observability

- **Grafana Dashboards**: Performance and usage metrics
- **Prometheus**: Metrics collection
- **Structured Logging**: JSON-formatted logs with context
- **Health Checks**: System status monitoring

## 🧩 Development Prototype

The `developing/simple_multi_agent/` directory contains a simplified prototype implementation that demonstrates the core multi-agent concepts. This can be used for:
- Testing new agent logic
- Understanding the workflow
- Rapid prototyping

```bash
cd developing/simple_multi_agent
uv run python run_analysis.py
```

## 📝 License

This project is licensed under the MIT License.

## 👥 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📞 Support

For questions and support, please refer to:
- API documentation at `/docs` endpoint
- Code examples in `developing/` directory
- Test files for usage patterns

---

**Built with ❤️ using LangGraph, FastAPI, and Next.js** 