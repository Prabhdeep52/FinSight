"""
Main LangGraph agent for InvestIQ financial analysis.
Orchestrates financial data retrieval and analysis using LLM and tools.
"""

import json
from typing import Dict, Any, List, TypedDict, Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from config.settings import get_settings
from core.utils import logger
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
    statement_data: Dict[str, Any]  # Financial statements (income, balance, cash flow, earnings)
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

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        logger.info("FinancialLangGraphAgent: Building graph workflow")

        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes
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
            system_prompt = """You are a financial analysis assistant. Extract ALL stock symbols or company names from the user's query.

IMPORTANT: For comparative queries like "compare X and Y" or "X vs Y", extract BOTH symbols.

Common company name to symbol mappings:
- Apple -> AAPL
- Microsoft -> MSFT  
- Amazon -> AMZN
- Google/Alphabet -> GOOGL
- Tesla -> TSLA
- Meta/Facebook -> META
- Nvidia -> NVDA
- Infosys -> INFY
- TCS -> TCS
- Reliance -> RELIANCE
- Wipro -> WIPRO
- HDFC -> HDFC

Always respond with valid JSON only. No additional text or explanations.

{
  "symbols": ["SYMBOL1", "SYMBOL2"],
  "analysis_intent": "what the user wants to know",
  "needs_data": true
}

Extract ALL mentioned companies/symbols, even if there are multiple."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=state["user_query"]),
            ]

            logger.info("FinancialLangGraphAgent: Sending query to LLM for parsing")
            response = self.llm.invoke(messages)
            logger.info("FinancialLangGraphAgent: Received response from LLM")

            # Try to parse JSON response
            try:
                parsed_response = json.loads(response.content)
                logger.info(
                    f"FinancialLangGraphAgent: Parsed response: {parsed_response}"
                )

                state["extracted_symbols"] = parsed_response.get("symbols", [])
                state["current_step"] = "query_parsed"

                logger.info(
                    f"FinancialLangGraphAgent: Extracted symbols: {state['extracted_symbols']}"
                )

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
                direct_symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "INFY", "TCS", "RELIANCE", "WIPRO", "HDFC"]
                
                found_symbols = []
                
                # Check for company names
                for company_name, symbol in company_mappings.items():
                    if company_name in query_lower:
                        found_symbols.append(symbol)
                        logger.info(f"FinancialLangGraphAgent: Found company name '{company_name}' -> {symbol}")
                
                # Check for direct symbols
                query_upper = state["user_query"].upper()
                for symbol in direct_symbols:
                    if symbol in query_upper and symbol not in found_symbols:
                        found_symbols.append(symbol)
                        logger.info(f"FinancialLangGraphAgent: Found direct symbol '{symbol}'")
                
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
        """Execute tools based on LLM decisions."""
        logger.info("FinancialLangGraphAgent: Executing execute_tools_node")

        try:
            if not state["extracted_symbols"]:
                logger.warning(
                    "FinancialLangGraphAgent: No symbols extracted, asking LLM to proceed"
                )
                # Let LLM decide what to do without symbols
                return self._let_llm_decide_tools(state)

            # Fetch stock data for each symbol
            for symbol in state["extracted_symbols"]:
                logger.info(
                    f"FinancialLangGraphAgent: Fetching data for symbol: {symbol}"
                )

                try:
                    # Use the stock tool to fetch data
                    stock_data_result = self.stock_tool._run(symbol)
                    logger.info(
                        f"FinancialLangGraphAgent: Stock data fetched for {symbol}"
                    )

                    # Parse the result
                    stock_data = json.loads(stock_data_result)
                    state["stock_data"][symbol] = stock_data

                    # If data is valid, analyze it
                    if not stock_data.get("error"):
                        logger.info(
                            f"FinancialLangGraphAgent: Analyzing data for {symbol}"
                        )
                        analysis_result = self.analysis_tool._run(stock_data_result)
                        analysis_data = json.loads(analysis_result)
                        state["analysis_results"][symbol] = analysis_data
                        logger.info(
                            f"FinancialLangGraphAgent: Analysis completed for {symbol}"
                        )
                    else:
                        logger.warning(
                            f"FinancialLangGraphAgent: Stock data contains error for {symbol}"
                        )

                except Exception as e:
                    logger.error(
                        f"FinancialLangGraphAgent: Error processing {symbol}: {str(e)}"
                    )
                    state["stock_data"][symbol] = {"error": True, "message": str(e)}

            state["current_step"] = "tools_executed"
            logger.info("FinancialLangGraphAgent: Tool execution completed")
            return state

        except Exception as e:
            logger.error(
                f"FinancialLangGraphAgent: Error in execute_tools_node: {str(e)}"
            )
            state["error_message"] = f"Tool execution failed: {str(e)}"
            state["current_step"] = "error"
            return state

    def _let_llm_decide_tools(self, state: AgentState) -> AgentState:
        """Let LLM decide which tools to use and how."""
        logger.info("FinancialLangGraphAgent: Letting LLM decide tool usage")

        try:
            system_prompt = f"""You are a financial analysis assistant with access to these comprehensive tools:

