"""
FastAPI routes for LangGraph financial agent interactions.
Provides natural language interface for financial analysis.
"""

from fastapi import APIRouter, HTTPException, Body, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from agents.langgraph_agent import create_financial_agent
from agents.langgraph_agent_optimized import create_optimized_financial_agent
from agents.langgraph_agent_autonomous import create_optimized_autonomous_agent  # NEW
from config.settings import get_settings
from core.utils import logger
from core.auth import JWTBearer, get_current_user
import json
import asyncio


# Request/Response models
class AgentQueryRequest(BaseModel):
    """Request model for agent query."""

    query: str = Field(
        ...,
        description="Natural language query about stocks or financial analysis",
        min_length=3,
        max_length=500,
    )
    session_id: Optional[str] = Field(
        default=None, description="Optional session id for conversation continuity"
    )
    user_id: Optional[str] = Field(
        default=None, description="Optional user id for persistence"
    )
    analysis_type: Optional[str] = Field(
        default="comprehensive",
        description="Type of analysis (comprehensive, valuation, performance, risk)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the situation of Apple stock?",
                "session_id": "test-session-123",
                "user_id": "test_user",
                "analysis_type": "comprehensive",
            }
        }


class AgentQueryResponse(BaseModel):
    """Response model for agent query."""

    query: str
    response: str
    symbols_analyzed: list
    stock_data: Dict[str, Any]
    statement_data: Dict[
        str, Any
    ] = {}  # Financial statements (income, balance, cash flow, earnings)
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
                "error_message": None,
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

# Global agent instances (initialized lazily)
_agent_instance = None
_optimized_agent_instance = None
_autonomous_agent_instance = None


def reset_agent_cache():
    """Reset agent cache to force re-initialization."""
    global _agent_instance, _optimized_agent_instance, _autonomous_agent_instance
    _agent_instance = None
    _optimized_agent_instance = None
    _autonomous_agent_instance = None
    logger.info("AgentRoutes: Agent cache reset")


def get_agent():
    """Get or create the appropriate agent instance based on settings."""
    settings = get_settings()

    # Use autonomous agent if enabled (highest priority)
    if settings.use_autonomous_agent:
        global _autonomous_agent_instance
        if _autonomous_agent_instance is None:
            logger.info("AgentRoutes: Initializing new AUTONOMOUS agent instance")
            try:
                _autonomous_agent_instance = create_optimized_autonomous_agent()
                logger.info(
                    "AgentRoutes: Autonomous agent instance created successfully"
                )
            except Exception as e:
                logger.error(
                    f"AgentRoutes: Failed to create autonomous agent: {str(e)}"
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to initialize autonomous agent: {str(e)}",
                )
        return _autonomous_agent_instance

    # Use optimized agent if enabled
    elif settings.use_optimized_agent:
        global _optimized_agent_instance
        if _optimized_agent_instance is None:
            logger.info("AgentRoutes: Initializing new OPTIMIZED agent instance")
            try:
                _optimized_agent_instance = create_optimized_financial_agent()
                logger.info(
                    "AgentRoutes: Optimized agent instance created successfully"
                )
            except Exception as e:
                logger.error(f"AgentRoutes: Failed to create optimized agent: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to initialize optimized agent: {str(e)}",
                )
        return _optimized_agent_instance

    else:
        # Use original agent
        global _agent_instance
        if _agent_instance is None:
            logger.info("AgentRoutes: Initializing new ORIGINAL agent instance")
            try:
                _agent_instance = create_financial_agent()
                logger.info("AgentRoutes: Original agent instance created successfully")
            except Exception as e:
                logger.error(f"AgentRoutes: Failed to create original agent: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to initialize original agent: {str(e)}",
                )
        return _agent_instance


@router.get("/", summary="Agent Information")
async def agent_info():
    """Get information about the LangGraph financial agent."""
    logger.info("AgentRoutes: Agent info endpoint called")

    return {
        "name": "FinSight LangGraph Financial Agent",
        "version": "1.0.0",
        "description": "Natural language interface for financial analysis using LangGraph and LLM",
        "capabilities": [
            "Natural language query processing",
            "Automatic stock symbol detection",
            "Multi-market stock data retrieval (Indian & Global)",
            "Comprehensive financial analysis",
            "Investment recommendations",
            "Risk assessment",
        ],
        "supported_queries": [
            "What is the situation of Apple stock?",
            "Analyze INFY stock performance",
            "Give me financial data for GOOGL",
            "How is TCS performing?",
            "Should I invest in Microsoft?",
        ],
        "endpoints": {
            "/query": "Process natural language financial queries",
            "/health": "Check agent and system health",
        },
    }


