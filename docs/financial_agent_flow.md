# Financial Agent Application: Code Flow Documentation

This document provides a detailed step-by-step explanation of the code flow for the Financial Agent application. It includes function snippets and their roles in the overall workflow.

---

## **1. Application Overview**

The Financial Agent application is a LangGraph-based system that combines:

- **LLM (Large Language Model)** for natural language understanding.
- **Financial tools** for data retrieval and analysis.
- **FastAPI** for exposing APIs.

It supports two main API endpoints:

1. **Direct Data Access (v1)**: Fetch raw financial data.
2. **AI-Powered Analysis (v2)**: Use LLM to analyze queries and generate insights.

---

## **2. Code Flow: From Input to Output**

### **Step 1: HTTP Request Hits FastAPI**

```python
# File: main.py
@app.post("/api/v1/agent/query")
def query_agent(request: AgentQueryRequest):
    # FastAPI receives the request and routes to agent_routes.py
```

### **Step 2: Route Handler Execution**

```python
# File: routes/agent_routes.py
async def query_agent(request: AgentQueryRequest):
    logger.info(f"AgentRoutes: Processing query: {request.query}")

    # Initialize agent
    agent = create_financial_agent()

    # Process query
    result = agent.process_query(request.query)
    return AgentQueryResponse(**result)
```

### **Step 3: Agent Initialization**

```python
# File: agents/langgraph_agent.py
def create_financial_agent() -> FinancialLangGraphAgent:
    logger.info("Creating FinancialLangGraphAgent")
    agent = FinancialLangGraphAgent()
    return agent
```

### **Step 4: Agent Constructor**

```python
# File: agents/langgraph_agent.py
class FinancialLangGraphAgent:
    def __init__(self):
        logger.info("FinancialLangGraphAgent: Initializing agent")

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1
        )

        # Initialize tools
        self.stock_tool = create_stock_data_tool()
        self.analysis_tool = create_financial_analysis_tool()

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools([self.stock_tool, self.analysis_tool])

        # Build LangGraph workflow
        self.graph = self._build_graph()
```

### **Step 5: Graph Construction**

```python
# File: agents/langgraph_agent.py
def _build_graph(self) -> StateGraph:
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("parse_query", self._parse_query_node)
    workflow.add_node("execute_tools", self._execute_tools_node)
    workflow.add_node("generate_response", self._generate_response_node)

    # Define flow
    workflow.set_entry_point("parse_query")
    workflow.add_edge("parse_query", "execute_tools")
    workflow.add_edge("execute_tools", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()
```

---

## **3. LangGraph Workflow Execution**

### **Node 1: Parse Query**

```python
# File: agents/langgraph_agent.py
def _parse_query_node(self, state: AgentState) -> AgentState:
    logger.info("Executing parse_query_node")

    # Create system prompt for LLM
    system_prompt = """You are a financial analysis assistant. Extract stock symbols from the query."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state['user_query'])
    ]

    # Call LLM for query parsing
    response = self.llm.invoke(messages)

    # Parse LLM response
    parsed_response = json.loads(response.content)
    state['extracted_symbols'] = parsed_response.get("symbols", [])
    state['current_step'] = "query_parsed"
    return state
```

### **Node 2: Execute Tools**

```python
# File: agents/langgraph_agent.py
def _execute_tools_node(self, state: AgentState) -> AgentState:
    logger.info("Executing execute_tools_node")

    for symbol in state['extracted_symbols']:
        # Fetch stock data using tool
        stock_data_result = self.stock_tool._run(symbol)
        state['stock_data'][symbol] = json.loads(stock_data_result)

    state['current_step'] = "tools_executed"
    return state
```

### **Node 3: Generate Response**

```python
# File: agents/langgraph_agent.py
def _generate_response_node(self, state: AgentState) -> AgentState:
    logger.info("Executing generate_response_node")

    # Prepare context for response generation
    context = {
        "user_query": state['user_query'],
        "stock_data": state['stock_data']
    }

    system_prompt = """You are a professional financial analyst. Generate a comprehensive response."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Context: {json.dumps(context)}")
    ]

    # Generate final response with LLM
    response = self.llm.invoke(messages)
    state['final_response'] = response.content
    state['current_step'] = "response_generated"
    return state
```

---

## **4. Tool Execution: Stock Data Fetching**

### **Stock Data Tool**

```python
# File: agents/tools/stock_tool.py
class StockDataTool(BaseTool):
    def _run(self, symbol: str) -> str:
        logger.info(f"Fetching data for symbol: {symbol}")

        # Call FinancialAgent directly
        agent = FinancialAgent()
        result = agent.get_stock_data(symbol)
        return json.dumps(result)
```

### **Financial Agent**

```python
# File: data_services/financial_agent.py
class FinancialAgent:
    def get_stock_data(self, symbol: str) -> Dict:
        logger.info(f"Processing request for symbol: {symbol}")

        if self._is_indian_stock(symbol):
            return self.nse_service.get_stock_data(symbol)
        else:
            return self.alpha_vantage_service.get_company_overview(symbol)
```

---

## **5. Final Output**

### **API Response**

```json
{
  "query": "What is the situation of Apple stock?",
  "response": "Apple (AAPL) is currently showing strong fundamentals with a P/E ratio of 37.6...",
  "symbols_analyzed": ["AAPL"],
  "stock_data": {
    "AAPL": {
      "Symbol": "AAPL",
      "Name": "Apple Inc",
      "MarketCapitalization": "3677003448000",
      "PERatio": "37.6",
      "EPS": "6.59"
    }
  },
  "status": "success"
}
```
