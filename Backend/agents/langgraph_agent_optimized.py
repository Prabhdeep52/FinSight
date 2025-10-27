"""
Optimized LangGraph agent with hybrid planning approach.
Reduces LLM calls from 12-15 to 3-4 for multi-stock comparisons.

Architecture:
1. Planning Phase: LLM decides what tools are needed (1 call)
2. Parallel Execution: Fetch all tools simultaneously (0 calls)
3. Review Phase: LLM checks if more data needed (1 call)
4. Final Analysis: Generate comprehensive response (1 call)

Total: 3-4 LLM calls instead of 12-15 (70% reduction)
"""

import json
import uuid
from typing import Dict, Any, List, TypedDict, Annotated
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from Backend.config.settings import get_settings
from Backend.core.utils import logger
import re
import concurrent.futures

from Backend.agents.tools.stock_tool import create_stock_data_tool
from Backend.agents.tools.analysis_tool import create_financial_analysis_tool
from Backend.agents.tools.statement_tools import (
    create_income_statement_tool,
    create_balance_sheet_tool,
    create_cash_flow_tool,
    create_earnings_tool,
)


class AgentState(TypedDict):
    """State management for the optimized agent."""

    messages: Annotated[List[Dict[str, Any]], add_messages]
    user_query: str
    extracted_symbols: List[str]
    stock_data: Dict[str, Any]
    statement_data: Dict[str, Any]
    analysis_results: Dict[str, Any]
    final_response: str
    error_message: str
    current_step: str
    tool_plan: Dict[str, Any]  # NEW: Stores the LLM's tool execution plan
    fetch_summary: List[str]  # NEW: Summary of what was fetched


class OptimizedFinancialAgent:
    """
    Optimized agent using hybrid planning approach.
    Much faster and cheaper than the original agentic loop.
    """

    def __init__(self):
        """Initialize the optimized agent."""
        logger.info("OptimizedFinancialAgent: Initializing optimized agent")

        self.settings = get_settings()

        # Initialize LLM (without tools binding initially)
        logger.info("OptimizedFinancialAgent: Setting up Google Gemini LLM")
        self.llm = ChatGoogleGenerativeAI(
            model=self.settings.gemini_model,
            google_api_key=self.settings.google_api_key,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
        )
        logger.info(
            f"OptimizedFinancialAgent: LLM configured with model {self.settings.gemini_model}"
        )

        # Initialize tools
        logger.info("OptimizedFinancialAgent: Setting up tools")
        self.stock_tool = create_stock_data_tool()
        self.income_tool = create_income_statement_tool()
        self.balance_tool = create_balance_sheet_tool()
        self.cashflow_tool = create_cash_flow_tool()
        self.earnings_tool = create_earnings_tool()
        self.analysis_tool = create_financial_analysis_tool()

        logger.info("OptimizedFinancialAgent: All tools initialized")

        # Tool mapping for parallel execution
        self.tool_map = {
            "stock_overview": self.stock_tool,
            "income_statement": self.income_tool,
            "balance_sheet": self.balance_tool,
            "cash_flow": self.cashflow_tool,
            "earnings": self.earnings_tool,
        }

        logger.info("OptimizedFinancialAgent: Initialization completed")

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process user query using optimized 4-phase approach.

        Args:
            user_query: Natural language financial query

        Returns:
            Dict with response, symbols_analyzed, stock_data, etc.
        """
        logger.info(f"OptimizedFinancialAgent: Processing query: {user_query}")

        try:
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
                "tool_plan": {},
                "fetch_summary": [],
            }

            # Phase 0: Parse query to extract symbols
            state = self._parse_query_node(state)

            if not state.get("extracted_symbols"):
                return {
                    "query": user_query,
                    "response": "I couldn't identify any stock symbols in your query. Please mention specific companies or ticker symbols.",
                    "symbols_analyzed": [],
                    "stock_data": {},
                    "statement_data": {},
                    "analysis_results": {},
                    "status": "error",
                    "error_message": "No symbols found",
                }

            # Phase 1: Planning - Ask LLM what tools it needs
            logger.info(
                "OptimizedFinancialAgent: PHASE 1 - Creating tool execution plan"
            )
            tool_plan = self._create_tool_plan(state)
            state["tool_plan"] = tool_plan

            # Phase 2: Parallel Execution - Execute all tools simultaneously
            logger.info(
                "OptimizedFinancialAgent: PHASE 2 - Executing tools in parallel"
            )
            self._execute_plan_parallel(state, tool_plan)

            # Phase 3: Review & Supplement - Check if more data needed
            logger.info("OptimizedFinancialAgent: PHASE 3 - Reviewing fetched data")
            additional_needed = self._review_and_supplement(state)

            if additional_needed["needed"]:
                logger.info(
                    f"OptimizedFinancialAgent: Fetching additional data: {additional_needed['tools']}"
                )
                self._fetch_additional_data(state, additional_needed["tools"])

            # Phase 4: Final Analysis - Generate response with all data
            logger.info("OptimizedFinancialAgent: PHASE 4 - Generating final analysis")
            state = self._generate_response_node(state)

            return {
                "query": user_query,
                "response": state["final_response"],
                "symbols_analyzed": state["extracted_symbols"],
                "stock_data": state["stock_data"],
                "statement_data": state["statement_data"],
                "analysis_results": state["analysis_results"],
                "status": "success",
                "error_message": None,
            }

        except Exception as e:
            logger.error(f"OptimizedFinancialAgent: Error processing query: {str(e)}")
            return {
                "query": user_query,
                "response": f"I encountered an error: {str(e)}",
                "symbols_analyzed": [],
                "stock_data": {},
                "statement_data": {},
                "analysis_results": {},
                "status": "error",
                "error_message": str(e),
            }

    def _parse_query_node(self, state: AgentState) -> AgentState:
        """Parse user query to extract symbols (same as original)."""
        logger.info("OptimizedFinancialAgent: Parsing query to extract symbols")

        query = state["user_query"]

        parsing_prompt = f"""
