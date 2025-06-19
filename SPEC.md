建立一個 Amazon 產品分析系統，整合 Agent 架構、全端開發與資料處理能力，為產品優化提供分析與建議。

此測評專為資深全端工程師/AI工程師設計，需要展現前端、後端、AI 應用的綜合技術能力。

- **時間限制**：7天
- **提供資源**：Claude.ai 付費帳號 (Max Plan) & OpenAI API Key
- **技術難度**：Senior Full-Stack AI Engineer Level

**重要：我們相信優秀的工程師應該善用工具來提升效率**

在這次測評中：

https://www.loom.com/share/00c38248b7e245dd8807c14b4213674c

- 鼓勵您使用 [Claude Code](https://www.youtube.com/playlist?list=PLf2m23nhTg1P5BsOHUOXyQz5RhfUSSVUi) 等 Agentic Coding 工具進行開發
- 善用 AI 工具來學習新技術、解決問題是我們評估的重點之一
- 即使遇到不熟悉的技術領域，也能透過 AI 工具快速上手

---

## 核心技術挑戰

### 挑戰1：LangGraph Multi-Agent 架構設計

建立hierarchical multi-agent system展現AI系統架構能力：

```python
# Agent架構設計
class ProductAnalysisSystem:
    supervisor_agent: "協調整體workflow的master agent"
    specialized_agents: {
        "data_collector": "產品與競品數據收集specialist",
        "market_analyzer": "競爭分析與市場定位specialist",
        "optimization_advisor": "產品優化建議specialist"
    }

# 技術重點
- Supervisor-worker coordination pattern
- Agent間狀態傳遞與通訊
- 複雜workflow orchestration
- Error recovery與retry mechanisms
```

### 挑戰2：Full-Stack系統開發

展現完整的前後端整合開發能力：

```python
# Backend Architecture
- FastAPI服務層設計
- PostgreSQL資料建模
- Redis caching策略
- WebSocket real-time communication
- Event-driven architecture patterns

# Frontend Development
- Next.js + TypeScript implementation
- Real-time UI updates
- Agent execution progress visualization
- Responsive design & UX optimization
```

### 挑戰3：資料管道與工具整合

建立robust的資料處理與tool integration系統：

```python
# Data Pipeline
- Amazon產品資料抓取與清理
- 競品自動發現與資料收集
- 資料驗證與正規化
- Rate limiting與anti-detection strategies

# Tool Integration
- Web scraping工具整合
- Data processing utilities
- Error handling與fallback mechanisms
```

---

## 🏗️ 技術規格要求

### Backend Tech Stack

- **Python 3.9+**
- **FastAPI** - API框架與服務層
- **LangGraph** - Multi-agent orchestration (必須使用)
- **PostgreSQL** - 主要資料存儲
- **Redis** - 快取與real-time data
- **Playwright/ Selenium** - 資料抓取工具

### Frontend Tech Stack

- **Next.js 14+** - React框架
- **TypeScript** - 型別安全開發
- **Tailwind CSS** - UI styling
- **WebSocket Client** - 即時通訊

### AI/Data Stack

- **Claude API (Anthropic)** - LLM服務
- **LangChain** - AI工具鏈（選用）
- **Pandas/NumPy** - 資料處理

---

## 📊 系統功能要求

### Core Workflow

```
使用者輸入: Amazon產品URL

系統執行流程:
1. Data Collection Phase
   - 主產品資料抓取（標題、價格、評論、規格）
   - 競品自動發現與資料收集（至少2-3個競品）
   - 評論內容分析

2. AI Analysis Phase
   - Supervisor Agent協調分析workflow
   - Market Analyzer進行競爭定位分析
   - Optimization Advisor生成改進建議

3. Real-time Display
   - **即時展示agent執行進度**
   - 動態更新分析結果
   - 生成完整optimization report

```

### Expected Output

系統應產出包含以下內容的綜合分析報告：

- 產品現況分析（價格、評分、關鍵特徵）
- 競品比較分析（優劣勢對比）
- 市場定位建議
- 產品優化策略（標題、描述、定價等）

---

## 評估重點

我們將從以下面向評估您的表現：

### LangGraph Multi-Agent Architecture

- Supervisor Agent 的設計品質
- Specialized Agents 的實現完整度
- Workflow orchestration 的複雜度處理
- 錯誤處理與系統韌性

### Full-Stack Development

- 後端架構設計的合理性
- 前端實現的完整度與使用者體驗
- Real-time 功能的實現品質

### Data Pipeline & Tool Integration

- 資料收集的穩定性與效率
- 工具整合的完善程度
- 系統的 robustness

### AI 工具運用能力（重要加分項）

- 展現如何有效使用 Claude Code 加速開發
- 運用 AI 解決技術難題的能力
- 學習新技術的效率
- 在不熟悉領域快速上手的能力

---

## 📦 交付要求

### 1. 完整Source Code

專案結構應包含：

- Backend服務（FastAPI + LangGraph agents）
- Frontend應用（Next.js + TypeScript）
- Database schema與migrations
- Docker配置檔案
- 完整的README文檔

### 2. 系統展示要求

- **One-click deployment**: 使用docker-compose啟動完整系統
- **完整workflow demo**: 支援任意Amazon產品URL分析
- **Real-time visualization**: 即時展示multi-agent執行過程
- **Comprehensive output**: 生成完整的產品優化分析報告

### 3. 技術文檔

- **README.md**: 系統安裝、執行與使用指南
- **Architecture Documentation**: 系統設計理念與技術架構說明
- **API Documentation**: 主要endpoint說明

### 4. Demo Video

展示以下內容：

1. 系統概述與技術亮點
2. 完整產品分析流程展示
3. 分析報告與優化建議展示
4. 如何使用 Claude Code/ 其他 Agentic Coding Tool

**我們期待看到您如何結合技術實力與 AI 工具，打造出色的解決方案！** 🚀

基於這個 FastAPI-LangGraph 模板來建立 Amazon 產品分析系統是一個很好的選擇。讓我分析需要做的主要調整和擴展：

## 現有基礎架構優勢

這個模板已經提供了很好的基礎：

- **LangGraph Agent 架構**： graph.py:46-51 提供了完整的代理管理框架
- **狀態管理**： graph.py:15-21 已有基本的狀態定義
- **API 基礎設施**： chatbot.py:35-41 提供了完整的 FastAPI 端點
- **資料庫整合**： database.py:27-33 已有 PostgreSQL 服務

## 需要的主要調整

### 1. 擴展為階層式 Multi-Agent 架構

**新增專門化代理類別**：

- 繼承現有的 `LangGraphAgent` 創建 `SupervisorAgent`、`DataCollectorAgent`、`MarketAnalyzerAgent`、`OptimizationAdvisorAgent`
- 擴展 [5](https://www.notion.so/AI-Test-Case-216b0ea72ead80ce8652e605a308dc2b?pvs=21) 的狀態圖架構來支援代理間協調

**狀態管理擴展**：

- 擴展 `GraphState` 來包含產品分析相關的狀態欄位（產品資料、競品資料、分析結果等）
- 新增代理間通信的狀態管理

### 2. 新增資料收集工具

**Web Scraping 工具**：

- 在現有的工具系統基礎上（ [6](https://www.notion.so/AI-Test-Case-216b0ea72ead80ce8652e605a308dc2b?pvs=21) ）新增 Amazon 產品抓取工具
- 整合 Playwright/Selenium 進行動態內容抓取
- 實現反偵測和速率限制機制

**資料處理管道**：

- 新增產品資料模型和資料庫 schema
- 實現資料清理和正規化邏輯
- 新增競品發現演算法

### 3. 前端開發（全新開發）

**Next.js + TypeScript 前端**：

- 建立全新的前端應用程式
- 實現即時進度顯示（WebSocket 整合）
- 設計產品分析結果的視覺化介面
- 使用 Tailwind CSS 進行響應式設計

### 4. 即時通信系統

**WebSocket 整合**：

- 在現有的 FastAPI 基礎上新增 WebSocket 端點
- 實現代理執行進度的即時推送
- 前端即時更新分析狀態

### 5. 快取和效能優化

**Redis 整合**：

- 新增 Redis 服務用於快取產品資料
- 實現分析結果的快取機制
- 優化重複查詢的效能

## 技術實作重點

### Backend 擴展

1. **新增產品分析相關的 API 端點**
2. **擴展資料庫模型**來儲存產品和分析資料
3. **實現多代理協調邏輯**
4. **新增 WebSocket 支援**用於即時通信

### Frontend 開發

1. **建立 Next.js 專案**（全新）
2. **實現產品 URL 輸入介面**
3. **設計分析進度視覺化**
4. **建立分析報告展示頁面**

### 工具和整合

1. **開發 Amazon 產品抓取工具**
2. **實現競品發現邏輯**
3. **整合資料處理管道**
4. **新增錯誤處理和重試機制**

## 環境配置調整

需要更新現有的環境配置（ [7](https://www.notion.so/AI-Test-Case-216b0ea72ead80ce8652e605a308dc2b?pvs=21) ）來支援：

- Redis 連接設定
- Web scraping 相關配置
- 新的 API Key 管理（Claude API）

## 部署考量

利用現有的 Docker 配置，需要：

1. **新增 Redis 服務**到 docker-compose
2. **更新前端建置流程**
3. **調整環境變數配置**

這個模板提供了很好的基礎架構，主要的工作是擴展代理系統、新增資料收集能力，以及建立前端應用程式。現有的認證、監控、日誌系統都可以直接使用。

## Notes

這個專案的模組化設計讓擴展變得相對容易。建議先實現基本的單一代理產品分析功能，然後逐步擴展為多代理架構。利用現有的 Langfuse 整合可以很好地追蹤多代理的執行流程。

Wiki pages you might want to explore:

- [System Architecture (wassim249/fastapi-langgraph-agent-production-ready-template)](https://www.notion.so/wiki/wassim249/fastapi-langgraph-agent-production-ready-template#1.1)
- [LangGraph Agent (wassim249/fastapi-langgraph-agent-production-ready-template)](https://www.notion.so/wiki/wassim249/fastapi-langgraph-agent-production-ready-template#4)