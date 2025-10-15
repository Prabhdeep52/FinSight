"""
FastAPI routes for LangGraph financial agent interactions.
Provides natural language interface for financial analysis.
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from agents.langgraph_agent import create_financial_agent
from core.utils import logger


# Request/Response models
class AgentQueryRequest(BaseModel):
    """Request model for agent query."""
    query: str = Field(
        ..., 
        description="Natural language query about stocks or financial analysis",
        min_length=3,
        max_length=500
    )
    analysis_type: Optional[str] = Field(
        default="comprehensive",
        description="Type of analysis (comprehensive, valuation, performance, risk)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the situation of Apple stock?",
                "analysis_type": "comprehensive"
            }
        }


class AgentQueryResponse(BaseModel):
    """Response model for agent query."""
    query: str
    response: str
    symbols_analyzed: list
    stock_data: Dict[str, Any]
    analysis_results: Dict[str, Any]
    status: str
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the situation of Apple stock?",
                "response": "Apple (AAPL) is currently showing strong financial fundamentals...",
                "symbols_analyzed": ["AAPL"],
                "stock_data": {"AAPL": {"symbol": "AAPL", "current_price": 150.25}},
                "analysis_results": {"AAPL": {"valuation": "fairly_valued"}},
                "status": "success",
                "error_message": None
            }
        }


class AgentHealthResponse(BaseModel):
    """Response model for agent health check."""
    agent_status: str
    llm_configured: bool
    tools_available: int
    api_connectivity: str
    last_check: str


# Initialize router and agent
router = APIRouter()

# Global agent instance (initialized lazily)
_agent_instance = None


def get_agent():
    """Get or create the global agent instance."""
    global _agent_instance
    if _agent_instance is None:
        logger.info("AgentRoutes: Initializing new agent instance")
        try:
            _agent_instance = create_financial_agent()
            logger.info("AgentRoutes: Agent instance created successfully")
        except Exception as e:
            logger.error(f"AgentRoutes: Failed to create agent instance: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to initialize financial agent: {str(e)}"
            )
    return _agent_instance


@router.get("/", summary="Agent Information")
async def agent_info():
    """Get information about the LangGraph financial agent."""
    logger.info("AgentRoutes: Agent info endpoint called")
    
    return {
        "name": "InvestIQ LangGraph Financial Agent",
        "version": "1.0.0",
        "description": "Natural language interface for financial analysis using LangGraph and LLM",
        "capabilities": [
            "Natural language query processing",
            "Automatic stock symbol detection",
            "Multi-market stock data retrieval (Indian & Global)",
            "Comprehensive financial analysis",
            "Investment recommendations",
            "Risk assessment"
        ],
        "supported_queries": [
            "What is the situation of Apple stock?",
            "Analyze INFY stock performance",
            "Give me financial data for GOOGL",
            "How is TCS performing?",
            "Should I invest in Microsoft?"
        ],
        "endpoints": {
            "/query": "Process natural language financial queries",
            "/health": "Check agent and system health"
        }
    }


@router.post("/query", response_model=AgentQueryResponse, summary="Process Financial Query")
async def process_agent_query(request: AgentQueryRequest):
    """
    Process natural language financial query using LangGraph agent.
    
    The agent will:
    1. Parse your natural language query
    2. Identify stock symbols automatically
    3. Fetch relevant financial data
    4. Perform comprehensive analysis
    5. Generate detailed insights and recommendations
    
    Examples:
    - "What is the situation of Apple stock?"
    - "How is INFY performing?"
    - "Should I invest in Microsoft?"
    - "Analyze TCS financial health"
    """
    logger.info(f"AgentRoutes: Processing query: {request.query}")
    
    try:
        # Get agent instance
        agent = get_agent()
        logger.info("AgentRoutes: Agent instance obtained")
        
        # Process the query
        logger.info("AgentRoutes: Starting query processing")
        result = agent.process_query(request.query)
        logger.info(f"AgentRoutes: Query processing completed with status: {result.get('status')}")
        
        # Log analysis summary
        symbols_count = len(result.get('symbols_analyzed', []))
        logger.info(f"AgentRoutes: Analysis covered {symbols_count} symbols: {result.get('symbols_analyzed')}")
        
        return AgentQueryResponse(**result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(f"AgentRoutes: Unexpected error processing query: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Query processing failed: {str(e)}"
        )


@router.post("/query-simple", summary="Simple Query Interface")
async def process_simple_query(query: str = Body(..., embed=True)):
    """
    Simplified endpoint for processing financial queries.
    
    Send a simple JSON with just the query string:
    {"query": "What is the situation of Apple stock?"}
    """
    logger.info(f"AgentRoutes: Processing simple query: {query}")
    
    try:
        request = AgentQueryRequest(query=query)
        return await process_agent_query(request)
        
    except Exception as e:
        logger.error(f"AgentRoutes: Error in simple query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Simple query processing failed: {str(e)}"
        )


@router.get("/health", response_model=AgentHealthResponse, summary="Agent Health Check")
async def agent_health_check():
    """
    Check the health status of the LangGraph financial agent.
    
    Returns information about:
    - Agent initialization status
    - LLM configuration
    - Available tools
    - API connectivity
    """
    logger.info("AgentRoutes: Agent health check requested")
    
    try:
        from datetime import datetime
        
        # Try to get agent instance
        try:
            agent = get_agent()
            agent_status = "healthy"
            llm_configured = True
            tools_available = len(agent.tools)
            logger.info("AgentRoutes: Agent health check - agent is healthy")
            
        except Exception as e:
            logger.warning(f"AgentRoutes: Agent health check - agent initialization failed: {str(e)}")
            agent_status = "unhealthy"
            llm_configured = False
            tools_available = 0
        
        # Check API connectivity (test with simple request)
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            api_connectivity = "connected" if response.status_code == 200 else "disconnected"
            logger.info(f"AgentRoutes: API connectivity check: {api_connectivity}")
            
        except Exception as e:
            logger.warning(f"AgentRoutes: API connectivity check failed: {str(e)}")
            api_connectivity = "disconnected"
        
        health_response = AgentHealthResponse(
            agent_status=agent_status,
            llm_configured=llm_configured,
            tools_available=tools_available,
            api_connectivity=api_connectivity,
            last_check=datetime.now().isoformat()
        )
        
        logger.info("AgentRoutes: Health check completed successfully")
        return health_response
        
    except Exception as e:
        logger.error(f"AgentRoutes: Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/examples", summary="Query Examples")
async def get_query_examples():
    """Get examples of queries that can be processed by the agent."""
    logger.info("AgentRoutes: Query examples requested")
    
    return {
        "basic_queries": [
            "What is the situation of Apple stock?",
            "How is INFY performing?",
            "Give me financial data for GOOGL",
            "Analyze Microsoft stock"
        ],
        "performance_queries": [
            "How has TCS performed this year?",
            "Is AAPL stock overvalued?",
            "What are the key metrics for RELIANCE?",
            "Should I invest in Tesla?"
        ],
        "comparison_queries": [
            "Compare Apple and Microsoft stocks",
            "Which is better: INFY or TCS?",
            "Analyze both GOOGL and MSFT"
        ],
        "risk_assessment": [
            "What are the risks of investing in AMZN?",
            "Is HDFC a safe investment?",
            "Analyze the risk factors for NVDA"
        ]
    }


@router.get("/supported-symbols", summary="Supported Stock Symbols")
async def get_supported_symbols():
    """Get information about supported stock symbols and markets."""
    logger.info("AgentRoutes: Supported symbols info requested")
    
    return {
        "global_stocks": {
            "description": "Major US and global stocks",
            "examples": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX"],
            "data_source": "Alpha Vantage API"
        },
        "indian_stocks": {
            "description": "Indian market stocks (NSE/BSE)",
            "examples": ["INFY", "TCS", "RELIANCE", "WIPRO", "HDFC", "ICICI", "SBI", "ITC"],
            "data_source": "Screener.in"
        },
        "detection": {
            "method": "Automatic detection based on symbol patterns and known lists",
            "note": "The agent automatically determines whether a stock is Indian or global"
        }
    }