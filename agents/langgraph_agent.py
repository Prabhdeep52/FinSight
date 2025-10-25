"""
Main LangGraph agent for FinSight financial analysis.
Orchestrates financial data retrieval and analysis using LLM and tools.
"""

import json
import re
import uuid
from typing import Dict, Any, List, TypedDict, Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from config.settings import get_settings
from core.utils import logger
import concurrent.futures
from agents.tools.stock_tool import create_stock_data_tool
from agents.tools.analysis_tool import create_financial_analysis_tool
from agents.tools.statement_tools import (
    create_income_statement_tool,
    create_balance_sheet_tool,
    create_cash_flow_tool,
    create_earnings_tool,
)


class AgentState(TypedDict):
    """State management for the LangGraph agent using TypedDict."""

    messages: Annotated[List[Dict[str, Any]], add_messages]
    user_query: str
    extracted_symbols: List[str]
    stock_data: Dict[str, Any]
    statement_data: Dict[
        str, Any
    ]  # Financial statements (income, balance, cash flow, earnings)
    analysis_results: Dict[str, Any]
    final_response: str
    error_message: str
    current_step: str


class FinancialLangGraphAgent:
    """
    Main LangGraph agent for financial analysis.
    Coordinates between LLM, stock data tools, and analysis tools
    to provide comprehensive financial insights.
    """

    def __init__(self):
        logger.info("FinancialLangGraphAgent: Initializing agent")
        self.settings = get_settings()

        # Initialize LLM
        logger.info("FinancialLangGraphAgent: Setting up Google Gemini LLM")
        if not self.settings.google_api_key:
            logger.error("FinancialLangGraphAgent: Google API key not configured")
            raise ValueError("Google API key is required for LLM functionality")

        self.llm = ChatGoogleGenerativeAI(
            model=self.settings.gemini_model,
            google_api_key=self.settings.google_api_key,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
        )
        logger.info(
            f"FinancialLangGraphAgent: LLM configured with model {self.settings.gemini_model}"
        )

        # Initialize tools
        logger.info("FinancialLangGraphAgent: Setting up tools")
        self.stock_tool = create_stock_data_tool()
        self.analysis_tool = create_financial_analysis_tool()
        # Statement tools
        self.income_tool = create_income_statement_tool()
        self.balance_tool = create_balance_sheet_tool()
        self.cashflow_tool = create_cash_flow_tool()
        self.earnings_tool = create_earnings_tool()
        self.tools = [
            self.stock_tool,
            self.analysis_tool,
            self.income_tool,
            self.balance_tool,
            self.cashflow_tool,
            self.earnings_tool,
        ]
        logger.info(f"FinancialLangGraphAgent: Configured {len(self.tools)} tools")

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        logger.info("FinancialLangGraphAgent: Tools bound to LLM")

        # Build the graph
        logger.info("FinancialLangGraphAgent: Building LangGraph workflow")
        self.graph = self._build_graph()
        logger.info("FinancialLangGraphAgent: Agent initialization completed")

    def _normalize_response_content(self, content: Any) -> str:
        """Convert LLM response payloads into plain text."""
        if content is None:
            return ""

        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text") or item.get("content") or ""
                    if isinstance(text, str):
                        parts.append(text)
            return " ".join(parts).strip()

        if isinstance(content, str):
            return content.strip()

        return str(content).strip()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        logger.info("FinancialLangGraphAgent: Building graph workflow")

        # Create the graph
        workflow = StateGraph(AgentState)

        # Add
        logger.info("FinancialLangGraphAgent: Adding workflow nodes")
        workflow.add_node("parse_query", self._parse_query_node)
        workflow.add_node("execute_tools", self._execute_tools_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Set entry point
        workflow.set_entry_point("parse_query")

        # Add edges
        logger.info("FinancialLangGraphAgent: Adding workflow edges")
        workflow.add_edge("parse_query", "execute_tools")
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)

        # Compile the graph
        logger.info("FinancialLangGraphAgent: Compiling workflow graph")
        compiled_graph = workflow.compile()
        logger.info("FinancialLangGraphAgent: Graph compilation completed")

        return compiled_graph

    def _parse_query_node(self, state: AgentState) -> AgentState:
        """Parse user query to understand intent and extract stock symbols."""
        logger.info("FinancialLangGraphAgent: Executing parse_query_node")
        logger.info(
            f"FinancialLangGraphAgent: Processing user query: {state['user_query']}"
        )

        try:
            # Create system message for query parsing
            system_prompt = """Extract stock symbols. Return JSON:
{"symbols": ["SYMBOL1", "SYMBOL2"], "analysis_intent": "...", "needs_data": true}

Shortcuts: Apple->AAPL, Microsoft->MSFT, Amazon->AMZN, Google->GOOGL, Tesla->TSLA, Meta->META, Nvidia->NVDA.
Extract ALL symbols mentioned."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=state["user_query"]),
            ]

            # Call LLM for query parsing
            response = self.llm.invoke(messages)
            response_text = self._normalize_response_content(
                getattr(response, "content", "")
            )

            # Parse LLM response
            # We need to find the JSON part of the response.
            try:
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    json_content = json_match.group(0)
                    parsed_response = json.loads(json_content)
                    logger.info(
                        f"FinancialLangGraphAgent: Parsed response: {parsed_response}"
                    )

                    state["extracted_symbols"] = parsed_response.get("symbols", [])
                    state["current_step"] = "query_parsed"

                    logger.info(
                        f"FinancialLangGraphAgent: Extracted symbols: {state['extracted_symbols']}"
                    )
                else:
                    raise json.JSONDecodeError("No JSON found", "", 0)

            except json.JSONDecodeError:
                logger.warning(
                    "FinancialLangGraphAgent: Failed to parse JSON, using enhanced fallback symbol extraction"
                )
                # Enhanced fallback: check both symbols and company names
                query_lower = state["user_query"].lower()

                # Company name to symbol mapping
                company_mappings = {
                    "apple": "AAPL",
                    "microsoft": "MSFT",
                    "amazon": "AMZN",
                    "google": "GOOGL",
                    "alphabet": "GOOGL",
                    "tesla": "TSLA",
                    "meta": "META",
                    "facebook": "META",
                    "nvidia": "NVDA",
                    "infosys": "INFY",
                    "tcs": "TCS",
                    "reliance": "RELIANCE",
                    "wipro": "WIPRO",
                    "hdfc": "HDFC",
                }

                # Direct symbol mapping
                direct_symbols = [
                    "AAPL",
                    "GOOGL",
                    "MSFT",
                    "AMZN",
                    "TSLA",
                    "META",
                    "NVDA",
                    "INFY",
                    "TCS",
                    "RELIANCE",
                    "WIPRO",
                    "HDFC",
                ]

                found_symbols = []

                # Check for company names
                for company_name, symbol in company_mappings.items():
                    if company_name in query_lower:
                        found_symbols.append(symbol)
                        logger.info(
                            f"FinancialLangGraphAgent: Found company name '{company_name}' -> {symbol}"
                        )

                # Check for direct symbols
                query_upper = state["user_query"].upper()
                for symbol in direct_symbols:
                    if symbol in query_upper and symbol not in found_symbols:
                        found_symbols.append(symbol)
                        logger.info(
                            f"FinancialLangGraphAgent: Found direct symbol '{symbol}'"
                        )

                state["extracted_symbols"] = found_symbols
                logger.info(
                    f"FinancialLangGraphAgent: Enhanced fallback extraction found: {found_symbols}"
                )

            return state

        except Exception as e:
            logger.error(
                f"FinancialLangGraphAgent: Error in parse_query_node: {str(e)}"
            )
            state["error_message"] = f"Query parsing failed: {str(e)}"
            state["current_step"] = "error"
            return state

    def _execute_tools_node(self, state: AgentState) -> AgentState:
        logger.info("FinancialLangGraphAgent: Executing execute_tools_node")

        try:
            # ALWAYS let LLM drive tool execution with live thinking updates
            # This ensures broadcast_thinking_status tool is invoked during analysis
            logger.info(
                "FinancialLangGraphAgent: Delegating tool execution to LLM for live thinking"
            )
            return self._let_llm_decide_tools(state)

        except Exception as e:
            logger.error(
                f"FinancialLangGraphAgent: Error in execute_tools_node: {str(e)}"
            )
            state["error_message"] = f"Tool execution failed: {str(e)}"
            state["current_step"] = "error"
            return state

    def _let_llm_decide_tools(self, state: AgentState) -> AgentState:
        """Let LLM decide which tools to use with agentic loop for multi-step reasoning."""
        logger.info("FinancialLangGraphAgent: Letting LLM decide tool usage")

        try:
            user_query = state["user_query"]
            extracted_symbols = state.get("extracted_symbols", [])

            system_prompt = (
                "You are FinSight. Fetch data for each symbol ONCE only:\n"
                f"Symbols: {', '.join(extracted_symbols)}\n\n"
                "For EACH symbol, call these 5 tools (ONE TIME EACH):\n"
                "1. get_stock_data(symbol)\n"
                "2. get_income_statement(symbol)\n"
                "3. get_balance_sheet(symbol)\n"
                "4. get_cash_flow(symbol)\n"
                "5. get_earnings(symbol)\n\n"
                "CRITICAL RULES:\n"
                "- If you see 'already_fetched' status → Data exists, STOP calling that tool\n"
                "- If you see 'api_unavailable' status → API rate limited, DO NOT RETRY, skip to next tool\n"
                "- Stock overview (get_stock_data) may fail due to API limits - this is OK, continue with statements\n"
                "- NEVER call the same tool for the same symbol twice\n"
                "After all tools complete for all symbols, return NO MORE tool calls to finish."
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Query: {user_query}"),
            ]

            # Agentic loop: keep invoking LLM until it stops requesting tools
            # REDUCED from 20 to 12 to save tokens (2 stocks × 5 tools = 10 calls + buffer)
            max_iterations = 12
            iteration = 0

            while iteration < max_iterations:
                iteration += 1
                logger.info(
                    f"FinancialLangGraphAgent: Agentic loop iteration {iteration}"
                )

                response = self.llm_with_tools.invoke(messages)
                logger.info(
                    f"FinancialLangGraphAgent: LLM response received (iteration {iteration})"
                )

                # Check if LLM wants to call tools
                if not response.tool_calls:
                    logger.info(
                        "FinancialLangGraphAgent: LLM finished - no more tool calls"
                    )
                    break

                logger.info(
                    f"FinancialLangGraphAgent: LLM requested {len(response.tool_calls)} tool calls"
                )

                # Execute each tool call and collect results
                tool_messages = []

                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_call_id = tool_call.get("id", str(uuid.uuid4()))

                    logger.info(
                        f"FinancialLangGraphAgent: Executing tool: {tool_name} with args: {tool_args}"
                    )

                    tool_result = None

                    try:
                        if tool_name == "get_stock_data":
                            symbol = tool_args.get("symbol")
                            if symbol:
                                result = self.stock_tool._run(symbol)
                                result_data = json.loads(result)

                                # Only store if not an error
                                if not result_data.get("error"):
                                    state["stock_data"][symbol] = result_data
                                    logger.info(
                                        f"FinancialLangGraphAgent: Fetched stock data for {symbol}"
                                    )
                                else:
                                    logger.warning(
                                        f"FinancialLangGraphAgent: Stock data fetch failed for {symbol}: {result_data.get('message')}"
                                    )

                                tool_result = result

                        elif tool_name == "get_income_statement":
                            symbol = tool_args.get("symbol")
                            if symbol:
                                result = self.income_tool._run(symbol)
                                if "statement_data" not in state:
                                    state["statement_data"] = {}
                                if symbol not in state["statement_data"]:
                                    state["statement_data"][symbol] = {}
                                state["statement_data"][symbol]["income_statement"] = (
                                    json.loads(result)
                                )
                                tool_result = result
                                logger.info(
                                    f"FinancialLangGraphAgent: Fetched income statement for {symbol}"
                                )

                        elif tool_name == "get_balance_sheet":
                            symbol = tool_args.get("symbol")
                            if symbol:
                                result = self.balance_tool._run(symbol)
                                if "statement_data" not in state:
                                    state["statement_data"] = {}
                                if symbol not in state["statement_data"]:
                                    state["statement_data"][symbol] = {}
                                state["statement_data"][symbol]["balance_sheet"] = (
                                    json.loads(result)
                                )
                                tool_result = result
                                logger.info(
                                    f"FinancialLangGraphAgent: Fetched balance sheet for {symbol}"
                                )

                        elif tool_name == "get_cash_flow":
                            symbol = tool_args.get("symbol")
                            if symbol:
                                result = self.cashflow_tool._run(symbol)
                                if "statement_data" not in state:
                                    state["statement_data"] = {}
                                if symbol not in state["statement_data"]:
                                    state["statement_data"][symbol] = {}
                                state["statement_data"][symbol]["cash_flow"] = (
                                    json.loads(result)
                                )
                                tool_result = result
                                logger.info(
                                    f"FinancialLangGraphAgent: Fetched cash flow for {symbol}"
                                )

                        elif tool_name == "get_earnings":
                            symbol = tool_args.get("symbol")
                            if symbol:
                                result = self.earnings_tool._run(symbol)
                                if "statement_data" not in state:
                                    state["statement_data"] = {}
                                if symbol not in state["statement_data"]:
                                    state["statement_data"][symbol] = {}
                                state["statement_data"][symbol]["earnings"] = (
                                    json.loads(result)
                                )
                                tool_result = result
                                logger.info(
                                    f"FinancialLangGraphAgent: Fetched earnings data for {symbol}"
                                )

                        elif tool_name == "analyze_financial_data":
                            stock_data = tool_args.get("stock_data")
                            analysis_type = tool_args.get(
                                "analysis_type", "comprehensive"
                            )
                            if stock_data:
                                result = self.analysis_tool._run(
                                    stock_data, analysis_type
                                )
                                analysis_data = json.loads(result)
                                symbol = analysis_data.get("symbol", "unknown")
                                state["analysis_results"][symbol] = analysis_data
                                tool_result = result
                                logger.info(
                                    f"FinancialLangGraphAgent: Analyzed data for {symbol}"
                                )

                        if tool_result is None:
                            tool_result = json.dumps(
                                {
                                    "status": "success",
                                    "message": "Tool executed successfully",
                                }
                            )

                    except Exception as tool_error:
                        logger.error(
                            f"FinancialLangGraphAgent: Tool execution error: {str(tool_error)}"
                        )
                        tool_result = json.dumps(
                            {"error": True, "message": str(tool_error)}
                        )

                    # Add SMART tool result - inform LLM what's already been fetched
                    from langchain_core.messages import ToolMessage

                    # Check what data we already have to prevent re-fetching
                    already_fetched = []
                    failed_api_call = False

                    if tool_name == "get_stock_data":
                        symbol = tool_args.get("symbol")
                        # Check if data successfully fetched
                        if symbol in state["stock_data"]:
                            already_fetched.append(f"{symbol} stock data")
                        # Check if API call failed (error in result)
                        elif tool_result and json.loads(tool_result).get("error"):
                            failed_api_call = True

                    elif tool_name in [
                        "get_income_statement",
                        "get_balance_sheet",
                        "get_cash_flow",
                        "get_earnings",
                    ]:
                        symbol = tool_args.get("symbol")
                        statement_key = tool_name.replace("get_", "")
                        if symbol in state.get(
                            "statement_data", {}
                        ) and statement_key in state["statement_data"].get(symbol, {}):
                            already_fetched.append(f"{symbol} {statement_key}")

                    # Create summary based on result status
                    if already_fetched:
                        summary_result = json.dumps(
                            {
                                "status": "already_fetched",
                                "tool": tool_name,
                                "symbol": tool_args.get("symbol", "N/A"),
                                "message": "Data already available - no need to call this again",
                                "note": "All required data has been collected. You can now finish and generate the analysis.",
                            }
                        )
                    elif failed_api_call:
                        error_details = json.loads(tool_result)
                        summary_result = json.dumps(
                            {
                                "status": "api_unavailable",
                                "tool": tool_name,
                                "symbol": tool_args.get("symbol", "N/A"),
                                "message": f"API rate limit exceeded - {error_details.get('message')}",
                                "note": "Stock overview data unavailable. DO NOT retry this call. Use only financial statement data (income/balance/cash/earnings) for analysis.",
                            }
                        )
                    else:
                        summary_result = json.dumps(
                            {
                                "status": "success",
                                "tool": tool_name,
                                "symbol": tool_args.get("symbol", "N/A"),
                                "message": "Data fetched and stored successfully",
                            }
                        )

                    tool_messages.append(
                        ToolMessage(
                            content=summary_result,
                            tool_call_id=tool_call_id,
                            name=tool_name,
                        )
                    )

                # Add assistant message and tool results to conversation
                messages.append(response)
                messages.extend(tool_messages)

                # Check if we have all required data - if so, encourage LLM to finish
                all_symbols = state.get("extracted_symbols", [])
                if all_symbols and all(
                    symbol in state["stock_data"] for symbol in all_symbols
                ):
                    # All stock data fetched - add hint to finish
                    logger.info(
                        f"FinancialLangGraphAgent: All stock data collected for {len(all_symbols)} symbols"
                    )
                    # If we have enough data, add a hint message
                    statement_coverage = sum(
                        1
                        for symbol in all_symbols
                        if symbol in state.get("statement_data", {})
                    )
                    if statement_coverage >= len(all_symbols):
                        logger.info(
                            "FinancialLangGraphAgent: All financial statements collected - encouraging completion"
                        )

                # CRITICAL: Trim message history to prevent token explosion
                # Keep only: system prompt + last user message + last 10 messages
                if len(messages) > 12:
                    # Keep system message, user query, and last 10 messages
                    messages = [messages[0], messages[1]] + messages[-10:]
                    logger.info(
                        f"FinancialLangGraphAgent: Trimmed message history to {len(messages)} messages to save tokens"
                    )

            logger.info(
                f"FinancialLangGraphAgent: Agentic loop completed after {iteration} iterations"
            )

            state["current_step"] = "llm_tools_executed"
            return state

        except Exception as e:
            logger.error(
                f"FinancialLangGraphAgent: Error in LLM tool decision: {str(e)}"
            )
            state["error_message"] = f"LLM tool execution failed: {str(e)}"
            state["current_step"] = "error"
            return state

    def _generate_response_node(self, state: AgentState) -> AgentState:
        """Generate final response based on collected data and analysis."""
        logger.info("FinancialLangGraphAgent: Executing generate_response_node")

        try:
            # Check if we have data to work with
            stock_data_count = len(state["stock_data"])
            analysis_count = len(state["analysis_results"])

            logger.info(
                f"FinancialLangGraphAgent: Context contains {stock_data_count} stock data entries and {analysis_count} analysis results"
            )

            if stock_data_count == 0:
                logger.warning(
                    "FinancialLangGraphAgent: No stock data available for response generation"
                )
                state["final_response"] = (
                    "I apologize, but I couldn't retrieve stock data to analyze your query. Please try again or check the stock symbols."
                )
                state["current_step"] = "response_generated"
                return state

            # Create a more concise context for multiple stocks to avoid token limits
            if stock_data_count > 1:
                # For multiple stocks, create a summary format to reduce token usage
                context_str = self._create_multi_stock_context(state)
                logger.info("FinancialLangGraphAgent: Using multi-stock context format")
            else:
                # For single stock, use full format
                context_str = self._create_single_stock_context(state)
                logger.info(
                    "FinancialLangGraphAgent: Using single-stock context format"
                )

            logger.debug(
                f"FinancialLangGraphAgent: Context string length: {len(context_str)} characters"
            )
            logger.debug(
                f"FinancialLangGraphAgent: Context preview (first 500 chars): {context_str[:500]}..."
            )

            system_prompt = (
                "Financial analyst. Write Markdown report with:\n\n"
                "## Executive Summary\n"
                "Brief 2-3 sentence overview.\n\n"
                "## Key Insights\n"
                "- Revenue & Growth (use income statement)\n"
                "- Profitability (margins, ROE)\n"
                "- Balance Sheet (liquidity, debt, cash)\n"
                "- Cash Flow (operating CF, free CF)\n"
                "- Earnings (EPS trends)\n"
                "- Valuation (P/E, multiples)\n\n"
                "## Risk Assessment\n"
                "Key risks from data.\n\n"
                "## Investment Recommendation\n"
                "Buy/Hold/Sell with brief rationale.\n\n"
                "Use specific numbers from the data provided."
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=context_str),
            ]

            logger.info("FinancialLangGraphAgent: Generating final response with LLM")
            logger.debug(
                f"FinancialLangGraphAgent: System prompt length: {len(system_prompt)} characters"
            )
            logger.debug(
                f"FinancialLangGraphAgent: Context message length: {len(messages[1].content)} characters"
            )

            # Run LLM invocation in a separate thread with a timeout to avoid blocking indefinitely
            llm_timeout = getattr(self.settings, "llm_timeout", 30)
            logger.info(
                f"FinancialLangGraphAgent: Invoking LLM (timeout={llm_timeout}s)"
            )
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self.llm.invoke, messages)
                    response = future.result(timeout=llm_timeout)

                logger.info(
                    f"FinancialLangGraphAgent: LLM response received. Type: {type(response)}"
                )

            except concurrent.futures.TimeoutError:
                logger.error(
                    f"FinancialLangGraphAgent: LLM invoke timed out after {llm_timeout} seconds"
                )

                # Try a single retry with reduced tokens if possible, otherwise return a friendly timeout message
                try:
                    # Attempt to reduce token usage for retry if attribute exists
                    original_max = None
                    if hasattr(self.llm, "max_tokens"):
                        original_max = getattr(self.llm, "max_tokens")
                        try:
                            setattr(self.llm, "max_tokens", min(original_max, 1024))
                            logger.info(
                                "FinancialLangGraphAgent: Retrying LLM invoke with reduced max_tokens"
                            )
                        except Exception:
                            # ignore if we can't set attribute
                            pass

                    response = self.llm.invoke(messages)
                    logger.info(
                        "FinancialLangGraphAgent: LLM response received on retry"
                    )

                    # restore original max_tokens when possible
                    if original_max is not None and hasattr(self.llm, "max_tokens"):
                        try:
                            setattr(self.llm, "max_tokens", original_max)
                        except Exception:
                            pass

                except Exception as e:
                    logger.error(
                        f"FinancialLangGraphAgent: LLM retry failed after timeout: {str(e)}"
                    )
                    state["final_response"] = (
                        "I apologize — the analysis is taking longer than expected. "
                        "Please try again in a few moments or use the streaming endpoint to see progress."
                    )
                    state["current_step"] = "response_generated"
                    return state

            except Exception as e:
                logger.error(f"FinancialLangGraphAgent: Error invoking LLM: {str(e)}")
                state["final_response"] = (
                    f"I apologize, but the analysis engine encountered an error: {str(e)}"
                )
                state["current_step"] = "response_generated"
                return state

            if hasattr(response, "content") and response.content is not None:
                normalized_content = self._normalize_response_content(response.content)
                logger.info(
                    "FinancialLangGraphAgent: LLM response normalized length: %s",
                    len(normalized_content),
                )

                if not normalized_content:
                    logger.error(
                        "FinancialLangGraphAgent: LLM returned empty or whitespace-only response"
                    )
                    logger.debug(
                        f"FinancialLangGraphAgent: Raw response content: '{response.content}'"
                    )
                    state["final_response"] = (
                        "I apologize, but the AI analysis engine returned an empty response. This might be due to content filtering or token limits. Please try rephrasing your query or ask about individual stocks."
                    )
                else:
                    state["final_response"] = normalized_content
                    logger.info(
                        "FinancialLangGraphAgent: Final response generated successfully"
                    )
            else:
                logger.error(
                    f"FinancialLangGraphAgent: LLM response object has no 'content' attribute. Response: {response}"
                )
                state["final_response"] = (
                    "I apologize, but the AI analysis engine returned an unexpected response format. Please try your query again."
                )

            state["current_step"] = "response_generated"
            logger.debug(
                f"FinancialLangGraphAgent: Response length: {len(state['final_response'])} characters"
            )

            return state

        except Exception as e:
            logger.error(
                f"FinancialLangGraphAgent: Error in generate_response_node: {str(e)}"
            )
            state["final_response"] = (
                f"I apologize, but I encountered an error while generating the analysis: {str(e)}"
            )
            state["current_step"] = (
                "response_generated"  # Still mark as completed to avoid error flow
            )
            return state

    def _create_single_stock_context(self, state: AgentState) -> str:
        """Create context string for single stock analysis."""
        symbol = list(state["stock_data"].keys())[0]
        stock_info = state["stock_data"][symbol]

        context_parts = [
            f"Query: {state['user_query']}",
            "",
            f"=== {symbol} - {stock_info.get('name', 'N/A')} ===",
            "",
            "## Stock Overview:",
            f"Market Cap: ${stock_info.get('market_cap', 0) / 1e9:.1f}B",
            f"Current Price: ${stock_info.get('current_price', 'N/A')}",
            f"P/E Ratio: {stock_info.get('pe_ratio', 'N/A')}",
            f"Beta: {stock_info.get('beta', 'N/A')}",
            f"52W Range: ${stock_info.get('low_52week', 'N/A')} - ${stock_info.get('high_52week', 'N/A')}",
            f"Dividend Yield: {stock_info.get('dividend_yield', 0) * 100:.2f}%",
            "",
        ]

        # Add detailed statement data
        statement_info = state.get("statement_data", {}).get(symbol, {})

        if "income_statement" in statement_info:
            context_parts.append("## Income Statement Data:")
            income = statement_info["income_statement"]
            logger.debug(f"Income statement keys: {list(income.keys())}")

            # The data is wrapped in a 'data' key from the tool
            income_data = income.get("data", income)

            # Alpha Vantage returns annual/quarterly reports - get the latest
            if "annualReports" in income_data and income_data["annualReports"]:
                latest = income_data["annualReports"][0]
                context_parts.append(
                    f"Total Revenue: ${float(latest.get('totalRevenue', 0)) / 1e9:.2f}B"
                )
                context_parts.append(
                    f"Gross Profit: ${float(latest.get('grossProfit', 0)) / 1e9:.2f}B"
                )
                context_parts.append(
                    f"Operating Income: ${float(latest.get('operatingIncome', 0)) / 1e9:.2f}B"
                )
                context_parts.append(
                    f"Net Income: ${float(latest.get('netIncome', 0)) / 1e9:.2f}B"
                )
                context_parts.append(
                    f"EBITDA: ${float(latest.get('ebitda', 0)) / 1e9:.2f}B"
                )
            context_parts.append("")

        if "balance_sheet" in statement_info:
            context_parts.append("## Balance Sheet Data:")
            balance = statement_info["balance_sheet"]
            balance_data = balance.get("data", balance)

            if "annualReports" in balance_data and balance_data["annualReports"]:
                latest = balance_data["annualReports"][0]
                context_parts.append(
                    f"Total Assets: ${float(latest.get('totalAssets', 0)) / 1e9:.2f}B"
                )
                context_parts.append(
                    f"Total Liabilities: ${float(latest.get('totalLiabilities', 0)) / 1e9:.2f}B"
                )
                context_parts.append(
                    f"Total Equity: ${float(latest.get('totalShareholderEquity', 0)) / 1e9:.2f}B"
                )
                context_parts.append(
                    f"Cash & Equivalents: ${float(latest.get('cashAndCashEquivalentsAtCarryingValue', 0)) / 1e9:.2f}B"
                )
                context_parts.append(
                    f"Total Debt: ${float(latest.get('shortLongTermDebtTotal', 0)) / 1e9:.2f}B"
                )
                context_parts.append(
                    f"Current Assets: ${float(latest.get('totalCurrentAssets', 0)) / 1e9:.2f}B"
                )
                context_parts.append(
                    f"Current Liabilities: ${float(latest.get('totalCurrentLiabilities', 0)) / 1e9:.2f}B"
                )
            context_parts.append("")

        if "cash_flow" in statement_info:
            context_parts.append("## Cash Flow Statement Data:")
            cashflow = statement_info["cash_flow"]
            cashflow_data = cashflow.get("data", cashflow)

            if "annualReports" in cashflow_data and cashflow_data["annualReports"]:
                latest = cashflow_data["annualReports"][0]
                context_parts.append(
                    f"Operating Cash Flow: ${float(latest.get('operatingCashflow', 0)) / 1e9:.2f}B"
                )
                context_parts.append(
                    f"Capital Expenditures: ${abs(float(latest.get('capitalExpenditures', 0))) / 1e9:.2f}B"
                )
                op_cf = float(latest.get("operatingCashflow", 0))
                capex = abs(float(latest.get("capitalExpenditures", 0)))
                context_parts.append(f"Free Cash Flow: ${(op_cf - capex) / 1e9:.2f}B")
                context_parts.append(
                    f"Dividends Paid: ${abs(float(latest.get('dividendPayout', 0))) / 1e9:.2f}B"
                )
            context_parts.append("")

        if "earnings" in statement_info:
            context_parts.append("## Earnings Data:")
            earnings = statement_info["earnings"]
            earnings_data = earnings.get("data", earnings)

            if (
                "quarterlyEarnings" in earnings_data
                and earnings_data["quarterlyEarnings"]
            ):
                latest = earnings_data["quarterlyEarnings"][0]
                context_parts.append(
                    f"Quarterly EPS: {latest.get('reportedEPS', 'N/A')}"
                )
                context_parts.append(
                    f"Estimated EPS: {latest.get('estimatedEPS', 'N/A')}"
                )
                context_parts.append(f"Surprise: {latest.get('surprise', 'N/A')}")
                context_parts.append(
                    f"Surprise Percentage: {latest.get('surprisePercentage', 'N/A')}%"
                )
            context_parts.append("")

        context_parts.append("---")
        context_parts.append(
            "Using ALL the financial data above, provide comprehensive analysis with specific numbers:"
        )

        return "\n".join(context_parts)

    def _create_multi_stock_context(self, state: AgentState) -> str:
        """Create optimized context string for multiple stocks with key financial statement data."""
        symbols = list(state["stock_data"].keys())

        context_parts = [
            f"Query: {state['user_query']}",
            f"\nComparing {len(symbols)} stocks: {', '.join(symbols)}\n",
        ]

        # Add essential metrics for comparison including statement data
        for symbol in symbols:
            stock_info = state["stock_data"].get(symbol, {})

            context_parts.append(f"=== {symbol} - {stock_info.get('name', 'N/A')} ===")
            context_parts.append(
                f"Market Cap: ${stock_info.get('market_cap', 0) / 1e9:.1f}B"
            )
            context_parts.append(f"P/E: {stock_info.get('pe_ratio', 'N/A')}")
            context_parts.append(f"Beta: {stock_info.get('beta', 'N/A')}")

            # Add statement data summaries
            statement_info = state.get("statement_data", {}).get(symbol, {})

            if "income_statement" in statement_info:
                income = statement_info["income_statement"]
                income_data = income.get("data", income)
                if "annualReports" in income_data and income_data["annualReports"]:
                    latest = income_data["annualReports"][0]
                    context_parts.append(
                        f"Revenue: ${float(latest.get('totalRevenue', 0)) / 1e9:.1f}B"
                    )
                    context_parts.append(
                        f"Net Income: ${float(latest.get('netIncome', 0)) / 1e9:.1f}B"
                    )
                    context_parts.append(
                        f"Operating Income: ${float(latest.get('operatingIncome', 0)) / 1e9:.1f}B"
                    )

            if "balance_sheet" in statement_info:
                balance = statement_info["balance_sheet"]
                balance_data = balance.get("data", balance)
                if "annualReports" in balance_data and balance_data["annualReports"]:
                    latest = balance_data["annualReports"][0]
                    context_parts.append(
                        f"Total Assets: ${float(latest.get('totalAssets', 0)) / 1e9:.1f}B"
                    )
                    context_parts.append(
                        f"Total Debt: ${float(latest.get('shortLongTermDebtTotal', 0)) / 1e9:.1f}B"
                    )
                    context_parts.append(
                        f"Cash: ${float(latest.get('cashAndCashEquivalentsAtCarryingValue', 0)) / 1e9:.1f}B"
                    )

            if "cash_flow" in statement_info:
                cashflow = statement_info["cash_flow"]
                cashflow_data = cashflow.get("data", cashflow)
                if "annualReports" in cashflow_data and cashflow_data["annualReports"]:
                    latest = cashflow_data["annualReports"][0]
                    context_parts.append(
                        f"Operating CF: ${float(latest.get('operatingCashflow', 0)) / 1e9:.1f}B"
                    )
                    op_cf = float(latest.get("operatingCashflow", 0))
                    capex = abs(float(latest.get("capitalExpenditures", 0)))
                    context_parts.append(f"Free CF: ${(op_cf - capex) / 1e9:.1f}B")

            if "earnings" in statement_info:
                earnings = statement_info["earnings"]
                earnings_data = earnings.get("data", earnings)
                if (
                    "quarterlyEarnings" in earnings_data
                    and earnings_data["quarterlyEarnings"]
                ):
                    latest = earnings_data["quarterlyEarnings"][0]
                    context_parts.append(f"EPS: {latest.get('reportedEPS', 'N/A')}")

            context_parts.append("")

        context_parts.append("---")
        context_parts.append(
            "Using ALL the financial statement data above, provide comparative analysis with specific numbers:"
        )

        return "\n".join(context_parts)

    def _handle_error_node(self, state: AgentState) -> AgentState:
        """Handle errors and provide fallback response."""
        logger.info("FinancialLangGraphAgent: Executing handle_error_node")
        logger.error(
            f"FinancialLangGraphAgent: Error encountered: {state['error_message']}"
        )

        state[
            "final_response"
        ] = f"""I apologize, but I encountered an error while processing your request: {state["error_message"]}

