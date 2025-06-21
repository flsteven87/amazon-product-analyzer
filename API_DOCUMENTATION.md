# 🔌 API Documentation

## What You Get

Our FastAPI-based system gives you clean REST endpoints for managing product analysis and real-time WebSocket updates. This documentation covers what's actually implemented and working.

## Base URL

```
http://localhost:8000/api/v1
```

## Core Analysis Endpoints

### Start Product Analysis

**POST** `/analyze`

The main endpoint that kicks off our multi-agent analysis workflow.

```json
// Request
{
  "product_url": "https://amazon.com/dp/B08N5WRWNW"
}

// Response (201 Created)
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": null,
  "product_url": "https://amazon.com/dp/B08N5WRWNW",
  "asin": "B08N5WRWNW",
  "status": "pending",
  "progress": 0,
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "completed_at": null
}
```

**What happens:** Creates an analysis task and immediately starts our LangGraph workflow in the background. The Data Collector, Market Analyzer, and Optimization Advisor agents begin their work.

### Check Analysis Progress

**GET** `/tasks/{task_id}/status`

Get real-time status updates on your analysis.

```json
// Response
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "product_url": "https://amazon.com/dp/B08N5WRWNW",
  "status": "processing",
  "progress": 65,
  "current_agent": "market_analyzer",
  "error_message": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:12Z",
  "completed_at": null
}
```

**Status values:** `pending`, `processing`, `completed`, `failed`
**Progress:** 0-100 percentage
**Current agent:** Shows which agent is currently working

### Get Complete Analysis Results

**GET** `/tasks/{task_id}`

Retrieve the full analysis with all agent outputs and scraped data.

```json
// Response
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "asin": "B08N5WRWNW",
  "status": "completed",
  "progress": 100,
  "product": {
    "asin": "B08N5WRWNW",
    "title": "Echo Dot (4th Gen) | Smart speaker with Alexa",
    "price": 49.99,
    "currency": "USD",
    "rating": 4.7,
    "review_count": 12453,
    "availability": "In Stock",
    "features": ["Voice control", "Smart home hub", "Music streaming"],
    "scraped_at": "2024-01-15T10:31:45Z"
  },
  "competitors": [
    {
      "competitor_asin": "B07XJ8C8F5",
      "title": "Google Nest Mini (2nd Generation)",
      "price": 39.99,
      "rating": 4.5,
      "review_count": 8421,
      "confidence_score": 0.92
    }
  ],
  "reports": [
    {
      "report_type": "market_analysis",
      "content": "## Competitive Analysis\\n\\nThe Echo Dot competes in the smart speaker market...",
      "created_at": "2024-01-15T10:32:15Z"
    },
    {
      "report_type": "optimization_recommendations", 
      "content": "## Optimization Strategy\\n\\nBased on competitive analysis...",
      "created_at": "2024-01-15T10:32:30Z"
    }
  ]
}
```

### List All Analysis Tasks

**GET** `/tasks`

Browse all your analysis tasks with pagination and filtering.

**Query Parameters:**
- `limit` (1-100, default 50): How many tasks to return
- `offset` (default 0): Skip this many tasks (for pagination)
- `status_filter`: Filter by status (`pending`, `processing`, `completed`, `failed`)

```json
// Response
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "asin": "B08N5WRWNW",
    "product_title": "Echo Dot (4th Gen)",
    "status": "completed",
    "progress": 100,
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:32:30Z"
  }
]
```

### Delete Analysis Task

**DELETE** `/tasks/{task_id}`

Remove an analysis task and all its related data from the database.

```
// Response: 204 No Content (success)
// 404 Not Found (task doesn't exist)
```

## Batch Operations

### Analyze Multiple Products

**POST** `/batch`

Submit up to 10 product URLs for simultaneous analysis.

```json
// Request
{
  "product_urls": [
    "https://amazon.com/dp/B08N5WRWNW",
    "https://amazon.com/dp/B07XJ8C8F5",
    "https://amazon.com/dp/B0842P1FQD"
  ]
}

// Response (201 Created)
{
  "batch_id": "456e7890-e89b-12d3-a456-426614174001",
  "task_ids": [
    "123e4567-e89b-12d3-a456-426614174000",
    "234e5678-e89b-12d3-a456-426614174001",
    "345e6789-e89b-12d3-a456-426614174002"
  ],
  "total_tasks": 3,
  "created_at": "2024-01-15T10:35:00Z"
}
```

Each product gets its own analysis task running independently.

