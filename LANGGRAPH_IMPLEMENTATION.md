# InvestIQ LangGraph Financial Agent

## Overview

This is a comprehensive implementation of a LangGraph-based multi-agent financial analysis system. The system uses Google's Gemini LLM to automatically understand natural language queries, detect stock symbols, fetch financial data, and provide intelligent analysis.

## ✅ Current Implementation Status

### ✅ **COMPLETED FEATURES**

1. **LangGraph Multi-Agent System**

   - Fully implemented with StateGraph workflow
   - Automatic tool selection by LLM
   - Comprehensive logging throughout the system
   - Error handling and fallback responses

2. **Intelligent Stock Detection**

   - LLM automatically detects stock symbols from natural language
   - No manual Indian vs Global classification required
   - Supports both Indian and Global markets
   - Automatic market routing based on symbol patterns

3. **Tools Implementation**

   - **Stock Data Tool**: Fetches data from existing API endpoints
   - **Financial Analysis Tool**: Provides comprehensive analysis
   - Both tools are LangChain-compatible with proper schemas

4. **API Integration**

   - New `/api/v1/agent/` endpoints for natural language queries
   - Maintains existing `/api/v1/` endpoints for direct data access
   - FastAPI documentation auto-generation

5. **Comprehensive Logging**
   - Detailed logging at every function call
   - Debug and info level logs throughout the system
   - Easy debugging and monitoring

## 🏗️ Architecture

### **LangGraph Workflow**

```
User Query → Query Parser → Tool Selector → Tool Execution → Analysis → Response Generation
```

### **Agent Components**

1. **FinancialLangGraphAgent**: Main orchestrator
2. **StockDataTool**: Fetches financial data
3. **FinancialAnalysisTool**: Analyzes data and generates insights
4. **AgentState**: Manages workflow state

### **API Layers**

1. **Agent Routes** (`/api/v1/agent/`): Natural language interface
2. **Direct Routes** (`/api/v1/`): Direct financial data access
3. **Tool Layer**: Connects to existing financial APIs

## 🛠️ How It Works

### **1. Natural Language Processing**

```python
# User Input: "What is the situation of Apple stock?"
# LLM automatically:
# 1. Identifies "Apple" as AAPL stock symbol
# 2. Determines need for stock data
# 3. Calls appropriate tools
# 4. Generates comprehensive analysis
```

### **2. Automatic Tool Selection**

- LLM decides which tools to use based on query
- No hardcoded logic for Indian vs Global detection
- Tools are called automatically when needed

### **3. Comprehensive Analysis**

- Financial metrics interpretation
- Valuation assessment
- Risk factor analysis
- Investment recommendations

## 📁 File Structure

```
agents/
├── __init__.py
├── langgraph_agent.py      # Main LangGraph agent
├── tools/
│   ├── __init__.py
│   ├── stock_tool.py       # Stock data fetching tool
│   └── analysis_tool.py    # Financial analysis tool
routes/
├── finance_routes.py       # Existing direct API routes
└── agent_routes.py         # New LangGraph agent routes
```

## 🚀 Usage Examples

### **Basic Query**

```bash
POST /api/v1/agent/query
{
  "query": "What is the situation of Apple stock?"
}
```

### **Response Structure**

```json
{
  "query": "What is the situation of Apple stock?",
  "response": "Apple (AAPL) is currently showing strong financial fundamentals...",
  "symbols_analyzed": ["AAPL"],
  "stock_data": {"AAPL": {...}},
  "analysis_results": {"AAPL": {...}},
  "status": "success"
}
```

## 🔧 Setup and Configuration

### **1. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **2. Configure Environment**

Update `.env` file:

```env
# Required for LLM functionality
GOOGLE_API_KEY=your_google_api_key_here

# Already configured
ALPHAVANTAGE_API_KEY=7G0TIKXZ5S056R0Y
```

### **3. Run the Application**

```bash
python main.py
```

### **4. Test the Implementation**

```bash
python test_agent.py
```

## 📡 API Endpoints

### **Agent Endpoints (New)**

- `GET /api/v1/agent/` - Agent information
- `POST /api/v1/agent/query` - Process natural language queries
- `POST /api/v1/agent/query-simple` - Simplified query interface
- `GET /api/v1/agent/health` - Agent health check
- `GET /api/v1/agent/examples` - Query examples
- `GET /api/v1/agent/supported-symbols` - Supported symbols info

### **Direct Data Endpoints (Existing)**

- `GET /api/v1/stock/{symbol}` - Direct stock data
- `GET /api/v1/stocks` - Multiple stocks data
- `GET /api/v1/health` - API health check

## 🧪 Testing

### **Automated Tests**

Run `python test_agent.py` to verify:

- ✅ Tool creation and functionality
- ✅ Indian vs Global stock detection
- ✅ Analysis tool with mock data
- ✅ Agent state management
- ✅ Import verification

### **Manual Testing Examples**

1. "What is the situation of Apple stock?"
2. "How is INFY performing?"
3. "Analyze Microsoft financial health"
4. "Should I invest in TCS?"

## 🔍 Logging and Debugging

### **Log Levels**

- **INFO**: Major operations and workflow steps
- **DEBUG**: Detailed data processing and metrics
- **WARNING**: Non-critical issues
- **ERROR**: Failures and exceptions

### **Log Examples**

```
INFO - StockDataTool: Starting data fetch for symbol: AAPL
INFO - FinancialAnalysisTool: Performing comprehensive analysis
INFO - FinancialLangGraphAgent: Query processing completed successfully
```

## ⚠️ Current Limitations

1. **Google API Key Required**: Full LLM functionality needs GOOGLE_API_KEY
2. **Local API Dependency**: Stock tool requires local API server running
3. **Rate Limits**: Subject to Alpha Vantage and Google API rate limits

## 🔮 Future Extensions (Ready to Implement)

1. **News Sentiment Tool**: Fetch and analyze news sentiment
2. **Financial Statements Tool**: Detailed financial statement analysis
3. **Technical Analysis Tool**: Chart patterns and technical indicators
4. **Portfolio Analysis Tool**: Multi-stock portfolio optimization
5. **Comparison Tool**: Side-by-side stock comparisons

## 🎯 Key Benefits Achieved

1. **✅ No Manual Logic**: LLM handles all decision making
2. **✅ Extensible**: Easy to add new tools and capabilities
3. **✅ Intelligent**: Automatic symbol detection and market routing
4. **✅ Comprehensive**: Detailed analysis with recommendations
5. **✅ Well-Logged**: Extensive logging for debugging
6. **✅ Production-Ready**: Proper error handling and validation

## 💡 How to Get Google API Key

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Create a new API key
4. Add it to your `.env` file as `GOOGLE_API_KEY=your_key_here`

## 🚦 Quick Start

1. **Clone and setup**: Already done ✅
2. **Install dependencies**: `pip install -r requirements.txt` ✅
3. **Run tests**: `python test_agent.py` ✅
4. **Get Google API key**: Follow instructions above
5. **Start server**: `python main.py`
6. **Visit docs**: http://localhost:8000/docs
7. **Test query**: POST to `/api/v1/agent/query`

The implementation is complete and ready for use! The LLM will automatically handle tool selection and provide intelligent financial analysis based on natural language queries.
