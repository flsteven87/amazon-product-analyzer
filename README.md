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
- PostgreSQL + Redis for data storage
- Playwright for web scraping
- Pydantic for data validation

**Frontend:**
- Next.js 14+ with TypeScript
- Tailwind CSS for styling
- WebSocket for real-time communication

**AI/Data:**
- OpenAI API & Claude API
- LangChain for AI toolchain
- Pandas/NumPy for data processing

## 📂 Project Structure

```
amazon-product-analyzer/
├── backend/                    # FastAPI 後端服務
│   ├── app/
│   │   ├── agents/            # LangGraph Agents
│   │   ├── api/               # FastAPI Routes
│   │   ├── core/              # 核心服務 (config, database, redis)
│   │   ├── models/            # SQLAlchemy Models
│   │   ├── services/          # Business Logic
│   │   ├── utils/             # 工具函數
│   │   └── main.py           # FastAPI App Entry
│   ├── alembic/              # Database Migrations
│   ├── tests/                # Pytest Tests
│   ├── pyproject.toml        # uv 專案配置
│   └── uv.lock              # uv 依賴鎖定檔案
├── frontend/                 # Next.js 前端應用 (待開發)
├── PLANNING.md              # 專案架構規劃
├── SPEC.md                  # 專案規格說明
├── TASK.md                  # 任務追蹤
└── README.md               # 此文檔
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend)
- PostgreSQL
- Redis
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
   # Copy environment template
   cp .env.example .env
   
   # Edit environment variables
   # Add your OpenAI API key, database URLs, etc.
   ```

4. **Database setup**
   ```bash
   # Run database migrations
   uv run alembic upgrade head
   ```

5. **Start the backend server**
   ```bash
   # Development mode
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or using the main script
   uv run python app/main.py
   ```

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
uv run flake8 app/

# Testing
uv run pytest
```

### Project Management

- **Planning**: See `PLANNING.md` for architectural decisions
- **Tasks**: See `TASK.md` for development progress
- **Specifications**: See `SPEC.md` for detailed requirements

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/e2e/
```

## 📊 Core Features

### 1. Product Analysis Workflow
- Amazon product data extraction
- Competitor discovery and analysis
- Review sentiment analysis
- Market positioning insights

### 2. Multi-Agent Coordination
- Supervisor agent orchestration
- Specialized agent coordination
- Real-time progress tracking
- Error handling and recovery

### 3. Real-time Visualization
- WebSocket-based progress updates
- Dynamic result streaming
- Interactive dashboard
- Comprehensive reporting

## 🔑 API Key Configuration

You'll need API keys for:
- **OpenAI API**: For GPT models
- **Claude API (Anthropic)**: For Claude models

Add these to your `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here
```

## 🐳 Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up --build

# Development mode
docker-compose -f docker-compose.dev.yml up
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
- Project documentation in `PLANNING.md`
- Task tracking in `TASK.md`
- Technical specifications in `SPEC.md`

---

**Built with ❤️ using LangGraph, FastAPI, and Next.js** 