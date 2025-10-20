"""
Optimized Autonomous Agent - Best of Both Worlds

Combines:
1. Autonomous tool selection (LLM decides via tool binding)
2. Intelligent batching (all tools fetched at once)
3. Minimal LLM calls (3-4 total instead of 12-15)

How it works:
- Phase 1: LLM autonomously creates a complete tool plan (1 call)
- Phase 2: Execute ALL tools in parallel (0 calls)
- Phase 3: LLM reviews and decides if more needed (1 call)
- Phase 4: Generate final response (1 call)

"""

import json
import re
import uuid
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from config.settings import get_settings
from core.utils import logger
import concurrent.futures

from agents.tools.stock_tool import create_stock_data_tool
from agents.tools.statement_tools import (
    create_income_statement_tool,
    create_balance_sheet_tool,
    create_cash_flow_tool,
    create_earnings_tool,
)
from core.memory_manager import HybridMemoryManager


class OptimizedAutonomousAgent:
    """
    Autonomous agent with intelligent batching.
    LLM autonomously decides tools, but we batch execution for efficiency.
    
    Total LLM calls: 3-4 (same as manual planning agent)
    """
    
    def __init__(self):
        """Initialize the optimized autonomous agent."""
        logger.info("OptimizedAutonomousAgent: Initializing")
        
        self.settings = get_settings()
        
        # Initialize memory manager with Supabase client
        logger.info("OptimizedAutonomousAgent: Setting up memory manager")
        from database.supabase_client import get_supabase_client
        supabase_client = get_supabase_client()
        self.memory = HybridMemoryManager(supabase_client)
        
        # Initialize LLM
        logger.info("OptimizedAutonomousAgent: Setting up Google Gemini LLM")
        self.llm = ChatGoogleGenerativeAI(
            model=self.settings.gemini_model,
            google_api_key=self.settings.google_api_key,
            temperature=0.1,
            max_tokens=self.settings.max_tokens,
        )
        
        # Initialize tools
        logger.info("OptimizedAutonomousAgent: Setting up tools")
        self.stock_tool = create_stock_data_tool()
        self.income_tool = create_income_statement_tool()
        self.balance_tool = create_balance_sheet_tool()
        self.cashflow_tool = create_cash_flow_tool()
        self.earnings_tool = create_earnings_tool()
        
        # Convert to StructuredTool for autonomous calling
        self.tools = self._create_structured_tools()
        
        # Bind tools to LLM for autonomous calling
        logger.info("OptimizedAutonomousAgent: Binding tools to LLM")
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Tool execution map
        self.tool_execution_map = {
            'get_stock_overview': self.stock_tool._run,
            'get_income_statement': self.income_tool._run,
            'get_balance_sheet': self.balance_tool._run,
            'get_cash_flow': self.cashflow_tool._run,
            'get_earnings': self.earnings_tool._run,
        }
        
        # Session-level data cache to avoid re-fetching in follow-up questions
        self.session_data_cache = {}  # {session_id: {symbol: {tool_name: data}}}
        logger.info("OptimizedAutonomousAgent: Session data cache initialized")
        
        logger.info("OptimizedAutonomousAgent: Initialization completed")
    
    def _create_structured_tools(self) -> List[StructuredTool]:
        """
        Convert our existing tools to LangChain StructuredTool format.
        This allows the LLM to autonomously call them via tool binding.
        """
        class StockSymbolInput(BaseModel):
            symbol: str = Field(description="Stock ticker symbol (e.g., AAPL, MSFT)")
        
        tools = [
            StructuredTool.from_function(
                func=self.stock_tool._run,
                name="get_stock_overview",
                description="Get stock market data: price, market cap, P/E ratio, beta, 52-week range. Essential for valuation.",
                args_schema=StockSymbolInput
            ),
            StructuredTool.from_function(
                func=self.income_tool._run,
                name="get_income_statement",
                description="Get income statement: revenue, gross profit, net income, margins. Essential for profitability.",
                args_schema=StockSymbolInput
            ),
            StructuredTool.from_function(
                func=self.balance_tool._run,
                name="get_balance_sheet",
                description="Get balance sheet: assets, liabilities, debt, equity. Essential for financial health.",
                args_schema=StockSymbolInput
            ),
            StructuredTool.from_function(
                func=self.cashflow_tool._run,
                name="get_cash_flow",
                description="Get cash flow: operating cash flow, free cash flow. Essential for liquidity.",
                args_schema=StockSymbolInput
            ),
            StructuredTool.from_function(
                func=self.earnings_tool._run,
                name="get_earnings",
                description="Get quarterly earnings: EPS, surprises, guidance. Essential for recent performance.",
                args_schema=StockSymbolInput
            ),
        ]
        
        logger.info(f"OptimizedAutonomousAgent: Created {len(tools)} structured tools")
        return tools
    
    def process_query(self, user_query: str, session_id: str = None, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Process query using optimized autonomous approach with memory support.
        
        Key Optimization: Ask LLM for COMPLETE tool list, then execute at once.
        No infinite looping - just 1 planning call, execute, 1 review, 1 final.
        
        Args:
            user_query: User's question
            session_id: Optional session ID for conversation continuity
            user_id: User identifier for memory persistence
        """
        logger.info(f"OptimizedAutonomousAgent: Processing query: {user_query}")
        
        try:
            # Get or create session (restores context from DB if returning to old chat)
            session_data = self.memory.get_or_create_session(session_id, user_id)
            session_id = session_data['session_id']
            
            # Build context for follow-up questions
            context = self.memory.build_short_term_context(session_id)
            if context:
                logger.info(f"OptimizedAutonomousAgent: Using conversation context ({len(context)} chars)")
            
            state = {
                "user_query": user_query,
                "extracted_symbols": [],
                "stock_data": {},
                "statement_data": {},
                "final_response": "",
                "fetch_summary": [],
                "session_id": session_id
            }
            
            # Phase 1: Autonomous Planning (1 LLM call) - with context for follow-ups
            logger.info("OptimizedAutonomousAgent: PHASE 1 - Autonomous planning")
            tool_plan, plan_reasoning = self._autonomous_planning_phase(user_query, context)
            
            if not tool_plan:
                logger.warning("OptimizedAutonomousAgent: No tools requested, generating direct response")
                state['final_response'] = self._generate_direct_response(user_query)
                
                # Save user query and assistant response to memory
                self.memory.save_message(session_id, "user", user_query, metadata={})
                self.memory.save_message(session_id, "assistant", state['final_response'], metadata={})
                
                return self._success_response(state)
            
            # Extract symbols from plan
            state['extracted_symbols'] = self._extract_symbols_from_plan(tool_plan)
            logger.info(f"OptimizedAutonomousAgent: Identified symbols: {state['extracted_symbols']}")
            
            # Phase 2: Batch Execution (0 LLM calls - just execute)
            logger.info(f"OptimizedAutonomousAgent: PHASE 2 - Executing {len(tool_plan)} tools in parallel")
            self._execute_tool_batch_parallel(tool_plan, state)
            
            # Phase 3: Review & Supplement (1 LLM call)
            logger.info("OptimizedAutonomousAgent: PHASE 3 - Reviewing completeness")
            additional_needed = self._review_with_metadata(state)
            
            if additional_needed['needed'] and additional_needed.get('tools'):
                logger.info(f"OptimizedAutonomousAgent: Fetching additional: {additional_needed['tools']}")
                additional_plan = self._plan_additional_tools(state, additional_needed['tools'])
                if additional_plan:
                    self._execute_tool_batch_parallel(additional_plan, state)
            
            # Phase 4: Final Response (1 LLM call)
            logger.info("OptimizedAutonomousAgent: PHASE 4 - Generating final analysis")
            state['final_response'] = self._generate_final_response(state)
            
            # Save conversation to memory
            query_type = self._classify_query_type(user_query)
            tools_used = [call['name'] for call in tool_plan]
            
            user_metadata = {
                "symbols": state['extracted_symbols'],
                "query_type": query_type,
                "tools_requested": tools_used
            }
            
            assistant_metadata = {
                "symbols": state['extracted_symbols'],
                "tools_used": tools_used
            }
            
            self.memory.save_message(session_id, "user", user_query, user_metadata)
            self.memory.save_message(session_id, "assistant", state['final_response'], assistant_metadata)
            
            return self._success_response(state)
        
        except Exception as e:
            logger.error(f"OptimizedAutonomousAgent: Error: {e}")
            return self._error_response(user_query, str(e))
    
    def _autonomous_planning_phase(self, user_query: str, context: str = "") -> tuple[List[Dict], str]:
        """
        Phase 1: Ask LLM to autonomously decide ALL tools it needs.
        
        Key: We use a special system prompt that forces LLM to think ahead
        and request ALL tools at once, not one-by-one.
        
        Args:
            user_query: Current user question
            context: Conversation context for follow-up questions
        
        Returns: (list of tool calls, reasoning text from LLM)
        """
        planning_system_prompt = """You are InvestIQ planning data collection.

**FIRST: Explain your reasoning in 1-2 sentences:**
- What type of query is this?
- What specific data do you need and WHY?

Example: "This is a comprehensive performance query for AAPL. I need all 5 data types to provide a complete picture: stock overview for valuation context, income statement for profitability metrics, balance sheet for financial health, cash flow for liquidity analysis, and earnings for recent performance trends."

**THEN: Request ALL tools you need in ONE response.**
Do NOT request tools one at a time. Think ahead and call everything you need NOW.

**Available Tools:**
- get_stock_overview(symbol) - Market data, valuation metrics
- get_income_statement(symbol) - Revenue, profits, margins
- get_balance_sheet(symbol) - Assets, debt, financial health
- get_cash_flow(symbol) - Cash generation, liquidity
- get_earnings(symbol) - Quarterly performance, EPS

**Strategy for Queries:**
- **"How is [stock]" or "performance"**: ALL 5 tools (comprehensive picture)
- **Comparison**: ALL 5 tools for ALL stocks (fair comparison)
- **Valuation**: Overview + Income + Balance (need debt for multiples)
- **Earnings focus**: Earnings + Income only
- **Financial health**: Balance + Cash Flow only
- **Quick check**: Overview only

**Process:**
1. FIRST: Explain your reasoning (1-2 sentences)
2. THEN: Call ALL necessary tools RIGHT NOW

Remember: Explain first, then call all tools NOW!"""
        
        try:
            # Build query with context for follow-ups
            query_with_context = f"Query: {user_query}"
            if context:
                query_with_context = f"{context}\n\nCurrent Query: {user_query}"
            
            query_with_context += "\n\nExplain your reasoning, then call ALL necessary tools NOW."
            
            # Ask LLM with tool binding to autonomously generate tool calls
            response = self.llm_with_tools.invoke([
                SystemMessage(content=planning_system_prompt),
                HumanMessage(content=query_with_context)
            ])
            
            # Extract both tool calls AND reasoning
            tool_calls = response.tool_calls if response.tool_calls else []
            reasoning = response.content if response.content else "Planning data collection strategy."
            
            if tool_calls:
                logger.info(f"OptimizedAutonomousAgent: LLM autonomously requested {len(tool_calls)} tools")
                logger.info(f"OptimizedAutonomousAgent: LLM reasoning: {reasoning[:100]}...")
            else:
                logger.warning("OptimizedAutonomousAgent: LLM did not request any tools")
            
            return tool_calls, reasoning
        
        except Exception as e:
            logger.error(f"Error in autonomous planning: {e}")
            return [], "Error in planning phase."
    
    def _extract_symbols_from_plan(self, tool_plan: List[Dict]) -> List[str]:
        """Extract unique symbols from tool calls."""
        symbols = set()
        for tool_call in tool_plan:
            symbol = tool_call.get('args', {}).get('symbol', '')
            if symbol:
                symbols.add(symbol.upper())
        return sorted(list(symbols))
    
    def _get_tool_purpose(self, tool_name: str) -> str:
        """
        Explain why we need this tool - used in streaming announcements.
        Returns a short phrase describing the tool's purpose.
        """
        purposes = {
            'get_stock_overview': 'the current valuation and market position',
            'get_income_statement': 'profitability and revenue trends',
            'get_balance_sheet': 'financial health and leverage',
            'get_cash_flow': 'cash generation and liquidity',
            'get_earnings': 'recent performance and earnings momentum'
        }
        return purposes.get(tool_name, 'this financial data')
    
    def _execute_tool_batch_parallel(self, tool_calls: List[Dict], state: Dict):
        """
        Execute tool calls in parallel with ThreadPoolExecutor.
        This is the key optimization - all tools run simultaneously.
        """
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                symbol = tool_call["args"].get("symbol", "").upper()
                
                executor_func = self.tool_execution_map.get(tool_name)
                if executor_func:
                    future = executor.submit(executor_func, symbol)
                    futures[future] = (tool_name, symbol)
                else:
                    logger.warning(f"Unknown tool: {tool_name}")
            
            # Collect results as they complete
            for future in as_completed(futures):
                tool_name, symbol = futures[future]
                
                try:
                    result = future.result(timeout=30)
                    self._store_tool_result(state, tool_name, symbol, result)
                    
                    # Add to fetch summary for review phase
                    data_type = tool_name.replace('get_', '').replace('_', ' ')
                    state['fetch_summary'].append(f"{data_type} for {symbol}")
                    
                    logger.info(f"OptimizedAutonomousAgent: Completed {tool_name}({symbol})")
                
                except Exception as e:
                    logger.error(f"OptimizedAutonomousAgent: Error {tool_name}({symbol}): {e}")
    
    def _store_tool_result(self, state: Dict, tool_name: str, symbol: str, result: str):
        """Store tool result in state for final response generation."""
        try:
            result_data = json.loads(result) if isinstance(result, str) else result
            
            # Don't store error results
            if result_data.get('error'):
                logger.warning(f"Tool {tool_name}({symbol}) returned error")
                return
            
            if tool_name == 'get_stock_overview':
                state['stock_data'][symbol] = result_data
            else:
                # Store statement data
                if symbol not in state['statement_data']:
                    state['statement_data'][symbol] = {}
                
                data_type = tool_name.replace('get_', '')
                state['statement_data'][symbol][data_type] = result_data
        
        except Exception as e:
            logger.error(f"Error storing result for {tool_name}({symbol}): {e}")
    
    def _review_with_metadata(self, state: Dict) -> Dict[str, Any]:
        """
        Phase 3: Show LLM what was fetched (metadata only) and ask if sufficient.
        Only shows summaries to prevent token explosion.
        """
        symbols = state['extracted_symbols']
        user_query = state['user_query']
        fetch_summary = state['fetch_summary']
        
        review_prompt = f"""
You fetched financial data for: {', '.join(symbols)}

Original query: "{user_query}"

**What was fetched:**
{chr(10).join(fetch_summary)}

**Available in state:**
- Stock overviews: {list(state['stock_data'].keys())}
- Statements: {list(state['statement_data'].keys())}

**AVAILABLE TOOLS (you can ONLY request these):**
1. get_stock_overview
2. get_income_statement
3. get_balance_sheet
4. get_cash_flow
5. get_earnings

**Question:** Is this SUFFICIENT to answer the query comprehensively?

Return JSON:
{{
  "needed": true/false,
  "reasoning": "brief 1-2 sentence explanation",
  "tools": ["tool_name"],  // ONLY from the 5 tools above, ONLY if needed=true
  "confidence": "high|medium|low"
}}

Be honest - only request more if truly necessary from available tools."""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content="Review data completeness. Be concise."),
                HumanMessage(content=review_prompt)
            ])
            
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                review = json.loads(json_match.group())
                
                # Validate requested tools exist
                requested_tools = review.get('tools', [])
                valid_tools = [t for t in requested_tools if t in self.tool_execution_map]
                
                if len(valid_tools) < len(requested_tools):
                    invalid = set(requested_tools) - set(valid_tools)
                    logger.warning(f"LLM requested invalid tools: {invalid}. Ignoring.")
                    review['tools'] = valid_tools
                    review['needed'] = len(valid_tools) > 0
                
                logger.info(f"Review: needed={review.get('needed', False)}, confidence={review.get('confidence', 'unknown')}")
                return review
            
            return {"needed": False, "reasoning": "Sufficient data available", "confidence": "high"}
        
        except Exception as e:
            logger.error(f"Review error: {e}")
            return {"needed": False, "reasoning": "Error in review", "confidence": "low"}
    
    def _plan_additional_tools(self, state: Dict, tool_names: List[str]) -> List[Dict]:
        """
        Create tool calls for additional data needed from review phase.
        Only creates calls for symbols we're analyzing.
        """
        additional_calls = []
        
        for symbol in state['extracted_symbols']:
            for tool_name in tool_names:
                # Validate tool exists
                if tool_name not in self.tool_execution_map:
                    logger.warning(f"Skipping invalid tool: {tool_name}")
                    continue
                
                # Check if we already have this data
                if tool_name == 'get_stock_overview':
                    if symbol in state['stock_data']:
                        logger.info(f"Already have stock_overview for {symbol}, skipping")
                        continue
                else:
                    data_type = tool_name.replace('get_', '')
                    if symbol in state['statement_data'] and data_type in state['statement_data'][symbol]:
                        logger.info(f"Already have {data_type} for {symbol}, skipping")
                        continue
                
                additional_calls.append({
                    "name": tool_name,
                    "args": {"symbol": symbol},
                    "id": str(uuid.uuid4())
                })
        
        logger.info(f"Created {len(additional_calls)} additional tool calls")
        return additional_calls
    
    def _generate_final_response(self, state: Dict) -> str:
        """
        Phase 4: Generate final comprehensive response.
        Uses timeout to prevent hanging.
        """
        context = self._create_context(state)
        
        final_system_prompt = """You are InvestIQ. Generate a comprehensive financial analysis report in Markdown.

**Structure:**
## Executive Summary
Brief 2-3 sentence overview

## Key Insights
- Revenue & Growth
- Profitability Metrics
- Balance Sheet Health
- Cash Flow Analysis
- Earnings Performance
- Valuation Assessment

## Risk Assessment
Key risks and concerns

## Investment Recommendation
Clear recommendation with rationale
if some data is missing , dont write that section ,also if user is asking a general question then dont follow the structure , just ans the question directly. 
Use specific numbers from the data. Be thorough but concise."""
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self.llm.invoke,
                    [SystemMessage(content=final_system_prompt), HumanMessage(content=context)]
                )
                response = future.result(timeout=60)
            
            return response.content
        
        except concurrent.futures.TimeoutError:
            logger.error("Final response generation timed out")
            return "Error: Response generation timed out after 60 seconds."
        except Exception as e:
            logger.error(f"Error generating final response: {e}")
            return f"Error generating analysis: {str(e)}"
    
    def _create_context(self, state: Dict) -> str:
        """
        Create context string from collected data for final response generation.
        """
        symbols = state['extracted_symbols']
        user_query = state['user_query']
        
        if not symbols:
            return f"Query: {user_query}\n\nNo stock symbols identified."
        
        context_parts = [f"Query: {user_query}\n"]
        
        for symbol in symbols:
            stock_info = state['stock_data'].get(symbol, {})
            statement_info = state.get('statement_data', {}).get(symbol, {})
            
            context_parts.append(f"\n=== {symbol} - {stock_info.get('name', 'N/A')} ===")
            
            # Stock overview data
            if stock_info:
                context_parts.append(f"Market Cap: ${stock_info.get('market_cap', 0)/1e9:.1f}B")
                context_parts.append(f"Current Price: ${stock_info.get('price', 'N/A')}")
                context_parts.append(f"P/E Ratio: {stock_info.get('pe_ratio', 'N/A')}")
                context_parts.append(f"52W Range: ${stock_info.get('week_52_low', 'N/A')} - ${stock_info.get('week_52_high', 'N/A')}")
            
            # Income statement data
            if 'income_statement' in statement_info:
                income = statement_info['income_statement']
                income_data = income.get('data', income)
                if 'annualReports' in income_data and income_data['annualReports']:
                    latest = income_data['annualReports'][0]
                    context_parts.append(f"Revenue: ${float(latest.get('totalRevenue', 0))/1e9:.1f}B")
                    context_parts.append(f"Net Income: ${float(latest.get('netIncome', 0))/1e9:.1f}B")
                    context_parts.append(f"Gross Profit Margin: {latest.get('grossProfitRatio', 'N/A')}")
            
            # Balance sheet data
            if 'balance_sheet' in statement_info:
                balance = statement_info['balance_sheet']
                balance_data = balance.get('data', balance)
                if 'annualReports' in balance_data and balance_data['annualReports']:
                    latest = balance_data['annualReports'][0]
                    context_parts.append(f"Total Assets: ${float(latest.get('totalAssets', 0))/1e9:.1f}B")
                    context_parts.append(f"Total Debt: ${float(latest.get('totalDebt', 0))/1e9:.1f}B")
                    context_parts.append(f"Cash: ${float(latest.get('cashAndCashEquivalentsAtCarryingValue', 0))/1e9:.1f}B")
            
            # Cash flow data
            if 'cash_flow' in statement_info:
                cashflow = statement_info['cash_flow']
                cashflow_data = cashflow.get('data', cashflow)
                if 'annualReports' in cashflow_data and cashflow_data['annualReports']:
                    latest = cashflow_data['annualReports'][0]
                    context_parts.append(f"Operating Cash Flow: ${float(latest.get('operatingCashflow', 0))/1e9:.1f}B")
                    context_parts.append(f"Free Cash Flow: ${float(latest.get('freeCashFlow', 0))/1e9:.1f}B")
            
            # Earnings data
            if 'earnings' in statement_info:
                earnings = statement_info['earnings']
                earnings_data = earnings.get('data', earnings)
                if 'quarterlyEarnings' in earnings_data and earnings_data['quarterlyEarnings']:
                    latest = earnings_data['quarterlyEarnings'][0]
                    context_parts.append(f"Latest EPS: ${latest.get('reportedEPS', 'N/A')}")
                    context_parts.append(f"EPS Surprise: ${latest.get('surprise', 'N/A')}")
        
        return "\n".join(context_parts)
    
    def _generate_direct_response(self, user_query: str) -> str:
        """Generate a direct response when no tools are needed."""
        try:
            response = self.llm.invoke([
                SystemMessage(content="You are InvestIQ, a financial analysis assistant."),
                HumanMessage(content=user_query)
            ])
            return response.content
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _success_response(self, state: Dict) -> Dict[str, Any]:
        """Format successful response."""
        return {
            "query": state['user_query'],
            "response": state['final_response'],
            "symbols_analyzed": state['extracted_symbols'],
            "stock_data": state['stock_data'],
            "statement_data": state['statement_data'],
            "status": "success",
            "error_message": None
        }
    
    def _error_response(self, query: str, error_msg: str) -> Dict[str, Any]:
        """Format error response."""
        return {
            "query": query,
            "response": f"I encountered an error while processing your request: {error_msg}",
            "symbols_analyzed": [],
            "stock_data": {},
            "statement_data": {},
            "status": "error",
            "error_message": error_msg
        }
    
    def stream_execution(self, user_query: str, session_id: str = None, user_id: str = "default_user"):
        """
        Stream execution with progress updates and memory support.
        Yields events for frontend sidebar display.
        
        Args:
            user_query: User's question
            session_id: Optional session ID for conversation continuity
            user_id: User identifier for memory persistence
        """
        try:
            # Get or create session
            logger.info(f"stream_execution: Starting with session_id={session_id}, user_id={user_id}")
            session_data = self.memory.get_or_create_session(session_id, user_id)
            logger.info(f"stream_execution: Session data received: {session_data}")
            session_id = session_data['session_id']
            
            # Build context for follow-up questions
            logger.info(f"stream_execution: Building context for session {session_id}")
            context = self.memory.build_short_term_context(session_id)
            logger.info(f"stream_execution: Context built successfully")
            
 
            # Initialize
            yield {
                'type': 'step',
                'step': 'initialize',
                'message': 'Initializing autonomous agent with intelligent batching...',
                'reasoning': 'I am setting up the agent with autonomous tool calling capability. The AI will independently decide which tools to use based on your question.',
                'progress': 5
            }
           
            
            state = {
                "user_query": user_query,
                "extracted_symbols": [],
                "stock_data": {},
                "statement_data": {},
                "fetch_summary": [],
                "session_id": session_id
            }
            
            # Phase 1: Autonomous Planning
            yield {
                'type': 'step',
                'step': 'planning',
                'message': 'Agent is autonomously planning data collection...',
                'reasoning': 'The AI is analyzing your question and deciding which financial data it needs.',
                'progress': 15
            }
            
            tool_plan, plan_reasoning = self._autonomous_planning_phase(user_query, context)
            
            if not tool_plan:
                yield {
                    'type': 'step',
                    'step': 'no_tools',
                    'message': 'No financial data needed for this query',
                    'reasoning': 'The AI determined it can answer your question directly without fetching financial data.',
                    'progress': 50
                }
                
                final_response = self._generate_direct_response(user_query)
                
                yield {
                    'type': 'complete',
                    'step': 'done',
                    'message': 'Analysis complete',
                    'progress': 100,
                    'data': {
                        'response': final_response,
                        'symbols_analyzed': [],
                        'stock_data': {},
                        'statement_data': {}
                    }
                }
                return
            
            # Extract symbols
            state['extracted_symbols'] = self._extract_symbols_from_plan(tool_plan)
            
            # Stream the REAL LLM reasoning from planning phase
            yield {
                'type': 'step',
                'step': 'plan_ready',
                'message': f'Autonomous planning complete - will fetch {len(tool_plan)} data points',
                'reasoning': plan_reasoning,  # ✅ REAL LLM REASONING!
                'progress': 25
            }
            
            # Phase 2: Parallel Execution (with session caching)
            # Check session cache first
            tools_to_execute = []
            cached_tools = []
            
            for tool_call in tool_plan:
                tool_name = tool_call["name"]
                symbol = tool_call["args"].get("symbol", "").upper()
                
                # Check if data exists in session cache
                if self._is_data_in_session_cache(session_id, symbol, tool_name):
                    cached_tools.append((tool_name, symbol))
                    # Use cached data
                    cached_data = self._get_from_session_cache(session_id, symbol, tool_name)
                    self._store_tool_result(state, tool_name, symbol, json.dumps(cached_data))
                    data_type = tool_name.replace('get_', '').replace('_', ' ')
                    state['fetch_summary'].append(f"{data_type} for {symbol} (from session cache)")
                    logger.info(f"Session cache HIT: {tool_name}({symbol})")
                else:
                    tools_to_execute.append(tool_call)
            
            # Show cache info if any
            if cached_tools:
                cached_symbols = set([sym for _, sym in cached_tools])
                yield {
                    'type': 'step',
                    'step': 'cache_hit',
                    'message': f'Using cached data from earlier in this conversation',
                    'reasoning': f'I already have data for {", ".join(cached_symbols)} from our previous exchange, so I won\'t fetch it again. This saves time and API calls!',
                    'progress': 28
                }
            
            if not tools_to_execute:
                yield {
                    'type': 'step',
                    'step': 'all_cached',
                    'message': 'All required data already available from this conversation',
                    'reasoning': f'I already have all the data I need from our earlier exchange. No new API calls needed - proceeding directly to analysis!',
                    'progress': 70
                }
            else:
                yield {
                    'type': 'step',
                    'step': 'executing',
                    'message': f'Fetching {len(tools_to_execute)} new data points ({len(cached_tools)} from cache)...',
                    'reasoning': f'I already have {len(cached_tools)} pieces of data from our conversation. Now fetching {len(tools_to_execute)} new data points in parallel.',
                    'progress': 30
                }
                
                # Execute remaining tools with progress updates
                completed = 0
                total = len(tools_to_execute)
                
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = {}
                    
                    for tool_call in tools_to_execute:
                        tool_name = tool_call["name"]
                        symbol = tool_call["args"].get("symbol", "").upper()
                        
                        executor_func = self.tool_execution_map.get(tool_name)
                        if executor_func:
                            future = executor.submit(executor_func, symbol)
                            futures[future] = (tool_name, symbol)
                    
                    for future in as_completed(futures):
                        tool_name, symbol = futures[future]
                        completed += 1
                        
                        try:
                            result = future.result(timeout=30)
                            self._store_tool_result(state, tool_name, symbol, result)
                            
                            # Store in session cache for future queries
                            try:
                                result_data = json.loads(result) if isinstance(result, str) else result
                                if not result_data.get('error'):
                                    self._add_to_session_cache(session_id, symbol, tool_name, result_data)
                                    logger.info(f"Session cache STORED: {tool_name}({symbol})")
                            except Exception as cache_error:
                                logger.warning(f"Failed to cache {tool_name}({symbol}): {cache_error}")
                            
                            data_type = tool_name.replace('get_', '').replace('_', ' ')
                            state['fetch_summary'].append(f"{data_type} for {symbol}")
                            
                            # Extract insight
                            insight = self._extract_insight(tool_name, result, symbol)
                            
                            yield {
                                'type': 'tool_success',
                                'tool': tool_name,
                                'symbol': symbol,
                                'message': f'Retrieved {data_type} for {symbol}',
                                'reasoning': insight,
                                'progress': 30 + int((completed / total) * 40)
                            }
                        
                        except Exception as e:
                            data_type = tool_name.replace('get_', '').replace('_', ' ')
                            
                            yield {
                                'type': 'tool_error',
                                'tool': tool_name,
                                'symbol': symbol,
                                'message': f'Failed to fetch {data_type} for {symbol}',
                                'reasoning': f'Encountered an error: {str(e)}',
                                'progress': 30 + int((completed / total) * 40)
                            }
            
            yield {
                'type': 'step',
                'step': 'execution_complete',
                'message': 'Data collection complete',
                'reasoning': f'I have successfully gathered {len(state["fetch_summary"])} pieces of financial data. Now I will review if this is sufficient.',
                'progress': 70
            }
            
            # Phase 3: Review & Supplement
            yield {
                'type': 'step',
                'step': 'review',
                'message': 'Reviewing collected data for completeness...',
                'reasoning': 'I am analyzing what data I have collected to ensure it is sufficient to answer your question comprehensively.',
                'progress': 75
            }
            
            additional_needed = self._review_with_metadata(state)
            
            if additional_needed['needed'] and additional_needed.get('tools'):
                # Show full LLM reasoning (don't truncate)
                reasoning = additional_needed.get('reasoning', 'Additional data needed for comprehensive analysis.')
                
                yield {
                    'type': 'step',
                    'step': 'additional_data',
                    'message': f'Fetching additional data: {", ".join(additional_needed["tools"])}',
                    'reasoning': reasoning,  # ✅ FULL LLM REASONING
                    'progress': 80
                }
                
                additional_plan = self._plan_additional_tools(state, additional_needed['tools'])
                if additional_plan:
                    self._execute_tool_batch_parallel(additional_plan, state)
                    
                    yield {
                        'type': 'step',
                        'step': 'additional_complete',
                        'message': f'Fetched {len(additional_plan)} additional data points',
                        'reasoning': 'I have obtained the supplementary data needed for a complete analysis.',
                        'progress': 85
                    }
            else:
                # Show full LLM reasoning (don't truncate)
                reasoning = additional_needed.get('reasoning', 'I have all the necessary data for comprehensive analysis.')
                
                yield {
                    'type': 'step',
                    'step': 'review_complete',
                    'message': 'Data review complete - sufficient information gathered',
                    'reasoning': reasoning,  # ✅ FULL LLM REASONING
                    'progress': 85
                }
            
            # Phase 4: Final Response
            yield {
                'type': 'step',
                'step': 'generate_response',
                'message': 'Generating comprehensive financial analysis...',
                'reasoning': f'I have autonomously gathered all necessary data for {len(state["extracted_symbols"])} stock(s). Now I am analyzing everything to provide you with a detailed answer.',
                'progress': 90
            }
            
            final_response = self._generate_final_response(state)
            
            # Save conversation to memory
            query_type = self._classify_query_type(user_query)
            tools_used = [call['name'] for call in tool_plan] if tool_plan else []
            
            user_metadata = {
                "symbols": state['extracted_symbols'],
                "query_type": query_type,
                "tools_requested": tools_used
            }
            
            assistant_metadata = {
                "symbols": state['extracted_symbols'],
                "tools_used": tools_used,
                "stock_data": state['stock_data'],
                "statement_data": state['statement_data']
            }
            
            self.memory.save_message(session_id, "user", user_query, user_metadata)
            self.memory.save_message(session_id, "assistant", final_response, assistant_metadata)
            
            yield {
                'type': 'complete',
                'step': 'done',
                'message': 'Analysis complete',
                'progress': 100,
                'data': {
                    'response': final_response,
                    'symbols_analyzed': state['extracted_symbols'],
                    'stock_data': state['stock_data'],
                    'statement_data': state['statement_data'],
                    'session_id': session_id
                }
            }
        
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Full traceback: {error_details}")
            yield {
                'type': 'error',
                'message': f"{str(e)} | {error_details[:500]}",
                'step': 'error',
                'progress': 0
            }
    
    def _extract_insight(self, tool_name: str, result: str, symbol: str) -> str:
        """
        Extract a brief conversational insight from tool result with interpretation.
        Used for streaming progress updates.
        """
        try:
            result_data = json.loads(result) if isinstance(result, str) else result
            
            if result_data.get('error'):
                return f"Encountered an issue fetching data for {symbol}."
            
            if tool_name == 'get_stock_overview':
                market_cap = result_data.get('market_cap', 0)
                pe_ratio = result_data.get('pe_ratio', 'N/A')
                beta = result_data.get('beta', 'N/A')
                
                # Add interpretation
                valuation_note = ""
                if pe_ratio != 'N/A' and isinstance(pe_ratio, (int, float)):
                    if pe_ratio > 30:
                        valuation_note = " This shows premium valuation."
                    elif pe_ratio < 15:
                        valuation_note = " This indicates value pricing."
                
                return f"Market cap ${market_cap/1e9:.1f}B, P/E {pe_ratio}, Beta {beta}.{valuation_note}"
            
            elif tool_name == 'get_income_statement':
                data = result_data.get('data', result_data)
                if 'annualReports' in data and data['annualReports']:
                    latest = data['annualReports'][0]
                    revenue = float(latest.get('totalRevenue', 0)) / 1e9
                    net_income = float(latest.get('netIncome', 0)) / 1e9
                    
                    # Calculate margin and add interpretation
                    margin = (net_income / revenue * 100) if revenue > 0 else 0
                    profit_note = ""
                    if margin > 20:
                        profit_note = " This shows strong profitability."
                    elif margin < 5:
                        profit_note = " This indicates tight margins."
                    
                    return f"Revenue ${revenue:.1f}B, Net Income ${net_income:.1f}B ({margin:.1f}% margin).{profit_note}"
                return f"I have obtained the income statement for {symbol}."
            
            elif tool_name == 'get_balance_sheet':
                data = result_data.get('data', result_data)
                if 'annualReports' in data and data['annualReports']:
                    latest = data['annualReports'][0]
                    assets = float(latest.get('totalAssets', 0)) / 1e9
                    debt = float(latest.get('totalDebt', 0)) / 1e9
                    
                    # Calculate leverage and add interpretation
                    debt_ratio = (debt / assets * 100) if assets > 0 else 0
                    health_note = ""
                    if debt_ratio < 20:
                        health_note = " This reveals strong financial health."
                    elif debt_ratio > 60:
                        health_note = " This indicates significant leverage."
                    
                    return f"Assets ${assets:.1f}B, Debt ${debt:.1f}B ({debt_ratio:.1f}% leverage).{health_note}"
                return f"I have obtained the balance sheet for {symbol}."
            
            elif tool_name == 'get_cash_flow':
                data = result_data.get('data', result_data)
                if 'annualReports' in data and data['annualReports']:
                    latest = data['annualReports'][0]
                    ocf = float(latest.get('operatingCashflow', 0)) / 1e9
                    fcf = float(latest.get('freeCashFlow', 0)) / 1e9
                    
                    # Add interpretation
                    cash_note = ""
                    if fcf > 0 and ocf > 0:
                        cash_note = " This shows strong cash generation."
                    elif fcf < 0:
                        cash_note = " This indicates cash consumption."
                    
                    return f"Operating CF ${ocf:.1f}B, Free CF ${fcf:.1f}B.{cash_note}"
                return f"I have obtained the cash flow statement for {symbol}."
            
            elif tool_name == 'get_earnings':
                return f"I have successfully obtained the earnings data for {symbol}."
            
            return f"Data retrieved successfully for {symbol}."
        
        except Exception as e:
            return f"Retrieved data for {symbol}."


    def _classify_query_type(self, query: str) -> str:
        """Classify query type for metadata storage."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['compare', 'versus', 'vs', 'better']):
            return 'comparison'
        elif any(word in query_lower for word in ['valuation', 'worth', 'value', 'p/e', 'pe ratio']):
            return 'valuation'
        elif any(word in query_lower for word in ['earnings', 'profit', 'revenue', 'income']):
            return 'earnings'
        elif any(word in query_lower for word in ['cash', 'liquidity', 'balance sheet', 'debt']):
            return 'financial_health'
        elif any(word in query_lower for word in ['how is', 'performance', 'analysis', 'overview']):
            return 'performance'
        else:
            return 'general'
    
    def _is_data_in_session_cache(self, session_id: str, symbol: str, tool_name: str) -> bool:
        """Check if data exists in session cache."""
        if not session_id or session_id not in self.session_data_cache:
            return False
        
        if symbol not in self.session_data_cache[session_id]:
            return False
        
        return tool_name in self.session_data_cache[session_id][symbol]
    
    def _get_from_session_cache(self, session_id: str, symbol: str, tool_name: str) -> Dict:
        """Get data from session cache."""
        return self.session_data_cache[session_id][symbol][tool_name]
    
    def _add_to_session_cache(self, session_id: str, symbol: str, tool_name: str, data: Dict):
        """Add data to session cache."""
        if not session_id:
            return
        
        if session_id not in self.session_data_cache:
            self.session_data_cache[session_id] = {}
        
        if symbol not in self.session_data_cache[session_id]:
            self.session_data_cache[session_id][symbol] = {}
        
        self.session_data_cache[session_id][symbol][tool_name] = data
        logger.debug(f"Added to session cache: {session_id}/{symbol}/{tool_name}")
    
    def clear_session_cache(self, session_id: str = None):
        """Clear session cache. Called when user starts a new chat."""
        if session_id:
            if session_id in self.session_data_cache:
                del self.session_data_cache[session_id]
                logger.info(f"Cleared session cache for {session_id}")
        else:
            self.session_data_cache.clear()
            logger.info("Cleared all session caches")


def create_optimized_autonomous_agent() -> OptimizedAutonomousAgent:
    """Factory function to create optimized autonomous agent."""
    logger.info("Creating OptimizedAutonomousAgent")
    return OptimizedAutonomousAgent()
