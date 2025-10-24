# FinSight — Autonomous Financial Research Agent

### AI-powered multi-tool financial analysis system
**Backend:** FastAPI · LangChain · Google Gemini API
**Frontend:** React · TailwindCSS (real-time streaming UI)
**Data Sources:** Financial APIs · DuckDuckGo News · PostgreSQL (memory store)

---
## Demo
| | |
|:--:|:--:|
| <img src="https://github.com/user-attachments/assets/8248b404-ad92-405c-8933-da03d36e3227" width="1350"/> | <img src="https://github.com/user-attachments/assets/d8633c75-5d9d-4433-870a-89d45200f12b" width="400"/> |


---

## Overview

**FinSight** is an autonomous financial research agent that performs comprehensive, end-to-end analysis of public companies based on natural language queries.

When a user asks a question such as *"How is Amazon performing recently?"*, the agent:

1. Interprets the financial intent of the query.
2. Plans which data sources and tools are required (stock overview, income statement, balance sheet, cash flow, earnings, or news).
3. Executes all relevant data retrievals concurrently through an intelligent batching system.
4. Streams reasoning, progress updates, and tool activity to the frontend in real time.
5. Produces a structured Markdown-based report summarizing performance, valuation, risk, and market sentiment.

This project demonstrates a complete full-stack implementation of an autonomous agent — combining reasoning, concurrent tool execution, caching, and real-time visualization.

---

## Key Features

### Backend (FastAPI + LangChain)
- **Autonomous tool selection:**
  The LLM dynamically decides which data sources are needed to answer a query.
- **Intelligent batching:**
  Executes multiple API calls in parallel using `ThreadPoolExecutor` to reduce latency.
- **Session memory and caching:**
  Stores past query results to avoid redundant API calls during a session.
- **News integration:**
  Fetches recent articles from DuckDuckGo News and extracts article content for sentiment-aware analysis.
- **Streaming responses:**
  Uses Server-Sent Events (SSE) to stream real-time agent reasoning and progress updates to the frontend.
- **Optimized final synthesis:**
  Combines structured financial data and recent news into a comprehensive Markdown report.

### Frontend (React + TailwindCSS)
- **Dynamic agent sidebar:**
  Displays the agent’s step-by-step reasoning, tool calls, and progress in real time.
- **Live streaming of events:**
  Shows tool success, errors, and analysis results as they occur.
- **Interactive query interface:**
  Accepts user input and displays AI responses with formatted Markdown.
- **Token-efficient visualization:**
  Displays concise insights and summarized financial information for clarity.

---

## Technical Architecture

1. **Frontend (React):**
   - User submits a financial or analytical query.
   - Establishes an SSE (Server-Sent Events) connection to the backend.
   - Renders streaming progress, reasoning, and final analysis output dynamically.

2. **Backend (FastAPI):**
   - Receives user queries at `/agent/query-stream`.
   - Passes the request to `OptimizedAutonomousAgent`.
   - Agent plans and executes tool calls in parallel.
   - Streams intermediate reasoning and tool outcomes back to the frontend.
   - Generates a structured final response.

3. **Agent Core (LangChain + Gemini):**
   - Autonomous planning: Decides required tools.
   - Parallel execution: Gathers financial, statement, and news data.
   - Context creation: Merges all retrieved data into a single reasoning context.
   - Final generation: Produces a comprehensive financial report with performance and risk insights.

---

## Tools Used

- Components and Technologies Used
- Backend Framework: FastAPI
- Agent Framework: LangChain / LangGraph
- LLM: Google Gemini API
- Frontend Framework: React with TailwindCSS
- Data Sources: Financial APIs and DuckDuckGo News
- Database: PostgreSQL
- Streaming Protocol: Server-Sent Events (SSE)
- Deployment Options: Render, Railway, or LangServe


## Folder Structure

The project is organized into the following main directories:

-   `agents/`: Contains the core LangChain/LangGraph agent implementations and their specialized tools.
    -   `agents/tools/`: Custom tools used by the agent for data retrieval and analysis.
-   `config/`: Configuration settings for the application.
-   `core/`: Core utilities, authentication logic, and constants.
-   `data_services/`: Services for interacting with external financial data providers.
-   `database/`: Database setup, migrations (Supabase), and client.
-   `Frontend/`: The React and TypeScript-based web user interface.
    -   `Frontend/src/`: Source code for the frontend application.
    -   `Frontend/src/components/`: Reusable UI components.
    -   `Frontend/src/pages/`: Top-level pages of the application (e.g., HomePage, LoginPage).
    -   `Frontend/src/services/`: Frontend services, including streaming.
-   `routes/`: FastAPI routes defining the API endpoints (agent, auth, finance).
-   `tests/`: Unit and integration tests for the backend.
-   `tools/`: Additional utility scripts or external API integrations.
