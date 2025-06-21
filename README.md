# 🚀 Amazon Product Analyzer - Multi-Agent Intelligence System

A sophisticated product analysis system built with **LangGraph's hierarchical multi-agent architecture**, demonstrating exceptional engineering in 3 days. The system orchestrates specialized AI agents to provide comprehensive Amazon product analysis with real-time updates.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-latest-orange.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)

## 🎯 Core Value Proposition

Transform any Amazon product URL into actionable insights through:
- **Automated Competitor Discovery**: Finds and analyzes relevant competing products
- **Market Positioning Analysis**: Understands product's place in the market
- **Optimization Recommendations**: AI-driven suggestions for improvement
- **Real-time Progress Tracking**: WebSocket-powered live updates

## 🏗️ Architectural Highlights

- **Hierarchical Multi-Agent System**: Supervisor orchestrates specialized agents for complex analysis
- **Production-Ready Design**: Comprehensive error handling, logging, and monitoring
- **Real-time Communication**: Native WebSocket implementation with graceful fallbacks
- **Intelligent Data Collection**: Multi-strategy scraping with LLM fallback
- **Beautiful Reports**: Notion-style formatting for professional presentation

[→ Read detailed architecture documentation](./ARCHITECTURE.md)

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (with `uv` package manager)
- Node.js 18+
- OpenAI API Key

### One-Command Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/amazon-product-analyzer.git
cd amazon-product-analyzer

# Configure environment
cp backend/.env.example backend/.env
# Edit .env with your OpenAI API key

# Start everything
docker-compose up -d

# Access the application
open http://localhost:3000
```

### Manual Setup (Development)

```bash
# Backend setup
cd backend
uv sync
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv run uvicorn app.main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

## 📊 System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js UI    │────▶│  FastAPI Backend │────▶│   PostgreSQL    │
│   (React 19)    │     │   + LangGraph    │     │    Database     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                        │
         │                        ▼
         │              ┌─────────────────┐
         └─────────────▶│   Multi-Agent   │
            WebSocket   │   Orchestrator  │
                        └─────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌───────────────┐      ┌──────────────┐      ┌──────────────────┐
│ Data Collector│      │Market Analyzer│      │Optimization Advisor│
└───────────────┘      └──────────────┘      └──────────────────┘
```

## 🎯 Core Features Implemented

### 1. Intelligent Multi-Agent System
- **Supervisor Agent**: Orchestrates the entire analysis workflow
- **Data Collector Agent**: Sophisticated web scraping with fallback strategies
- **Market Analyzer Agent**: Competitive intelligence and positioning
- **Optimization Advisor Agent**: Strategic recommendations
- **Report Synthesizer**: Beautiful, actionable reports

### 2. Real-time Analysis Pipeline
- WebSocket-based progress updates
- Graceful degradation to polling
- Visual progress tracking
- Live agent status updates

### 3. Comprehensive Data Collection
- Multi-strategy scraping approach
- Automatic competitor discovery
- LLM-powered fallback for blocked content
- Intelligent data validation and normalization

### 4. Professional Reporting
- Notion-style formatted reports
- Competitive analysis tables
- Actionable recommendations
- Executive summaries

## 📸 System Demo

### Analysis Dashboard
Real-time progress tracking with agent status visibility:
- WebSocket connection indicator
- Progress bar with percentage
- Agent execution stages
- Live status updates

### Sample Analysis Report
Professional Notion-style analysis includes:
- Product overview with key metrics
- Competitive landscape analysis
- Market positioning insights
- Optimization recommendations
- Executive summary

## 🔧 Technical Stack

### Backend
- **FastAPI**: High-performance async API framework
- **LangGraph**: State-of-the-art agent orchestration
- **PostgreSQL**: Reliable data persistence
- **SQLModel**: Type-safe ORM
- **BeautifulSoup/Playwright**: Web scraping tools

### Frontend  
- **Next.js 14**: Modern React framework
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Native WebSocket**: Real-time communication

### AI/ML
- **OpenAI GPT-4**: Advanced language understanding
- **LangChain**: AI application framework
- **Custom Agents**: Specialized analysis capabilities

## 📚 Documentation

- [**Architecture Overview**](./ARCHITECTURE.md) - System design and technical decisions
- [**Agent Deep Dive**](./DATA_COLLECTOR_DEEP_DIVE.md) - Detailed look at the Data Collector Agent
- [**API Documentation**](./API_DOCUMENTATION.md) - Complete API reference


## 🧪 Testing the System

### Sample Product URLs
```
https://www.amazon.com/dp/B0CW6BLQKL
https://www.amazon.com/dp/B0014BYHJE
```

### Expected Flow
1. Enter Amazon product URL
2. Watch real-time agent progress
3. View comprehensive analysis report
4. Export or share results

## 🔍 Project Structure

```
amazon-product-analyzer/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI endpoints
│   │   ├── core/         # Core business logic
│   │   │   ├── agents/   # LangGraph agents
│   │   │   ├── graph/    # Workflow orchestration
│   │   │   └── tools/    # Scraping & processing
│   │   ├── models/       # Database models
│   │   └── services/     # Service layer
│   └── scripts/          # Utility scripts
├── frontend/
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   ├── services/         # API clients
│   └── types/            # TypeScript types
├── *.md                  # Documentation files
└── docker-compose.yml    # Containerization
```

## 🚦 Performance Metrics

- **Analysis Speed**: 2-4 minutes for complete analysis
- **Success Rate**: High success rate with LLM fallback strategies
- **WebSocket Updates**: Real-time progress tracking
- **Data Quality**: Comprehensive validation and scoring

## 🛡️ Production Considerations

- Comprehensive error handling and recovery
- Rate limiting and respectful scraping
- Structured logging with correlation IDs
- Health check endpoints
- Graceful shutdown handling

## 🔮 Future Enhancements

- Redis caching layer for improved performance
- Distributed agent processing
- Historical price tracking
- Review sentiment analysis
- Export to multiple formats

## 🔑 API Key Configuration

Add your OpenAI API key to the `.env` file:
```env
LLM_API_KEY=your_openai_api_key_here
POSTGRES_URL=postgresql://user:password@localhost:5432/dbname
```

## 📊 Development Commands

```bash
# Backend development
cd backend
uv run uvicorn app.main:app --reload

# Frontend development
cd frontend
npm run dev

# Run with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Run tests
cd backend && uv run pytest
```

## 📝 License

This project is licensed under the MIT License.

---

*For questions or discussions about the architecture and implementation choices, please refer to the [detailed documentation](./ARCHITECTURE.md).*