Analyze this financial query and extract information:

Query: "{query}"

Return a JSON object with:
{{
  "symbols": ["AAPL", "MSFT", ...],  // Stock symbols mentioned
  "analysis_intent": "brief description of what user wants",
  "needs_data": true/false  // Whether financial data is needed
}}

Examples:
- "How is Apple doing?" → {{"symbols": ["AAPL"], "analysis_intent": "current performance", "needs_data": true}}
- "Compare MSFT and GOOGL" → {{"symbols": ["MSFT", "GOOGL"], "analysis_intent": "comparison", "needs_data": true}}
"""

        try:
            response = self.llm.invoke([HumanMessage(content=parsing_prompt)])

            # Extract JSON from response
            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                state["extracted_symbols"] = parsed.get("symbols", [])
                logger.info(
                    f"OptimizedFinancialAgent: Extracted symbols: {state['extracted_symbols']}"
                )
            else:
                logger.warning("Could not parse symbols from LLM response")
                state["extracted_symbols"] = []

        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            state["extracted_symbols"] = []

        return state

    def _create_tool_plan(self, state: AgentState) -> Dict[str, Any]:
        """
        PHASE 1: Ask LLM what tools it needs for this query.
        Returns a structured plan instead of making tool calls.
        """
        symbols = state["extracted_symbols"]
        user_query = state["user_query"]

        planning_prompt = f"""
You are a financial analyst planning data collection.

Query: "{user_query}"
Symbols: {", ".join(symbols)}

Analyze the query and decide what financial data you need. Consider:

**Query Types & Required Data:**
- **Comparison**: ALL 5 data types for ALL symbols (comprehensive comparison)
- **Performance Analysis**: ALL 5 data types (full picture of company health)
- **Valuation**: Overview + Income + Balance Sheet (need debt for valuation multiples)
- **Earnings Focus**: Earnings + Income Statement only
- **Financial Health**: Balance Sheet + Cash Flow only
- **Quick Market Check**: Stock Overview only

**Available Data Types:**
1. `stock_overview` - Market cap, PE ratio, price, beta, 52W range
2. `income_statement` - Revenue, profit, margins, operating income
3. `balance_sheet` - Assets, liabilities, debt, equity, cash
4. `cash_flow` - Operating CF, free CF, capex
5. `earnings` - Quarterly EPS, surprises, guidance