@router.post(
    "/query", response_model=AgentQueryResponse, summary="Process Financial Query"
)
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

        # Process the query with session support
        logger.info("AgentRoutes: Starting query processing")
        result = agent.process_query(
            request.query, session_id=request.session_id, user_id=request.user_id
        )
        logger.info(
            f"AgentRoutes: Query processing completed with status: {result.get('status')}"
        )

        # Log analysis summary
        symbols_count = len(result.get("symbols_analyzed", []))
        logger.info(
            f"AgentRoutes: Analysis covered {symbols_count} symbols: {result.get('symbols_analyzed')}"
        )

        # Add availability markers for data that wasn't fetched
        for symbol in result.get("symbols_analyzed", []):
            statement_data = result.get("statement_data", {}).get(symbol, {})

            # Mark missing statement data
            if "income_statement" not in statement_data:
                if "statement_data" not in result:
                    result["statement_data"] = {}
                if symbol not in result["statement_data"]:
                    result["statement_data"][symbol] = {}
                result["statement_data"][symbol]["income_statement"] = {
                    "available": False,
                    "message": "Agent did not request this data",
                }

            if "balance_sheet" not in statement_data:
                if symbol not in result["statement_data"]:
                    result["statement_data"][symbol] = {}
                result["statement_data"][symbol]["balance_sheet"] = {
                    "available": False,
                    "message": "Agent did not request this data",
                }

            if "cash_flow" not in statement_data:
                if symbol not in result["statement_data"]:
                    result["statement_data"][symbol] = {}
                result["statement_data"][symbol]["cash_flow"] = {
                    "available": False,
                    "message": "Agent did not request this data",
                }

            if "earnings" not in statement_data:
                if symbol not in result["statement_data"]:
                    result["statement_data"][symbol] = {}
                result["statement_data"][symbol]["earnings"] = {
                    "available": False,
                    "message": "Agent did not request this data",
                }

        return AgentQueryResponse(**result)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"AgentRoutes: Unexpected error processing query: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Query processing failed: {str(e)}"
        )


@router.post(
    "/query-stream",
    summary="Stream Query Processing",
    dependencies=[Depends(JWTBearer())],
)
async def stream_agent_query(request_data: AgentQueryRequest, req: Request):
    """
    Stream agent thinking process to frontend in real-time.

    Returns Server-Sent Events (SSE) with agent progress updates.
    Requires: Authorization: Bearer <token>
    """
    # Get user_id from JWT token
    user_id = get_current_user(req)
    logger.info(
        f"AgentRoutes: Starting streaming query for user {user_id}: {request_data.query}"
    )

    async def event_generator():
        try:
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Initializing agent...', 'step': 'init', 'progress': 0})}\n\n"
            await asyncio.sleep(0.1)

            agent = get_agent()
            logger.info("AgentRoutes: Agent instance obtained for streaming")

            # Stream execution events with session support (use JWT user_id)
            for event in agent.stream_execution(
                request_data.query,
                session_id=request_data.session_id,
                user_id=user_id,  # Use user_id from JWT token
            ):
                yield f"data: {json.dumps(event)}\n\n"
                await asyncio.sleep(0.05)

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"AgentRoutes: Streaming error: {str(e)}")
            error_event = {"type": "error", "message": str(e), "step": "error"}
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
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
            status_code=500, detail=f"Simple query processing failed: {str(e)}"
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
            logger.warning(
                f"AgentRoutes: Agent health check - agent initialization failed: {str(e)}"
            )
            agent_status = "unhealthy"
            llm_configured = False
            tools_available = 0

        # Check API connectivity (test with simple request)
        try:
            import requests

            response = requests.get("http://localhost:8000/health", timeout=5)
            api_connectivity = (
                "connected" if response.status_code == 200 else "disconnected"
            )
            logger.info(f"AgentRoutes: API connectivity check: {api_connectivity}")

        except Exception as e:
            logger.warning(f"AgentRoutes: API connectivity check failed: {str(e)}")
            api_connectivity = "disconnected"

        health_response = AgentHealthResponse(
            agent_status=agent_status,
            llm_configured=llm_configured,
            tools_available=tools_available,
            api_connectivity=api_connectivity,
            last_check=datetime.now().isoformat(),
        )

        logger.info("AgentRoutes: Health check completed successfully")
        return health_response

    except Exception as e:
        logger.error(f"AgentRoutes: Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/examples", summary="Query Examples")