Please try rephrasing your query or ensure that:
1. Stock symbols are correctly spelled
2. Your request is clear and specific
3. The financial API is accessible

You can ask questions like:
- "What is the situation of Apple stock?"
- "Analyze INFY stock performance"
- "Give me financial data for GOOGL"
"""

        state["current_step"] = "error_handled"
        logger.info("FinancialLangGraphAgent: Error handling completed")
        return state

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user query and return comprehensive financial analysis.

        Args:
            user_query: Natural language query about stocks or financial analysis

        Returns:
            Dictionary containing analysis results and response
        """
        logger.info(f"FinancialLangGraphAgent: Processing user query: {user_query}")

        try:
            # Initialize state
            initial_state = {
                "messages": [],
                "user_query": user_query,
                "extracted_symbols": [],
                "stock_data": {},
                "statement_data": {},  # Financial statements data
                "analysis_results": {},
                "final_response": "",
                "error_message": "",
                "current_step": "start",
            }

            logger.info("FinancialLangGraphAgent: Starting graph execution")

            # Execute the graph
            final_state = self.graph.invoke(initial_state)

            logger.info(
                f"FinancialLangGraphAgent: Graph execution completed with step: {final_state.get('current_step', 'unknown')}"
            )

            # Prepare result
            result = {
                "query": user_query,
                "response": final_state.get("final_response", "No response generated"),
                "symbols_analyzed": list(final_state.get("stock_data", {}).keys()),
                "stock_data": final_state.get("stock_data", {}),
                "statement_data": final_state.get(
                    "statement_data", {}
                ),  # Financial statements
                "analysis_results": final_state.get("analysis_results", {}),
                "status": "success"
                if final_state.get("current_step") != "error"
                else "error",
                "error_message": final_state.get("error_message")
                if final_state.get("error_message")
                else None,
            }

            logger.info(
                "FinancialLangGraphAgent: Query processing completed successfully"
            )
            return result

        except Exception as e:
            logger.error(
                f"FinancialLangGraphAgent: Unexpected error during query processing: {str(e)}"
            )
            return {
                "query": user_query,
                "response": f"I apologize, but an unexpected error occurred: {str(e)}",
                "symbols_analyzed": [],
                "stock_data": {},
                "analysis_results": {},
                "status": "error",
                "error_message": str(e),
            }

    def stream_execution(self, user_query: str):
        """
        Stream execution events to frontend for real-time progress updates.

        Yields:
            Dict events with type, message, step, and data
        """
        try:
            # Step 1: Initialize
            yield {
                "type": "step",
                "step": "initialize",
                "message": "Setting up analysis environment...",
                "progress": 5,
            }

            # Initialize state
            state = {
                "messages": [],
                "user_query": user_query,
                "extracted_symbols": [],
                "stock_data": {},
                "statement_data": {},
                "analysis_results": {},
                "final_response": "",
                "error_message": "",
                "current_step": "start",
            }

            # Step 2: Parse query
            yield {
                "type": "step",
                "step": "parse_query",
                "message": f'Understanding your question: "{user_query}"',
                "progress": 10,
            }

            state = self._parse_query_node(state)

            if state.get("extracted_symbols"):
                symbols_text = ", ".join(state["extracted_symbols"])
                yield {
                    "type": "step",
                    "step": "symbols_found",
                    "message": f"Detected stocks: {symbols_text}",
                    "data": {"symbols": state["extracted_symbols"]},
                    "progress": 15,
                }

            # Step 3: Fetch data with streaming
            yield {
                "type": "step",
                "step": "fetch_data_start",
                "message": "Starting financial data retrieval...",
                "progress": 20,
            }

            # Stream tool execution
            for tool_event in self._execute_tools_with_streaming(state):
                yield tool_event

            # Step 4: Generate response
            yield {
                "type": "step",
                "step": "generate_response",
                "message": "Analyzing data and preparing comprehensive report...",
                "progress": 90,
            }

            state = self._generate_response_node(state)

            # Step 5: Complete
            yield {
                "type": "complete",
                "step": "done",
                "message": "Analysis complete!",
                "progress": 100,
                "data": {
                    "response": state["final_response"],
                    "symbols_analyzed": list(state["stock_data"].keys()),
                    "stock_data": state["stock_data"],
                    "statement_data": state["statement_data"],
                    "analysis_results": state["analysis_results"],
                },
            }

        except Exception as e:
            logger.error(
                f"FinancialLangGraphAgent: Streaming execution error: {str(e)}"
            )
            yield {"type": "error", "message": f"Error: {str(e)}", "step": "error"}

    def _execute_tools_with_streaming(self, state: AgentState):
        """Execute tools and stream progress updates."""
        symbols = state.get("extracted_symbols", [])
        total_expected_tools = len(symbols) * 5  # 5 tools per symbol
        completed_tools = 0

        # System prompt
        system_prompt = (
            "You are FinSight financial assistant. Your task is to fetch comprehensive data.\n\n"
            f"**Symbols to analyze:** {', '.join(symbols)}\n\n"
            "**Required actions for EACH symbol (call ONCE only):**\n"
            "1. get_stock_data(symbol) - Get overview\n"
            "2. get_income_statement(symbol) - Get revenue & profits\n"
            "3. get_balance_sheet(symbol) - Get assets & liabilities\n"
            "4. get_cash_flow(symbol) - Get cash flow data\n"
            "5. get_earnings(symbol) - Get earnings history\n\n"
            "**CRITICAL RULES:**\n"
            "- Call each tool ONCE per symbol\n"
            "- If a tool returns an error or 'already_fetched' status, do NOT retry it\n"
            "- After completing all tools for all symbols, return NO MORE tool calls\n"
            "- Work efficiently - avoid duplicate calls"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"User query: {state['user_query']}\n\nFetch all required data for the symbols listed above."
            ),
        ]

        max_iterations = 12
        iteration = 0
        tools_called = set()  # Track which tools have been called

        while iteration < max_iterations:
            iteration += 1

            yield {
                "type": "iteration",
                "message": f"Processing step {iteration} of {max_iterations}...",
                "progress": 20
                + int((completed_tools / max(total_expected_tools, 1)) * 65),
                "iteration": iteration,
            }

            response = self.llm_with_tools.invoke(messages)

            if not response.tool_calls:
                logger.info(
                    "FinancialLangGraphAgent: LLM finished - no more tool calls"
                )
                yield {
                    "type": "step",
                    "step": "tools_complete",
                    "message": f"Data collection complete ({completed_tools} tools executed)",
                    "progress": 85,
                }
                break

            tool_messages = []

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_call_id = tool_call.get("id", str(uuid.uuid4()))
                symbol = tool_args.get("symbol", "")

                # Create unique identifier for this tool call
                tool_identifier = f"{tool_name}_{symbol}"

                # Check if already called
                if tool_identifier in tools_called:
                    yield {
                        "type": "tool_skip",
                        "tool": tool_name,
                        "symbol": symbol,
                        "message": f"Skipping {tool_name} for {symbol} (already fetched)",
                        "reasoning": f"I already called {tool_name} for {symbol}, so I'll skip this duplicate request.",
                        "progress": 20
                        + int((completed_tools / max(total_expected_tools, 1)) * 65),
                    }
                    continue

                tools_called.add(tool_identifier)

                # Get display name
                tool_display = tool_name.replace("get_", "").replace("_", " ").title()

                # Reasoning for why we need this tool
                reasoning_map = {
                    "get_stock_data": f"I need to fetch the company overview for {symbol} to understand its market position, valuation metrics, and key fundamentals.",
                    "get_income_statement": f"Now I'll retrieve the income statement for {symbol} to analyze revenue trends, profitability, and operating efficiency.",
                    "get_balance_sheet": f"Next, I need the balance sheet for {symbol} to assess financial health, liquidity, and leverage.",
                    "get_cash_flow": f"I'm fetching cash flow data for {symbol} to evaluate cash generation ability and capital allocation.",
                    "get_earnings": f"Finally, I need earnings history for {symbol} to track quarterly performance and earnings quality.",
                }

                # Stream tool execution with reasoning
                yield {
                    "type": "tool_start",
                    "tool": tool_name,
                    "symbol": symbol,
                    "message": f"Calling {tool_name}({symbol})",
                    "reasoning": reasoning_map.get(
                        tool_name, f"Fetching {tool_display} data for {symbol}"
                    ),
                    "progress": 20
                    + int((completed_tools / max(total_expected_tools, 1)) * 65),
                }

                # Execute tool
                tool_result = self._execute_single_tool(tool_name, tool_args, state)
                completed_tools += 1

                # Check if successful and provide detailed feedback
                try:
                    result_data = json.loads(tool_result)
                    if result_data.get("error"):
                        error_msg = result_data.get("message", "Failed")
                        yield {
                            "type": "tool_error",
                            "tool": tool_name,
                            "symbol": symbol,
                            "message": f" {tool_name}({symbol}) returned error",
                            "reasoning": f"The API returned an error: {error_msg}. I'll continue with available data from other sources.",
                            "progress": 20
                            + int(
                                (completed_tools / max(total_expected_tools, 1)) * 65
                            ),
                        }
                    else:
                        # Extract key insight from the data
                        insight = self._extract_tool_insight(
                            tool_name, result_data, symbol
                        )
                        yield {
                            "type": "tool_success",
                            "tool": tool_name,
                            "symbol": symbol,
                            "message": f"{tool_name}({symbol}) completed",
                            "reasoning": insight,
                            "progress": 20
                            + int(
                                (completed_tools / max(total_expected_tools, 1)) * 65
                            ),
                        }
                except:
                    yield {
                        "type": "tool_success",
                        "tool": tool_name,
                        "symbol": symbol,
                        "message": f"{tool_name}({symbol}) completed",
                        "reasoning": f"Successfully retrieved {tool_display} data for {symbol}.",
                        "progress": 20
                        + int((completed_tools / max(total_expected_tools, 1)) * 65),
                    }

                # Add to messages
                from langchain_core.messages import ToolMessage

                # Summarize result for LLM
                summary = (
                    f"Successfully fetched {tool_name} for {symbol}"
                    if not result_data.get("error")
                    else f"Error fetching {tool_name} for {symbol}: {result_data.get('message')}"
                )

                tool_messages.append(
                    ToolMessage(
                        content=summary, tool_call_id=tool_call_id, name=tool_name
                    )
                )

            messages.append(response)
            messages.extend(tool_messages)

            # Trim messages to save tokens
            if len(messages) > 12:
                messages = [messages[0], messages[1]] + messages[-10:]
                logger.info(
                    "FinancialLangGraphAgent: Trimmed message history to 12 messages to save tokens"
                )

        if iteration >= max_iterations:
            yield {
                "type": "warning",
                "message": f"⚠️  Reached maximum iterations ({max_iterations}). Proceeding with available data.",
                "progress": 85,
            }

    def _extract_tool_insight(
        self, tool_name: str, result_data: dict, symbol: str
    ) -> str:
        """Extract a key insight from tool result data for streaming."""
        try:
            if tool_name == "get_stock_data":
                market_cap = result_data.get("market_cap", 0)
                pe_ratio = result_data.get("pe_ratio", "N/A")
                name = result_data.get("name", symbol)
                return f"Got overview for {name}: Market cap ${market_cap / 1e9:.1f}B, P/E {pe_ratio}. Now I have the valuation context."

            elif tool_name == "get_income_statement":
                income_data = result_data.get("data", result_data)
                if "annualReports" in income_data and income_data["annualReports"]:
                    latest = income_data["annualReports"][0]
                    revenue = float(latest.get("totalRevenue", 0)) / 1e9
                    net_income = float(latest.get("netIncome", 0)) / 1e9
                    return f"Retrieved income statement: Revenue ${revenue:.1f}B, Net Income ${net_income:.1f}B. This shows profitability trends."
                return "Retrieved income statement data successfully."

            elif tool_name == "get_balance_sheet":
                balance_data = result_data.get("data", result_data)
                if "annualReports" in balance_data and balance_data["annualReports"]:
                    latest = balance_data["annualReports"][0]
                    assets = float(latest.get("totalAssets", 0)) / 1e9
                    debt = float(latest.get("shortLongTermDebtTotal", 0)) / 1e9
                    return f"Retrieved balance sheet: Total assets ${assets:.1f}B, Debt ${debt:.1f}B. Now I can assess financial leverage."
                return "Retrieved balance sheet data successfully."

            elif tool_name == "get_cash_flow":
                cf_data = result_data.get("data", result_data)
                if "annualReports" in cf_data and cf_data["annualReports"]:
                    latest = cf_data["annualReports"][0]
                    op_cf = float(latest.get("operatingCashflow", 0)) / 1e9
                    return f"Retrieved cash flow: Operating CF ${op_cf:.1f}B. This reveals cash generation strength."
                return "Retrieved cash flow data successfully."

            elif tool_name == "get_earnings":
                earnings_data = result_data.get("data", result_data)
                if (
                    "quarterlyEarnings" in earnings_data
                    and earnings_data["quarterlyEarnings"]
                ):
                    latest = earnings_data["quarterlyEarnings"][0]
                    eps = latest.get("reportedEPS", "N/A")
                    surprise = latest.get("surprisePercentage", "N/A")
                    return f"Retrieved earnings: Latest EPS {eps}, Surprise {surprise}%. This shows earnings quality."
                return "Retrieved earnings data successfully."

            return f"Successfully retrieved {tool_name.replace('get_', '').replace('_', ' ')} data."

        except Exception:
            return f"Retrieved {tool_name.replace('get_', '').replace('_', ' ')} data successfully."

        state["current_step"] = "tools_executed"

    def _execute_single_tool(
        self, tool_name: str, tool_args: dict, state: AgentState
    ) -> str:
        """Execute a single tool and update state."""
        symbol = tool_args.get("symbol")

        try:
            if tool_name == "get_stock_data":
                result = self.stock_tool._run(symbol)
                result_data = json.loads(result)
                if not result_data.get("error"):
                    state["stock_data"][symbol] = result_data
                    logger.info(
                        f"FinancialLangGraphAgent: Fetched stock data for {symbol}"
                    )
                else:
                    logger.warning(
                        f"FinancialLangGraphAgent: Stock data fetch failed for {symbol}: {result_data.get('message')}"
                    )
                return result

            elif tool_name == "get_income_statement":
                result = self.income_tool._run(symbol)
                if "statement_data" not in state:
                    state["statement_data"] = {}
                if symbol not in state["statement_data"]:
                    state["statement_data"][symbol] = {}
                state["statement_data"][symbol]["income_statement"] = json.loads(result)
                logger.info(
                    f"FinancialLangGraphAgent: Fetched income statement for {symbol}"
                )
                return result

            elif tool_name == "get_balance_sheet":
                result = self.balance_tool._run(symbol)
                if "statement_data" not in state:
                    state["statement_data"] = {}
                if symbol not in state["statement_data"]:
                    state["statement_data"][symbol] = {}
                state["statement_data"][symbol]["balance_sheet"] = json.loads(result)
                logger.info(
                    f"FinancialLangGraphAgent: Fetched balance sheet for {symbol}"
                )
                return result

            elif tool_name == "get_cash_flow":
                result = self.cashflow_tool._run(symbol)
                if "statement_data" not in state:
                    state["statement_data"] = {}
                if symbol not in state["statement_data"]:
                    state["statement_data"][symbol] = {}
                state["statement_data"][symbol]["cash_flow"] = json.loads(result)
                logger.info(f"FinancialLangGraphAgent: Fetched cash flow for {symbol}")
                return result

            elif tool_name == "get_earnings":
                result = self.earnings_tool._run(symbol)
                if "statement_data" not in state:
                    state["statement_data"] = {}
                if symbol not in state["statement_data"]:
                    state["statement_data"][symbol] = {}
                state["statement_data"][symbol]["earnings"] = json.loads(result)
                logger.info(
                    f"FinancialLangGraphAgent: Fetched earnings data for {symbol}"
                )
                return result

            elif tool_name == "analyze_financial_data":
                result = self.analysis_tool._run(symbol)
                state["analysis_results"][symbol] = json.loads(result)
                logger.info(
                    f"FinancialLangGraphAgent: Completed financial analysis for {symbol}"
                )
                return result

            else:
                logger.warning(f"FinancialLangGraphAgent: Unknown tool: {tool_name}")
                return json.dumps(
                    {"error": True, "message": f"Unknown tool: {tool_name}"}
                )

        except Exception as e:
            logger.error(
                f"FinancialLangGraphAgent: Error executing tool {tool_name}: {str(e)}"
            )
            return json.dumps({"error": True, "message": str(e)})


def create_financial_agent() -> FinancialLangGraphAgent:
    """
    Factory function to create a financial LangGraph agent.

    Returns:
        Configured FinancialLangGraphAgent instance
    """
    logger.info("Creating FinancialLangGraphAgent")
    agent = FinancialLangGraphAgent()
    logger.info("FinancialLangGraphAgent created successfully")
    return agent