**IMPORTANT RULES:**
- Questions about "how is [stock]" or "performance" need ALL 5 data types (user wants complete picture)
- Comparisons ALWAYS need ALL data for ALL symbols (fair comparison requires same data)
- When in doubt, fetch MORE rather than less (better to have extra data than miss something)
- Only skip data types if query explicitly asks for narrow analysis (e.g., "just earnings")

Return JSON:
{{
  "query_type": "comparison|performance|valuation|earnings|health|quick_check",
  "reasoning": "explain why you need this data",
  "symbols": [
    {{
      "symbol": "AAPL",
      "data_needed": ["stock_overview", "income_statement", "balance_sheet", "cash_flow", "earnings"],
      "rationale": "why each data type is needed"
    }}
  ],
  "estimated_completeness": "90%",
  "priority": "high|medium|low"
}}
"""

        try:
            logger.info("Asking LLM to create data fetching plan...")
            response = self.llm.invoke(
                [
                    SystemMessage(
                        content="You are a financial data analyst creating efficient data fetching plans."
                    ),
                    HumanMessage(content=planning_prompt),
                ]
            )

            # Parse JSON plan
            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                logger.info(
                    f"LLM Plan: {plan.get('query_type', 'unknown')} - {plan.get('reasoning', 'no reasoning')[:100]}"
                )
                return plan
            else:
                logger.warning("Could not parse plan, using comprehensive fallback")
                return self._create_comprehensive_plan(symbols)

        except Exception as e:
            logger.error(f"Error creating plan: {e}")
            return self._create_comprehensive_plan(symbols)

    def _create_comprehensive_plan(self, symbols: List[str]) -> Dict[str, Any]:
        """Fallback: comprehensive plan that fetches everything."""
        return {
            "query_type": "comprehensive",
            "reasoning": "Using comprehensive data fetch to ensure complete analysis",
            "symbols": [
                {
                    "symbol": sym,
                    "data_needed": [
                        "stock_overview",
                        "income_statement",
                        "balance_sheet",
                        "cash_flow",
                        "earnings",
                    ],
                    "rationale": "Fetching all data for thorough analysis",
                }
                for sym in symbols
            ],
            "estimated_completeness": "100%",
            "priority": "high",
        }

    def _execute_plan_parallel(self, state: AgentState, plan: Dict[str, Any]):
        """
        PHASE 2: Execute the LLM's plan in parallel.
        Uses ThreadPoolExecutor to fetch all tools simultaneously.
        """
        # Build task list from plan
        fetch_tasks = []
        for symbol_plan in plan.get("symbols", []):
            symbol = symbol_plan["symbol"]
            data_needed = symbol_plan.get("data_needed", [])

            for data_type in data_needed:
                fetch_tasks.append(
                    {
                        "data_type": data_type,
                        "symbol": symbol,
                        "rationale": symbol_plan.get("rationale", ""),
                    }
                )

        total_tasks = len(fetch_tasks)
        logger.info(f"Executing {total_tasks} fetch operations in parallel")

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}

            for task in fetch_tasks:
                future = executor.submit(
                    self._fetch_single_data, task["data_type"], task["symbol"]
                )
                futures[future] = task

            # Collect results
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result(timeout=30)

                    # Store result in state
                    self._store_fetch_result(
                        state, task["data_type"], task["symbol"], result
                    )

                    # Add to summary
                    if not result.get("error"):
                        state["fetch_summary"].append(
                            f"✓ {task['data_type']} for {task['symbol']}"
                        )
                    else:
                        state["fetch_summary"].append(
                            f"✗ {task['data_type']} for {task['symbol']}: {result.get('message', 'error')}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error fetching {task['data_type']} for {task['symbol']}: {e}"
                    )
                    state["fetch_summary"].append(
                        f"✗ {task['data_type']} for {task['symbol']}: {str(e)}"
                    )

        logger.info(
            f"Parallel fetch completed. Summary: {len(state['fetch_summary'])} operations"
        )

    def _fetch_single_data(self, data_type: str, symbol: str) -> Dict[str, Any]:
        """Fetch a single piece of data using the appropriate tool."""
        try:
            tool = self.tool_map.get(data_type)
            if not tool:
                return {"error": True, "message": f"Unknown data type: {data_type}"}

            result = tool._run(symbol)
            return json.loads(result) if isinstance(result, str) else result

        except Exception as e:
            return {"error": True, "message": str(e)}

    def _store_fetch_result(
        self, state: AgentState, data_type: str, symbol: str, result: Dict[str, Any]
    ):
        """Store fetched data in the appropriate state location."""
        if result.get("error"):
            return

        if data_type == "stock_overview":
            state["stock_data"][symbol] = result
        else:
            # Store in statement_data
            if symbol not in state["statement_data"]:
                state["statement_data"][symbol] = {}
            state["statement_data"][symbol][data_type] = result

    def _review_and_supplement(self, state: AgentState) -> Dict[str, Any]:
        """
        PHASE 3: Show LLM what was fetched (metadata only) and ask if more data needed.
        """
        user_query = state["user_query"]
        symbols = state["extracted_symbols"]
        fetch_summary = state["fetch_summary"]

        review_prompt = f"""