async def get_query_examples():
    """Get examples of queries that can be processed by the agent."""
    logger.info("AgentRoutes: Query examples requested")

    return {
        "basic_queries": [
            "What is the situation of Apple stock?",
            "How is INFY performing?",
            "Give me financial data for GOOGL",
            "Analyze Microsoft stock",
        ],
        "performance_queries": [
            "How has TCS performed this year?",
            "Is AAPL stock overvalued?",
            "What are the key metrics for RELIANCE?",
            "Should I invest in Tesla?",
        ],
        "comparison_queries": [
            "Compare Apple and Microsoft stocks",
            "Which is better: INFY or TCS?",
            "Analyze both GOOGL and MSFT",
        ],
        "risk_assessment": [
            "What are the risks of investing in AMZN?",
            "Is HDFC a safe investment?",
            "Analyze the risk factors for NVDA",
        ],
    }


@router.post(
    "/clear-session-cache",
    summary="Clear Session Cache",
    dependencies=[Depends(JWTBearer())],
)
async def clear_session_cache(
    req: Request, session_id: Optional[str] = Body(None, embed=True)
):
    """
    Clear session-level data cache for follow-up questions.
    Call this when user starts a new chat to ensure fresh data fetching.
    Requires: Authorization: Bearer <token>

    Args:
        session_id: Optional session ID to clear. If not provided, clears all caches.
    """
    user_id = get_current_user(req)
    logger.info(
        f"AgentRoutes: Clearing session cache for user {user_id}, session_id={session_id}"
    )

    try:
        agent = get_agent()
        if hasattr(agent, "clear_session_cache"):
            agent.clear_session_cache(session_id)
            return {
                "status": "success",
                "message": f"Session cache cleared for {session_id if session_id else 'all sessions'}",
            }
        else:
            return {
                "status": "not_supported",
                "message": "Current agent does not support session caching",
            }
    except Exception as e:
        logger.error(f"AgentRoutes: Error clearing session cache: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to clear session cache: {str(e)}"
        )


@router.get("/supported-symbols", summary="Supported Stock Symbols")
async def get_supported_symbols():
    """Get information about supported stock symbols and markets."""
    logger.info("AgentRoutes: Supported symbols info requested")

    return {
        "global_stocks": {
            "description": "Major US and global stocks",
            "examples": [
                "AAPL",
                "GOOGL",
                "MSFT",
                "AMZN",
                "TSLA",
                "META",
                "NVDA",
                "NFLX",
            ],
            "data_source": "Alpha Vantage API",
        },
        "indian_stocks": {
            "description": "Indian market stocks (NSE/BSE)",
            "examples": [
                "INFY",
                "TCS",
                "RELIANCE",
                "WIPRO",
                "HDFC",
                "ICICI",
                "SBI",
                "ITC",
            ],
            "data_source": "Screener.in",
        },
        "detection": {
            "method": "Automatic detection based on symbol patterns and known lists",
            "note": "The agent automatically determines whether a stock is Indian or global",
        },
    }


@router.get(
    "/chat-history",
    summary="Get User Chat History",
    dependencies=[Depends(JWTBearer())],
)
async def get_chat_history(req: Request):
    """
    Get all conversations for the authenticated user.
    Requires: Authorization: Bearer <token>

    Returns list of conversations with session_id, title, created_at, updated_at.
    """
    user_id = get_current_user(req)
    logger.info(f"AgentRoutes: Fetching chat history for user {user_id}")

    try:
        from database.supabase_client import get_supabase_client

        supabase = get_supabase_client()

        # Query conversations for this user (RLS will automatically filter)
        response = (
            supabase.table("conversations")
            .select("id, session_id, title, created_at, updated_at")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )

        return {"status": "success", "conversations": response.data}

    except Exception as e:
        logger.error(f"AgentRoutes: Error fetching chat history: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch chat history: {str(e)}"
        )


