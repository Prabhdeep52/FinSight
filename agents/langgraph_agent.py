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


class AgentState(TypedDict):
    """State management for the LangGraph agent using TypedDict."""

    messages: Annotated[List[Dict[str, Any]], add_messages]
    user_query: str
    extracted_symbols: List[str]
    stock_data: Dict[str, Any]
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
        self.tools = [self.stock_tool, self.analysis_tool]
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
            system_prompt = """You are a financial analysis assistant. Your task is to:
1. Understand the user's financial analysis request
2. Identify stock symbols mentioned in the query
3. Determine what type of analysis is needed

Extract stock symbols from the query. Stock symbols can be:
- US stocks: AAPL, GOOGL, MSFT, AMZN, TSLA, etc.
- Indian stocks: INFY, TCS, RELIANCE, WIPRO, HDFC, etc.
- Any stock symbol format

Respond with a JSON object containing:
- "symbols": list of stock symbols found
- "analysis_intent": description of what analysis the user wants
- "needs_data": boolean indicating if stock data is needed

Example response:
{
  "symbols": ["AAPL"],
  "analysis_intent": "comprehensive stock analysis",
  "needs_data": true
}"""

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
                    "FinancialLangGraphAgent: Failed to parse JSON, using fallback symbol extraction"
                )
                # Fallback: simple keyword extraction
                query_upper = state["user_query"].upper()
                common_symbols = [
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

                found_symbols = [
                    symbol for symbol in common_symbols if symbol in query_upper
                ]
                state["extracted_symbols"] = found_symbols
                logger.info(
                    f"FinancialLangGraphAgent: Fallback extraction found: {found_symbols}"
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
            system_prompt = f"""You are a financial analysis assistant with access to these tools:
1. get_stock_data(symbol) - Fetch financial data for any stock symbol
2. analyze_financial_data(stock_data, analysis_type) - Analyze financial data

User query: {state["user_query"]}

Please use the appropriate tools to help answer the user's question. If you need stock data for specific companies, use the get_stock_data tool first, then analyze the data using analyze_financial_data tool.

Think step by step about what information you need and which tools to use."""

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
                                f"FinancialLangGraphAgent: Fetched data for {symbol}"
                            )

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
            # Prepare context for response generation
            context = {
                "user_query": state["user_query"],
                "stock_data": state["stock_data"],
                "analysis_results": state["analysis_results"],
            }

            logger.info(
                "FinancialLangGraphAgent: Preparing response generation context"
            )
            logger.debug(
                f"FinancialLangGraphAgent: Context contains {len(state['stock_data'])} stock data entries and {len(state['analysis_results'])} analysis results"
            )

            system_prompt = """You are a professional financial analyst. Based on the stock data and analysis provided, generate a comprehensive, helpful response to the user's query.

Structure your response as follows:
1. Brief summary of the requested analysis
2. Key financial metrics and findings
3. Analysis insights and interpretation
4. Risk factors and considerations
5. Recommendations or conclusions

Make the response clear, informative, and actionable. Use professional financial terminology but explain complex concepts clearly."""

            # Create context string
            context_str = f"""
User Query: {state["user_query"]}

Stock Data Available: {json.dumps(state["stock_data"], indent=2)}

Analysis Results: {json.dumps(state["analysis_results"], indent=2)}
"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=f"Please provide a comprehensive response based on this context:\n\n{context_str}"
                ),
            ]

            logger.info("FinancialLangGraphAgent: Generating final response with LLM")
            response = self.llm.invoke(messages)

            state["final_response"] = response.content
            state["current_step"] = "response_generated"

            logger.info(
                "FinancialLangGraphAgent: Final response generated successfully"
            )
            logger.debug(
                f"FinancialLangGraphAgent: Response length: {len(state['final_response'])} characters"
            )

            return state

        except Exception as e:
            logger.error(
                f"FinancialLangGraphAgent: Error in generate_response_node: {str(e)}"
            )
            state["error_message"] = f"Response generation failed: {str(e)}"
            state["current_step"] = "error"
            return state

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