You just fetched financial data for: {", ".join(symbols)}

Original query: "{user_query}"

**What was fetched:**
{chr(10).join(fetch_summary)}

**Available in state:**
- Stock overviews: {list(state["stock_data"].keys())}
- Financial statements: {list(state["statement_data"].keys())}

**Question:** Do you have SUFFICIENT data to provide a comprehensive answer to the user's question?

Consider:
- Can you answer the query completely with this data?
- Is any critical information missing?
- Would additional data significantly improve the answer?

Return JSON:
{{
  "needed": true/false,
  "reasoning": "explain your assessment",
  "tools": ["additional_tool1", "additional_tool2"],  // if needed=true
  "confidence": "high|medium|low"  // confidence you can answer well
}}

**Be honest:** Only request more data if truly necessary. Don't over-fetch.
"""

        try:
            response = self.llm.invoke(
                [
                    SystemMessage(
                        content="You are reviewing if you have sufficient data to answer a financial query."
                    ),
                    HumanMessage(content=review_prompt),
                ]
            )

            # Parse response
            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                review = json.loads(json_match.group())
                logger.info(
                    f"LLM Review: needed={review.get('needed', False)}, confidence={review.get('confidence', 'unknown')}"
                )
                return review
            else:
                return {
                    "needed": False,
                    "reasoning": "Sufficient data available",
                    "confidence": "medium",
                }

        except Exception as e:
            logger.error(f"Error in review: {e}")
            return {
                "needed": False,
                "reasoning": "Error in review, proceeding with available data",
                "confidence": "low",
            }

    def _fetch_additional_data(self, state: AgentState, additional_tools: List[str]):
        """Fetch additional data if LLM determined it's needed."""
        logger.info(f"Fetching additional data: {additional_tools}")

        symbols = state["extracted_symbols"]

        # Build additional fetch tasks
        fetch_tasks = []
        for symbol in symbols:
            for tool_type in additional_tools:
                fetch_tasks.append({"data_type": tool_type, "symbol": symbol})

        # Execute additional fetches in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}

            for task in fetch_tasks:
                future = executor.submit(
                    self._fetch_single_data, task["data_type"], task["symbol"]
                )
                futures[future] = task

            # Collect results
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result(timeout=30)
                    self._store_fetch_result(
                        state, task["data_type"], task["symbol"], result
                    )

                    if not result.get("error"):
                        state["fetch_summary"].append(
                            f"Additional fetch: {task['data_type']} for {task['symbol']}"
                        )
                        logger.info(
                            f"Successfully fetched additional {task['data_type']} for {task['symbol']}"
                        )
                    else:
                        logger.warning(
                            f"Failed to fetch additional {task['data_type']} for {task['symbol']}: {result.get('message')}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error fetching additional {task['data_type']} for {task['symbol']}: {e}"
                    )

        logger.info(
            f"Additional data fetch completed. Total operations: {len(fetch_tasks)}"
        )

    def _generate_response_node(self, state: AgentState) -> AgentState:
        """
        PHASE 4: Generate final response with all collected data.
        (Same as original agent)
        """
        logger.info("Generating final response")

        try:
            symbols = state["extracted_symbols"]
            stock_data_count = len(state["stock_data"])

            if stock_data_count == 0:
                state["final_response"] = (
                    "I couldn't retrieve sufficient data to analyze your query. Please try again."
                )
                return state

            # Create context from collected data
            if len(symbols) > 1:
                context_str = self._create_multi_stock_context(state)
            else:
                context_str = self._create_single_stock_context(state)

            system_prompt = (
                "Financial analyst. Write Markdown report with:\n\n"
                "## Executive Summary\n"
                "Brief 2-3 sentence overview.\n\n"
                "## Key Insights\n"
                "- Revenue & Growth\n"
                "- Profitability\n"
                "- Balance Sheet\n"
                "- Cash Flow\n"
                "- Earnings\n"
                "- Valuation\n\n"
                "## Risk Assessment\n\n"
                "## Investment Recommendation\n\n"
                "Use specific numbers from the data."
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=context_str),
            ]

            # Invoke with timeout
            llm_timeout = 60
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self.llm.invoke, messages)
                    response = future.result(timeout=llm_timeout)

                state["final_response"] = response.content
                logger.info("Final response generated successfully")

            except concurrent.futures.TimeoutError:
                logger.error(f"LLM timed out after {llm_timeout}s")
                state["final_response"] = (
                    "Analysis is taking longer than expected. Please try again."
                )

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            state["final_response"] = f"Error generating analysis: {str(e)}"

        return state

    def _create_single_stock_context(self, state: AgentState) -> str:
        """Create context for single stock (same as original)."""
        symbol = list(state["stock_data"].keys())[0]
        stock_info = state["stock_data"][symbol]

        context_parts = [
            f"Query: {state['user_query']}",
            "",
            f"=== {symbol} - {stock_info.get('name', 'N/A')} ===",
            "",
            "## Stock Overview:",
            f"Market Cap: ${stock_info.get('market_cap', 0) / 1e9:.1f}B",
            f"P/E Ratio: {stock_info.get('pe_ratio', 'N/A')}",
            f"Beta: {stock_info.get('beta', 'N/A')}",
            "",
        ]

        # Add statement data if available
        statement_info = state.get("statement_data", {}).get(symbol, {})

        if "income_statement" in statement_info:
            income = statement_info["income_statement"]
            income_data = income.get("data", income)
            if "annualReports" in income_data and income_data["annualReports"]:
                latest = income_data["annualReports"][0]
                context_parts.append("## Income Statement:")
                context_parts.append(
                    f"Revenue: ${float(latest.get('totalRevenue', 0)) / 1e9:.1f}B"
                )
                context_parts.append(
                    f"Net Income: ${float(latest.get('netIncome', 0)) / 1e9:.1f}B"
                )
                context_parts.append("")

        return "\n".join(context_parts)

    def _create_multi_stock_context(self, state: AgentState) -> str:
        """Create context for multiple stocks (same as original)."""
        symbols = list(state["stock_data"].keys())

        context_parts = [
            f"Query: {state['user_query']}",
            f"\nComparing {len(symbols)} stocks: {', '.join(symbols)}\n",
        ]

        for symbol in symbols:
            stock_info = state["stock_data"].get(symbol, {})
            context_parts.append(f"=== {symbol} ===")
            context_parts.append(
                f"Market Cap: ${stock_info.get('market_cap', 0) / 1e9:.1f}B"
            )
            context_parts.append(f"P/E: {stock_info.get('pe_ratio', 'N/A')}")
            context_parts.append("")

        return "\n".join(context_parts)

    def stream_execution(self, user_query: str):
        """
        Stream execution events for real-time progress updates.
        Optimized version with 4-phase progress tracking.
        """
        try:
            # Initialize
            yield {
                "type": "step",
                "step": "initialize",
                "message": "Initializing analysis engine...",
                "reasoning": "Setting up the optimized 4-phase analysis pipeline for efficient data gathering and analysis.",
                "progress": 5,
            }

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
                "tool_plan": {},
                "fetch_summary": [],
            }

            # Phase 0: Parse Query
            yield {
                "type": "step",
                "step": "parse_query",
                "message": f'Understanding your query: "{user_query}"',
                "reasoning": "Let me first extract the stock symbols and understand what type of analysis you need.",
                "progress": 10,
            }

            state = self._parse_query_node(state)

            if not state.get("extracted_symbols"):
                yield {
                    "type": "error",
                    "message": "I could not find any stock symbols in your query",
                    "step": "error",
                }
                return

            symbols_text = ", ".join(state["extracted_symbols"])
            yield {
                "type": "step",
                "step": "symbols_found",
                "message": f"I identified {len(state['extracted_symbols'])} stock(s) to analyze: {symbols_text}",
                "reasoning": f"Now that I know which companies to research, I will create an intelligent data fetching plan based on your question.",
                "progress": 15,
            }

            # Phase 1: Planning
            yield {
                "type": "step",
                "step": "planning",
                "message": "Planning what financial data I need to gather...",
                "reasoning": "I am analyzing your query to determine exactly which data points are necessary. This helps me avoid fetching irrelevant information and saves time.",
                "progress": 20,
            }

            tool_plan = self._create_tool_plan(state)
            state["tool_plan"] = tool_plan

            # Calculate total tools to fetch
            total_tools = sum(
                len(sp.get("data_needed", [])) for sp in tool_plan.get("symbols", [])
            )

            yield {
                "type": "step",
                "step": "plan_created",
                "message": f"Data collection plan ready: {tool_plan.get('query_type', 'unknown')} analysis",
                "reasoning": f"{tool_plan.get('reasoning', 'I have determined what data I need')}. I will now fetch {total_tools} pieces of financial data.",
                "progress": 25,
                "data": {
                    "query_type": tool_plan.get("query_type"),
                    "total_tools": total_tools,
                    "completeness": tool_plan.get("estimated_completeness"),
                },
            }

            # Phase 2: Parallel Execution
            yield {
                "type": "step",
                "step": "parallel_execution_start",
                "message": f"Now fetching {total_tools} data points simultaneously...",
                "reasoning": "Instead of requesting data one piece at a time, I am fetching everything in parallel. This approach is significantly faster, especially when analyzing multiple companies.",
                "progress": 30,
            }

            # Stream parallel execution progress
            yield from self._stream_parallel_execution(state, tool_plan)

            yield {
                "type": "step",
                "step": "parallel_execution_complete",
                "message": f"Data collection complete - retrieved {len(state['fetch_summary'])} pieces of information",
                "reasoning": f"I have successfully gathered comprehensive financial data for {symbols_text}. Let me verify that I have everything needed.",
                "progress": 75,
            }

            # Phase 3: Review & Supplement
            yield {
                "type": "step",
                "step": "review",
                "message": "Reviewing collected data for completeness...",
                "reasoning": "Before providing my analysis, I want to make sure I have all the information necessary to answer your question thoroughly.",
                "progress": 80,
            }

            additional_needed = self._review_and_supplement(state)

            if additional_needed.get("needed"):
                yield {
                    "type": "step",
                    "step": "additional_data",
                    "message": f"I need some additional data: {', '.join(additional_needed.get('tools', []))}",
                    "reasoning": additional_needed.get(
                        "reasoning",
                        "After reviewing what I have, I realize I need a bit more data to provide a complete analysis",
                    ),
                    "progress": 85,
                }
                self._fetch_additional_data(state, additional_needed.get("tools", []))
            else:
                yield {
                    "type": "step",
                    "step": "review_complete",
                    "message": "Data review complete - I have sufficient information",
                    "reasoning": f"{additional_needed.get('reasoning', 'I have all the data I need to provide a comprehensive answer')}. Confidence level: {additional_needed.get('confidence', 'high')}",
                    "progress": 85,
                }

            # Phase 4: Final Analysis
            yield {
                "type": "step",
                "step": "generate_response",
                "message": "Analyzing the financial data and preparing my report...",
                "reasoning": "Now that I have all the necessary financial information, I am performing a detailed analysis to answer your question comprehensively.",
                "progress": 90,
            }

            state = self._generate_response_node(state)

            # Complete
            yield {
                "type": "complete",
                "step": "done",
                "message": "Analysis complete",
                "progress": 100,
                "data": {
                    "response": state["final_response"],
                    "symbols_analyzed": state["extracted_symbols"],
                    "stock_data": state["stock_data"],
                    "statement_data": state["statement_data"],
                    "analysis_results": state["analysis_results"],
                },
            }

        except Exception as e:
            logger.error(f"OptimizedAgent streaming error: {e}")
            yield {
                "type": "error",
                "message": f"I encountered an error: {str(e)}",
                "step": "error",
            }

    def _stream_parallel_execution(self, state: AgentState, plan: Dict[str, Any]):
        """Stream progress updates during parallel execution."""
        # Build task list
        fetch_tasks = []
        for symbol_plan in plan.get("symbols", []):
            symbol = symbol_plan["symbol"]
            data_needed = symbol_plan.get("data_needed", [])

            for data_type in data_needed:
                fetch_tasks.append(
                    {
                        "data_type": data_type,
                        "symbol": symbol,
                        "rationale": symbol_plan.get("rationale", ""),
                    }
                )

        total_tasks = len(fetch_tasks)
        completed = 0

        # Execute in parallel with progress updates
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}

            for task in fetch_tasks:
                future = executor.submit(
                    self._fetch_single_data, task["data_type"], task["symbol"]
                )
                futures[future] = task

            # Collect results and stream progress
            for future in as_completed(futures):
                task = futures[future]
                completed += 1
                progress = 30 + int((completed / total_tasks) * 45)

                try:
                    result = future.result(timeout=30)

                    # Store result
                    self._store_fetch_result(
                        state, task["data_type"], task["symbol"], result
                    )

                    # Generate conversational progress message
                    data_type_name = task["data_type"].replace("_", " ").title()

                    if result.get("error"):
                        yield {
                            "type": "tool_error",
                            "tool": task["data_type"],
                            "symbol": task["symbol"],
                            "message": f"Failed to retrieve {data_type_name} for {task['symbol']}",
                            "reasoning": f"I encountered an issue: {result.get('message', 'Unknown error')}. I will continue with the data I have.",
                            "progress": progress,
                        }
                    else:
                        # Extract key insight from the data
                        insight = self._extract_insight(
                            task["data_type"], result, task["symbol"]
                        )

                        yield {
                            "type": "tool_success",
                            "tool": task["data_type"],
                            "symbol": task["symbol"],
                            "message": f"Retrieved {data_type_name} for {task['symbol']}",
                            "reasoning": insight,
                            "progress": progress,
                        }

                        state["fetch_summary"].append(
                            f"✓ {task['data_type']} for {task['symbol']}"
                        )

                except Exception as e:
                    state["fetch_summary"].append(
                        f"✗ {task['data_type']} for {task['symbol']}: {str(e)}"
                    )

                    yield {
                        "type": "tool_error",
                        "tool": task["data_type"],
                        "symbol": task["symbol"],
                        "message": f"Error fetching {task['data_type']} for {task['symbol']}",
                        "reasoning": f"I encountered a technical error: {str(e)}. I will proceed with available data.",
                        "progress": progress,
                    }

    def _extract_insight(
        self, data_type: str, result: Dict[str, Any], symbol: str
    ) -> str:
        """Extract a conversational insight from fetched data."""
        try:
            if data_type == "stock_overview":
                market_cap = result.get("market_cap", 0)
                pe_ratio = result.get("pe_ratio", "N/A")
                name = result.get("name", symbol)
                return f"Now I have the company overview for {name}. Market capitalization is ${market_cap / 1e9:.1f}B with a P/E ratio of {pe_ratio}. This gives me the valuation context."

            elif data_type == "income_statement":
                income_data = result.get("data", result)
                if "annualReports" in income_data and income_data["annualReports"]:
                    latest = income_data["annualReports"][0]
                    revenue = float(latest.get("totalRevenue", 0)) / 1e9
                    net_income = float(latest.get("netIncome", 0)) / 1e9
                    return f"I have obtained the income statement. Revenue is ${revenue:.1f}B with net income of ${net_income:.1f}B. This shows me the profitability picture."
                return "I have retrieved the income statement data successfully."

            elif data_type == "balance_sheet":
                balance_data = result.get("data", result)
                if "annualReports" in balance_data and balance_data["annualReports"]:
                    latest = balance_data["annualReports"][0]
                    assets = float(latest.get("totalAssets", 0)) / 1e9
                    debt = float(latest.get("shortLongTermDebtTotal", 0)) / 1e9
                    return f"I have the balance sheet now. Total assets are ${assets:.1f}B with ${debt:.1f}B in debt. This tells me about the financial structure and leverage."
                return "I have retrieved the balance sheet data successfully."

            elif data_type == "cash_flow":
                cf_data = result.get("data", result)
                if "annualReports" in cf_data and cf_data["annualReports"]:
                    latest = cf_data["annualReports"][0]
                    op_cf = float(latest.get("operatingCashflow", 0)) / 1e9
                    return f"I have obtained the cash flow statement. Operating cash flow is ${op_cf:.1f}B, which reveals the company's cash generation capability."
                return "I have retrieved the cash flow data successfully."

            elif data_type == "earnings":
                earnings_data = result.get("data", result)
                if (
                    "quarterlyEarnings" in earnings_data
                    and earnings_data["quarterlyEarnings"]
                ):
                    latest = earnings_data["quarterlyEarnings"][0]
                    eps = latest.get("reportedEPS", "N/A")
            return f"I have successfully obtained the {data_type.replace('_', ' ')} data for {symbol}."

        except Exception:
            return (
                f"I have fetched the {data_type.replace('_', ' ')} data for {symbol}."
            )

    def _extract_data_insight(
        self, data_type: str, symbol: str, result: Dict[str, Any]
    ) -> str:
        """Extract a quick insight from fetched data."""
        try:
            if data_type == "stock_overview":
                market_cap = result.get("market_cap", 0)
                pe_ratio = result.get("pe_ratio", "N/A")
                return f"Got {symbol} overview: Market cap ${market_cap / 1e9:.1f}B, P/E {pe_ratio}. This gives me valuation context."

            elif data_type == "income_statement":
                income_data = result.get("data", result)
                if "annualReports" in income_data and income_data["annualReports"]:
                    latest = income_data["annualReports"][0]
                    revenue = float(latest.get("totalRevenue", 0)) / 1e9
                    return f"Retrieved {symbol} income: Revenue ${revenue:.1f}B. This shows profitability trends."

            elif data_type == "balance_sheet":
                balance_data = result.get("data", result)
                if "annualReports" in balance_data and balance_data["annualReports"]:
                    latest = balance_data["annualReports"][0]
                    assets = float(latest.get("totalAssets", 0)) / 1e9
                    return f"Got {symbol} balance sheet: Assets ${assets:.1f}B. This reveals financial strength."

            elif data_type == "cash_flow":
                cf_data = result.get("data", result)
                if "annualReports" in cf_data and cf_data["annualReports"]:
                    latest = cf_data["annualReports"][0]
                    op_cf = float(latest.get("operatingCashflow", 0)) / 1e9
                    return f"Retrieved {symbol} cash flow: Operating CF ${op_cf:.1f}B. Cash generation is key."

            elif data_type == "earnings":
                earnings_data = result.get("data", result)
                if (
                    "quarterlyEarnings" in earnings_data
                    and earnings_data["quarterlyEarnings"]
                ):
                    latest = earnings_data["quarterlyEarnings"][0]
                    eps = latest.get("reportedEPS", "N/A")
                    return f"Got {symbol} earnings: Latest EPS {eps}. This shows recent performance."

            return f"Retrieved {data_type.replace('_', ' ')} for {symbol}."

        except Exception:
            return f"Retrieved {data_type.replace('_', ' ')} for {symbol}."


def create_optimized_financial_agent() -> OptimizedFinancialAgent:
    """Factory function to create optimized agent."""
    logger.info("Creating OptimizedFinancialAgent")
    return OptimizedFinancialAgent()