@router.get(
    "/chat-messages/{session_id}",
    summary="Get Chat Messages",
    dependencies=[Depends(JWTBearer())],
)
async def get_chat_messages(session_id: str, req: Request):
    """
    Get all messages for a specific conversation along with thinking_history.
    Requires: Authorization: Bearer <token>

    RLS policies ensure users can only access their own conversations.
    """
    user_id = get_current_user(req)
    logger.info(
        f"AgentRoutes: Fetching messages for session {session_id}, user {user_id}"
    )

    try:
        from database.supabase_client import get_supabase_client

        supabase = get_supabase_client()

        # Verify session belongs to user and get thinking_history
        conv_response = (
            supabase.table("conversations")
            .select("id, thinking_history")
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not conv_response.data:
            raise HTTPException(
                status_code=404, detail="Conversation not found or unauthorized"
            )

        conversation = conv_response.data[0]
        thinking_history = conversation.get("thinking_history", []) or []

        # Fetch messages (RLS will automatically filter)
        messages_response = (
            supabase.table("messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )

        return {
            "status": "success",
            "session_id": session_id,
            "messages": messages_response.data,
            "thinking_history": thinking_history,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AgentRoutes: Error fetching messages: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch messages: {str(e)}"
        )


@router.delete(
    "/chat-history/{session_id}",
    summary="Delete Conversation",
    dependencies=[Depends(JWTBearer())],
)
async def delete_conversation(session_id: str, req: Request):
    """
    Delete a conversation and all its messages.
    Requires: Authorization: Bearer <token>

    RLS policies ensure users can only delete their own conversations.
    """
    user_id = get_current_user(req)
    logger.info(f"AgentRoutes: Deleting conversation {session_id} for user {user_id}")

    try:
        from database.supabase_client import get_supabase_client

        supabase = get_supabase_client()

        # Verify conversation belongs to user
        conv_response = (
            supabase.table("conversations")
            .select("id")
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not conv_response.data:
            raise HTTPException(
                status_code=404, detail="Conversation not found or unauthorized"
            )

        # Delete conversation (messages will cascade delete)
        delete_response = (
            supabase.table("conversations")
            .delete()
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        return {"status": "success", "message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AgentRoutes: Error deleting conversation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete conversation: {str(e)}"
        )


@router.post(
    "/update-conversation-title",
    summary="Update Conversation Title",
    dependencies=[Depends(JWTBearer())],
)
async def update_conversation_title(req: Request, data: dict = Body(...)):
    """
    Update conversation title immediately when first message is sent.
    This makes the conversation appear in the sidebar right away.

    Requires: Authorization: Bearer <token>
    """
    user_id = get_current_user(req)
    session_id = data.get("session_id")
    title = data.get("title")

    if not session_id or not title:
        raise HTTPException(status_code=400, detail="session_id and title are required")

    logger.info(f"AgentRoutes: Updating title for session {session_id}, user {user_id}")

    try:
        from database.supabase_client import get_supabase_client

        supabase = get_supabase_client()

        # Verify conversation exists and belongs to user
        conv_response = (
            supabase.table("conversations")
            .select("id")
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not conv_response.data:
            # Conversation doesn't exist yet, create it
            supabase.table("conversations").insert(
                {"user_id": user_id, "session_id": session_id, "title": title}
            ).execute()
            logger.info(f"✅ Created conversation with title: {title}")
        else:
            # Update existing conversation
            supabase.table("conversations").update({"title": title}).eq(
                "session_id", session_id
            ).eq("user_id", user_id).execute()
            logger.info(f"✅ Updated conversation title: {title}")

        return {"status": "success", "message": "Conversation title updated"}

    except Exception as e:
        logger.error(f"AgentRoutes: Error updating conversation title: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update conversation title: {str(e)}"
        )


@router.post(
    "/save-thinking/{session_id}",
    summary="Save Thinking Events",
    dependencies=[Depends(JWTBearer())],
)
async def save_thinking_events(
    session_id: str, req: Request, thinking_data: dict = Body(...)
):
    """
    Append thinking/streaming events to the conversation's thinking_history.
    This is called from frontend after each query completion.

    The thinking_history is an array of all thinking events across all queries in the conversation.
    We append a separator and the new events after each query.

    Requires: Authorization: Bearer <token>
    """
    user_id = get_current_user(req)
    logger.info(
        f"AgentRoutes: Appending thinking for session {session_id}, user {user_id}"
    )

    try:
        from database.supabase_client import get_supabase_client

        supabase = get_supabase_client()

        # Verify conversation belongs to user and get current thinking_history
        conv_response = (
            supabase.table("conversations")
            .select("id, thinking_history")
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not conv_response.data:
            raise HTTPException(
                status_code=404, detail="Conversation not found or unauthorized"
            )

        conversation = conv_response.data[0]
        current_thinking = conversation.get("thinking_history", []) or []

        # Get new thinking events from request
        new_events = thinking_data.get("thinking", [])

        # If there's existing thinking, add a separator before appending new events
        if len(current_thinking) > 0 and len(new_events) > 0:
            separator = {
                "type": "status",
                "step": "new_query",
                "message": "─── New Query ───",
                "progress": 0,
            }
            current_thinking.append(separator)

        # Append new events
        current_thinking.extend(new_events)

        # Update conversation with appended thinking_history
        update_response = (
            supabase.table("conversations")
            .update({"thinking_history": current_thinking})
            .eq("session_id", session_id)
            .eq("user_id", user_id)
            .execute()
        )

        logger.info(
            f"✅ Appended {len(new_events)} thinking events to conversation {session_id}"
        )
        logger.info(
            f"   Total thinking events in conversation: {len(current_thinking)}"
        )

        return {
            "status": "success",
            "message": "Thinking events appended successfully",
            "events_count": len(new_events),
            "total_events": len(current_thinking),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AgentRoutes: Error saving thinking events: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to save thinking events: {str(e)}"
        )