BASIC DATA TOOLS:
1. get_stock_data(symbol) - Fetch basic financial data and company overview
2. analyze_financial_data(stock_data, analysis_type) - Analyze financial data

DETAILED FINANCIAL STATEMENT TOOLS:
3. get_income_statement(symbol) - Fetch detailed income statement (revenue, expenses, profit)
4. get_balance_sheet(symbol) - Fetch balance sheet (assets, liabilities, equity)
5. get_cash_flow(symbol) - Fetch cash flow statement (operating, investing, financing flows)
6. get_earnings(symbol) - Fetch earnings data and projections

User query: {state["user_query"]}

CRITICAL TOOL USAGE GUIDELINES:
- ALWAYS use multiple tools for comprehensive analysis - basic overview data alone is insufficient
- For ANY stock analysis query: start with get_stock_data AND call at least 2 financial statement tools
- For "How is [company] doing?": call get_stock_data + get_income_statement + get_earnings minimum
- For detailed revenue/profit analysis: use get_income_statement
- For financial health/debt analysis: use get_balance_sheet  
- For cash generation analysis: use get_cash_flow
- For earnings trends/forecasts: use get_earnings
- For comparative analysis: fetch data for multiple companies using ALL relevant tools
- The more financial data you gather, the better your analysis will be