## System Information

### Analysis Statistics

**GET** `/stats`

Get overview statistics about your analysis system.

```json
// Response
{
  "total_tasks": 127,
  "completed_tasks": 115,
  "failed_tasks": 5,
  "pending_tasks": 2,
  "processing_tasks": 5,
  "avg_completion_time_minutes": 2.8,
  "success_rate": 90.55
}
```

## Real-Time WebSocket API

### Connect to WebSocket

**WebSocket** `/ws`

Get real-time updates during analysis processing.

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

// Join a specific task for updates
ws.send(JSON.stringify({
  type: "join_task",
  task_id: "123e4567-e89b-12d3-a456-426614174000"
}));

// Receive real-time updates
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  // message.type: "progress_update", "agent_started", "agent_completed", etc.
};
```

**Message Types You'll Receive:**
- `connected`: WebSocket connection established
- `joined_task`: Successfully subscribed to task updates
- `progress_update`: Task progress changed (includes current agent)
- `agent_started`: New agent began execution
- `agent_completed`: Agent finished its work
- `task_completed`: Entire analysis workflow finished
- `task_failed`: Analysis encountered an error

**Message Types You Can Send:**
- `join_task`: Subscribe to updates for a specific task
- `leave_task`: Stop receiving updates for a task
- `ping`: Health check (receives `pong` response)

### WebSocket Statistics

**GET** `/ws/stats`

Check WebSocket server health and connection info.

```json
// Response
{
  "websocket_enabled": true,
  "stats": {
    "active_connections": 3,
    "total_messages_sent": 1247,
    "total_connections": 89
  }
}
```

## Error Handling

All endpoints return standard HTTP status codes and detailed error messages:

```json
// 400 Bad Request (validation error)
{
  "detail": "URL must be from a supported Amazon domain"
}

// 404 Not Found
{
  "detail": "Analysis task not found"
}

// 500 Internal Server Error
{
  "detail": "Failed to create analysis: Database connection error"
}
```

## URL Validation

We only accept Amazon URLs from supported domains:
- amazon.com
- amazon.co.uk  
- amazon.de

The system automatically extracts the ASIN (Amazon Standard Identification Number) from valid product URLs.

## Rate Limiting

Currently no rate limiting is implemented, but the batch endpoint limits you to 10 URLs per request to prevent system overload.

## Authentication

No authentication is currently required. This is a development/demo system.

## Real-World Usage Notes

**Performance:** Most analyses complete in 2-4 minutes depending on data availability and competitor discovery success.

**WebSocket Reliability:** The WebSocket connection automatically handles reconnection. If you miss updates, you can always poll the status endpoint.

**Data Persistence:** All analysis results are stored in PostgreSQL via Supabase. Tasks remain available until explicitly deleted.

**Error Recovery:** If scraping fails, the system falls back to LLM-based analysis to ensure you always get results.

## SDK Examples

### Python Client Example

```python
import httpx
import asyncio

async def analyze_product(product_url: str):
    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
        # Start analysis
        response = await client.post("/analyze", json={"product_url": product_url})
        task = response.json()
        task_id = task["id"]
        
        # Poll for completion
        while True:
            status_response = await client.get(f"/tasks/{task_id}/status")
            status = status_response.json()
            
            print(f"Progress: {status['progress']}% - {status['current_agent']}")
            
            if status["status"] in ["completed", "failed"]:
                break
                
            await asyncio.sleep(2)
        
        # Get final results
        if status["status"] == "completed":
            results = await client.get(f"/tasks/{task_id}")
            return results.json()
```

### JavaScript Frontend Example

```javascript
class AmazonAnalyzer {
  constructor(baseUrl = 'http://localhost:8000/api/v1') {
    this.baseUrl = baseUrl;
  }
  
  async analyzeProduct(productUrl) {
    // Start analysis
    const response = await fetch(`${this.baseUrl}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_url: productUrl })
    });
    
    const task = await response.json();
    
    // Set up WebSocket for real-time updates
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws`);
    
    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'join_task', task_id: task.id }));
    };
    
    return new Promise((resolve) => {
      ws.onmessage = async (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'task_completed') {
          // Get final results
          const results = await fetch(`${this.baseUrl}/tasks/${task.id}`);
          resolve(await results.json());
          ws.close();
        }
      };
    });
  }
}
```

This API documentation reflects what's actually implemented and tested in our system. The multi-agent workflow, WebSocket updates, and data persistence all work as described above.