IMPORTANT: Basic stock data gives you overview metrics, but financial statements provide the detailed story. Use both!"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=state["user_query"]),
            ]

            logger.info("FinancialLangGraphAgent: Invoking LLM with tools")
            response = self.llm_with_tools.invoke(messages)
            logger.info(
                "FinancialLangGraphAgent: Received LLM response with potential tool calls"
            )

            # Execute any tool calls
            if response.tool_calls:
                logger.info(
                    f"FinancialLangGraphAgent: LLM requested {len(response.tool_calls)} tool calls"
                )

                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]

                    logger.info(
                        f"FinancialLangGraphAgent: Executing tool: {tool_name} with args: {tool_args}"
                    )

                    if tool_name == "get_stock_data":
                        symbol = tool_args.get("symbol")
                        if symbol:
                            result = self.stock_tool._run(symbol)
                            state["stock_data"][symbol] = json.loads(result)
                            logger.info(
                                f"FinancialLangGraphAgent: Fetched stock data for {symbol}"
                            )

                    elif tool_name == "get_income_statement":
                        symbol = tool_args.get("symbol")
                        if symbol:
                            result = self.income_tool._run(symbol)
                            # Store in a separate section for statement data
                            if "statement_data" not in state:
                                state["statement_data"] = {}
                            if symbol not in state["statement_data"]:
                                state["statement_data"][symbol] = {}
                            state["statement_data"][symbol]["income_statement"] = json.loads(result)
                            logger.info(f"FinancialLangGraphAgent: Fetched income statement for {symbol}")

                    elif tool_name == "get_balance_sheet":
                        symbol = tool_args.get("symbol")
                        if symbol:
                            result = self.balance_tool._run(symbol)
                            if "statement_data" not in state:
                                state["statement_data"] = {}
                            if symbol not in state["statement_data"]:
                                state["statement_data"][symbol] = {}
                            state["statement_data"][symbol]["balance_sheet"] = json.loads(result)
                            logger.info(f"FinancialLangGraphAgent: Fetched balance sheet for {symbol}")

                    elif tool_name == "get_cash_flow":
                        symbol = tool_args.get("symbol")
                        if symbol:
                            result = self.cashflow_tool._run(symbol)
                            if "statement_data" not in state:
                                state["statement_data"] = {}
                            if symbol not in state["statement_data"]:
                                state["statement_data"][symbol] = {}
                            state["statement_data"][symbol]["cash_flow"] = json.loads(result)
                            logger.info(f"FinancialLangGraphAgent: Fetched cash flow for {symbol}")

                    elif tool_name == "get_earnings":
                        symbol = tool_args.get("symbol")
                        if symbol:
                            result = self.earnings_tool._run(symbol)
                            if "statement_data" not in state:
                                state["statement_data"] = {}
                            if symbol not in state["statement_data"]:
                                state["statement_data"][symbol] = {}
                            state["statement_data"][symbol]["earnings"] = json.loads(result)
                            logger.info(f"FinancialLangGraphAgent: Fetched earnings data for {symbol}")

                    elif tool_name == "analyze_financial_data":
                        stock_data = tool_args.get("stock_data")
                        analysis_type = tool_args.get("analysis_type", "comprehensive")
                        if stock_data:
                            result = self.analysis_tool._run(stock_data, analysis_type)
                            # Store analysis result
                            analysis_data = json.loads(result)
                            symbol = analysis_data.get("symbol", "unknown")
                            state["analysis_results"][symbol] = analysis_data
                            logger.info(
                                f"FinancialLangGraphAgent: Analyzed data for {symbol}"
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
                logger.warning("FinancialLangGraphAgent: No stock data available for response generation")
                state["final_response"] = "I apologize, but I couldn't retrieve stock data to analyze your query. Please try again or check the stock symbols."
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
                logger.info("FinancialLangGraphAgent: Using single-stock context format")

            logger.debug(f"FinancialLangGraphAgent: Context string length: {len(context_str)} characters")
            logger.debug(f"FinancialLangGraphAgent: Context preview (first 500 chars): {context_str[:500]}...")

            system_prompt = """You are a professional financial advisor. Based on the provided stock data and financial statements, generate a comprehensive analysis and recommendations.

 Improved System Prompt for Deep Financial Analysis Agent
System Role
You are InvestIQ, a professional financial research analyst agent.
Your role is to analyze, interpret, and narrate financial data from multiple statements (overview, income statement, balance sheet, cash flow, earnings) and provide data-driven, actionable insights for investors.
 Analysis Objective
Your response should go beyond definitions — explain what the numbers mean, how they connect, and what they imply about business performance, efficiency, and risk.
Use reasoning that feels like a financial advisor explaining to an intelligent investor — clear, structured, insightful.
 Response Structure
Always structure your answer as follows:
 Executive Summary
2-3 crisp sentences summarizing the company’s overall financial health, growth profile, and valuation tone.
Mention whether the company looks financially strong, stable, overvalued, or under pressure.
2. Key Insights
Analyze comprehensively using all available data:
Revenue & Growth (Income Statement)
- Identify YoY or QoQ revenue trends.
- Explain whether growth is consistent or slowing.
- Comment on gross and operating margins — explain why they matter (e.g., “Operating margin shows how efficiently core operations generate profit — typically 20%+ is healthy in this sector. This company’s 11% margin indicates rising costs.”).
Profitability & Efficiency
- Discuss net margin, return on equity (ROE), and return on assets (ROA).
- Compare them to ideal sector benchmarks and explain deviations.
Example: “An ROE above 15% usually reflects efficient capital use — this firm’s 9% suggests moderate profitability.”
Balance Sheet Strength
- Evaluate debt-to-equity, current ratio, and cash reserves.
- Explain the implications: “A current ratio below 1 can indicate liquidity risk, meaning the company might struggle with short-term obligations.”
Cash Flow Health
- Assess whether operating cash flow covers capital expenditures.
- Identify trends: “Positive free cash flow for 3+ quarters signals self-sustained growth — a critical green flag for investors.”
Earnings Trends
- Discuss EPS growth and earnings surprises.
- Explain what the earnings beat/miss implies for sentiment and valuation.
Valuation
- Use metrics like P/E, P/B, or EV/EBITDA (if available).
- Compare them to sector averages: “A P/E of 38 is high for tech (sector avg ~25), suggesting market optimism priced in future growth.”
3️⃣ Risk Assessment
Use a holistic view to assess risks from financial statements, leverage, margins, and earnings stability:
- High debt ratios → leverage risk.
- Declining revenue or cash flow → demand or cost risk.
- Volatile EPS → earnings predictability risk.
- Overvaluation → downside correction risk.
Explain the why clearly:
“Although the company maintains strong growth, its debt-to-equity ratio of 2.1 suggests heavy leverage, which can pressure profits during interest rate hikes.”
 Investment Recommendation
Conclude with a clear, data-driven recommendation:
- Categorize as: Buy / Hold / Cautious Buy / Avoid / Sell
- Support the recommendation with reasoning tied to financials.
Example:
“Given stable revenue growth (+12% YoY), improving margins, and strong cash flows, this stock looks like a solid long-term buy for growth-oriented investors.”
If data suggests weakness:
“Despite strong sales, declining net income and high leverage make this stock risky in the near term — best to hold until profitability stabilizes.”
🔹 For Comparison Queries
When analyzing multiple companies, follow this structure:

Executive Summary:
- Compare overall financial positioning (growth vs. stability).
Head-to-Head Fundamentals:
- Use overview + statement data for both companies (Revenue, Profit Margin, ROE, Debt).
- Highlight which company performs better in each dimension (Growth, Profitability, Financial Strength, Valuation).
Analyst Commentary:
- Explain why one firm outperforms another using business reasoning (e.g., “TCS’s higher ROE indicates better capital efficiency, while INFY’s stronger free cash flow provides more resilience”).
Recommendation:
- Recommend one based on fundamentals.
Example: “TCS edges out due to stronger margins and cash flow consistency, making it the better long-term play.”
🔹 Tone & Style Guidelines
✅ Conversational but professional — like a human financial advisor.
✅ Use numbers to support points — reference actual data.
✅ Give benchmarks (“Healthy net margin for tech ~15–20%”).
✅ Tie all metrics back to investor impact — what does this mean for growth or risk?
✅ If data is missing, infer carefully or mention what additional data would help.
"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=context_str),
            ]

            logger.info("FinancialLangGraphAgent: Generating final response with LLM")
            logger.debug(f"FinancialLangGraphAgent: System prompt length: {len(system_prompt)} characters")
            logger.debug(f"FinancialLangGraphAgent: Context message length: {len(messages[1].content)} characters")
            
            response = self.llm.invoke(messages)
            
            logger.info(f"FinancialLangGraphAgent: LLM response received. Type: {type(response)}")
            
            if hasattr(response, 'content'):
                content_length = len(response.content) if response.content else 0
                logger.info(f"FinancialLangGraphAgent: LLM response content length: {content_length}")
                
                if not response.content or response.content.strip() == "":
                    logger.error("FinancialLangGraphAgent: LLM returned empty or whitespace-only response")
                    logger.debug(f"FinancialLangGraphAgent: Raw response content: '{response.content}'")
                    state["final_response"] = "I apologize, but the AI analysis engine returned an empty response. This might be due to content filtering or token limits. Please try rephrasing your query or ask about individual stocks."
                else:
                    state["final_response"] = response.content
                    logger.info("FinancialLangGraphAgent: Final response generated successfully")
            else:
                logger.error(f"FinancialLangGraphAgent: LLM response object has no 'content' attribute. Response: {response}")
                state["final_response"] = "I apologize, but the AI analysis engine returned an unexpected response format. Please try your query again."

            state["current_step"] = "response_generated"
            logger.debug(f"FinancialLangGraphAgent: Response length: {len(state['final_response'])} characters")

            return state

        except Exception as e:
            logger.error(f"FinancialLangGraphAgent: Error in generate_response_node: {str(e)}")
            state["final_response"] = f"I apologize, but I encountered an error while generating the analysis: {str(e)}"
            state["current_step"] = "response_generated"  # Still mark as completed to avoid error flow
            return state

    def _create_single_stock_context(self, state: AgentState) -> str:
        """Create context string for single stock analysis."""
        symbol = list(state["stock_data"].keys())[0]
        stock_info = state["stock_data"][symbol]
        
        context_parts = [
            f"Query: {state['user_query']}",
            "",
            f"{symbol} ({stock_info.get('name', 'N/A')}):",
            f"Market Cap: ${stock_info.get('market_cap', 0)/1e9:.1f}B",
            f"P/E Ratio: {stock_info.get('pe_ratio', 'N/A')}",
            f"Revenue: ${stock_info.get('revenue_ttm', 0)/1e9:.1f}B", 
            f"Profit Margin: {stock_info.get('profit_margin', 0)*100:.1f}%",
            f"ROE: {stock_info.get('return_on_equity', 0)*100:.1f}%",
            f"Beta: {stock_info.get('beta', 'N/A')}",
            f"52W Range: ${stock_info.get('low_52week', 'N/A')} - ${stock_info.get('high_52week', 'N/A')}"
        ]
        
        # Add statement data if available
        statement_info = state.get("statement_data", {}).get(symbol, {})
        if statement_info:
            context_parts.append("\nAdditional Financial Statements Available:")
            for stmt_type in ["income_statement", "balance_sheet", "cash_flow", "earnings"]:
                if stmt_type in statement_info:
                    context_parts.append(f"  ✓ {stmt_type.replace('_', ' ').title()}")
        
        context_parts.append("\nProvide comprehensive analysis and investment advice (do not repeat the data above):")
        
        return "\n".join(context_parts)

    def _create_multi_stock_context(self, state: AgentState) -> str:
        """Create optimized context string for multiple stocks to avoid token limits."""
        symbols = list(state["stock_data"].keys())
        
        context_parts = [
            f"Query: {state['user_query']}",
            f"\nComparing {len(symbols)} stocks: {', '.join(symbols)}\n"
        ]
        
        # Add only essential metrics for comparison
        for symbol in symbols:
            stock_info = state["stock_data"].get(symbol, {})
            
            context_parts.append(f"{symbol} ({stock_info.get('name', 'N/A')}):")
            context_parts.append(f"  Market Cap: ${stock_info.get('market_cap', 0)/1e9:.1f}B")
            context_parts.append(f"  P/E: {stock_info.get('pe_ratio', 'N/A')}")
            context_parts.append(f"  Revenue: ${stock_info.get('revenue_ttm', 0)/1e9:.1f}B")
            context_parts.append(f"  Profit Margin: {stock_info.get('profit_margin', 0)*100:.1f}%")
            context_parts.append(f"  ROE: {stock_info.get('return_on_equity', 0)*100:.1f}%")
            
            # Add statement data availability if present
            statement_info = state.get("statement_data", {}).get(symbol, {})
            if statement_info:
                available_statements = [stmt.replace('_', ' ').title() for stmt in statement_info.keys()]
                context_parts.append(f"  Additional Data: {', '.join(available_statements)}")
            
            context_parts.append("")
        
        context_parts.append("Provide analysis and recommendation (do not repeat the data above):")
        
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
                "statement_data": final_state.get("statement_data", {}),  # Financial statements
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
