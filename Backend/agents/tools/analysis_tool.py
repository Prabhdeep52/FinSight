"""
Financial analysis tool for LangGraph agents.
Provides LLM with ability to analyze financial data and generate insights.
"""
import json
from typing import Dict, Any, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from core.utils import logger


class AnalysisInput(BaseModel):
    """Input schema for financial analysis tool."""
    stock_data: str = Field(
        description="JSON string containing stock financial data to analyze. "
                   "Should include metrics like price, market cap, P/E ratio, etc."
    )
    analysis_type: str = Field(
        default="comprehensive",
        description="Type of analysis to perform. Options: 'comprehensive', 'valuation', 'performance', 'risk'"
    )


class FinancialAnalysisTool(BaseTool):
    """
    Tool for analyzing financial data and generating insights.
    
    This tool takes stock financial data and provides detailed analysis
    including valuation assessment, performance metrics, and risk factors.
    """
    
    name: str = "analyze_financial_data"
    description: str = (
        "Analyze financial data and provide comprehensive insights. "
        "Use this tool after fetching stock data to generate meaningful analysis, "
        "interpretations, and recommendations based on financial metrics. "
        "Provides valuation assessment, performance analysis, and risk evaluation."
    )
    args_schema: Type[BaseModel] = AnalysisInput
    
    def _run(self, stock_data: str, analysis_type: str = "comprehensive") -> str:
        """
        Execute financial analysis on the provided stock data.
        
        Args:
            stock_data: JSON string containing financial metrics
            analysis_type: Type of analysis to perform
            
        Returns:
            JSON string containing analysis results and insights
        """
        logger.info(f"FinancialAnalysisTool: Starting {analysis_type} analysis")
        
        try:
            # Parse the stock data
            logger.info("FinancialAnalysisTool: Parsing input stock data")
            data = json.loads(stock_data) if isinstance(stock_data, str) else stock_data
            logger.debug(f"FinancialAnalysisTool: Parsed data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            if data.get('error'):
                logger.warning(f"FinancialAnalysisTool: Input data contains error: {data.get('message')}")
                return json.dumps({
                    "error": True,
                    "message": "Cannot analyze data with errors",
                    "input_error": data.get('message')
                }, indent=2)
            
            # Extract key metrics
            logger.info("FinancialAnalysisTool: Extracting key financial metrics")
            analysis_result = self._perform_analysis(data, analysis_type)
            
            logger.info(f"FinancialAnalysisTool: Analysis completed successfully for {analysis_type}")
            return json.dumps(analysis_result, indent=2)
            
        except json.JSONDecodeError as e:
            logger.error(f"FinancialAnalysisTool: JSON parsing error: {str(e)}")
            return json.dumps({
                "error": True,
                "message": f"Invalid JSON data provided: {str(e)}",
                "error_type": "JSONDecodeError"
            }, indent=2)
            
        except Exception as e:
            logger.error(f"FinancialAnalysisTool: Unexpected error during analysis: {str(e)}")
            return json.dumps({
                "error": True,
                "message": f"Analysis failed: {str(e)}",
                "error_type": "UnexpectedException"
            }, indent=2)
    
    def _perform_analysis(self, data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """
        Perform the actual financial analysis based on the data and analysis type.
        
        Args:
            data: Financial data dictionary
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis results dictionary
        """
        logger.info(f"FinancialAnalysisTool: Performing {analysis_type} analysis")
        
        # Extract basic information
        symbol = data.get('symbol', 'Unknown')
        name = data.get('name', 'Unknown Company')
        current_price = data.get('current_price')
        currency = data.get('currency', 'USD')
        
        logger.info(f"FinancialAnalysisTool: Analyzing {symbol} ({name})")
        
        # Base analysis structure
        analysis = {
            "symbol": symbol,
            "company_name": name,
            "analysis_type": analysis_type,
            "currency": currency,
            "current_price": current_price,
            "analysis_timestamp": "2025-10-15",  # In production, use actual timestamp
            "key_metrics": {},
            "insights": {},
            "risk_factors": [],
            "recommendations": []
        }
        
        # Extract and analyze key metrics
        logger.info("FinancialAnalysisTool: Extracting key metrics")
        analysis["key_metrics"] = self._extract_key_metrics(data)
        
        # Perform specific analysis based on type
        if analysis_type == "comprehensive" or analysis_type == "valuation":
            logger.info("FinancialAnalysisTool: Performing valuation analysis")
            analysis["insights"]["valuation"] = self._analyze_valuation(data)
        
        if analysis_type == "comprehensive" or analysis_type == "performance":
            logger.info("FinancialAnalysisTool: Performing performance analysis")
            analysis["insights"]["performance"] = self._analyze_performance(data)
        
        if analysis_type == "comprehensive" or analysis_type == "risk":
            logger.info("FinancialAnalysisTool: Performing risk analysis")
            analysis["risk_factors"] = self._analyze_risk_factors(data)
        
        # Generate recommendations
        logger.info("FinancialAnalysisTool: Generating recommendations")
        analysis["recommendations"] = self._generate_recommendations(data, analysis["insights"])
        
        logger.info("FinancialAnalysisTool: Analysis computation completed")
        return analysis
    
    def _extract_key_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize key financial metrics."""
        logger.debug("FinancialAnalysisTool: Extracting key financial metrics")
        
        metrics = {}
        
        # Basic metrics
        metrics["market_cap"] = data.get('market_cap')
        metrics["pe_ratio"] = data.get('pe_ratio')
        metrics["eps"] = data.get('eps')
        metrics["book_value"] = data.get('book_value')
        metrics["dividend_yield"] = data.get('dividend_yield')
        
        # Growth and profitability
        metrics["revenue_ttm"] = data.get('revenue_ttm')
        metrics["profit_margin"] = data.get('profit_margin')
        metrics["operating_margin"] = data.get('operating_margin')
        metrics["return_on_equity"] = data.get('return_on_equity')
        metrics["return_on_assets"] = data.get('return_on_assets')
        
        # Financial health
        metrics["debt_to_equity"] = data.get('debt_to_equity')
        metrics["beta"] = data.get('beta')
        
        # Price ranges
        metrics["high_52week"] = data.get('high_52week')
        metrics["low_52week"] = data.get('low_52week')
        
        logger.debug(f"FinancialAnalysisTool: Extracted {len([k for k, v in metrics.items() if v is not None])} non-null metrics")
        return metrics
    
    def _analyze_valuation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze valuation metrics."""
        logger.debug("FinancialAnalysisTool: Analyzing valuation metrics")
        
        valuation = {}
        pe_ratio = data.get('pe_ratio')
        pb_ratio = data.get('pb_ratio')
        market_cap = data.get('market_cap')
        
        # P/E Ratio analysis
        if pe_ratio:
            if pe_ratio < 15:
                valuation["pe_assessment"] = "Potentially undervalued based on P/E ratio"
            elif pe_ratio < 25:
                valuation["pe_assessment"] = "Fairly valued based on P/E ratio"
            else:
                valuation["pe_assessment"] = "Potentially overvalued based on P/E ratio"
        else:
            valuation["pe_assessment"] = "P/E ratio not available for analysis"
        
        # Market cap assessment
        if market_cap:
            if market_cap > 100000000000:  # >100B
                valuation["market_cap_category"] = "Large Cap (>$100B)"
            elif market_cap > 10000000000:  # >10B
                valuation["market_cap_category"] = "Large Cap ($10B-$100B)"
            elif market_cap > 2000000000:  # >2B
                valuation["market_cap_category"] = "Mid Cap ($2B-$10B)"
            else:
                valuation["market_cap_category"] = "Small Cap (<$2B)"
        
        logger.debug("FinancialAnalysisTool: Valuation analysis completed")
        return valuation
    
    def _analyze_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics."""
        logger.debug("FinancialAnalysisTool: Analyzing performance metrics")
        
        performance = {}
        
        # Profitability analysis
        profit_margin = data.get('profit_margin')
        if profit_margin:
            if profit_margin > 20:
                performance["profitability"] = "Excellent profit margins (>20%)"
            elif profit_margin > 10:
                performance["profitability"] = "Good profit margins (10-20%)"
            elif profit_margin > 5:
                performance["profitability"] = "Moderate profit margins (5-10%)"
            else:
                performance["profitability"] = "Low profit margins (<5%)"
        
        # ROE analysis
        roe = data.get('return_on_equity')
        if roe:
            if roe > 20:
                performance["roe_assessment"] = "Excellent return on equity (>20%)"
            elif roe > 15:
                performance["roe_assessment"] = "Good return on equity (15-20%)"
            elif roe > 10:
                performance["roe_assessment"] = "Moderate return on equity (10-15%)"
            else:
                performance["roe_assessment"] = "Low return on equity (<10%)"
        
        # 52-week performance
        current_price = data.get('current_price')
        high_52week = data.get('high_52week')
        low_52week = data.get('low_52week')
        
        if all([current_price, high_52week, low_52week]):
            price_position = (current_price - low_52week) / (high_52week - low_52week) * 100
            performance["52_week_position"] = f"Trading at {price_position:.1f}% of 52-week range"
        
        logger.debug("FinancialAnalysisTool: Performance analysis completed")
        return performance
    
    def _analyze_risk_factors(self, data: Dict[str, Any]) -> list:
        """Identify potential risk factors."""
        logger.debug("FinancialAnalysisTool: Analyzing risk factors")
        
        risks = []
        
        # High debt risk
        debt_to_equity = data.get('debt_to_equity')
        if debt_to_equity and debt_to_equity > 2:
            risks.append("High debt-to-equity ratio indicates financial leverage risk")
        
        # High beta risk
        beta = data.get('beta')
        if beta and beta > 1.5:
            risks.append("High beta indicates higher volatility than market")
        
        # High P/E risk
        pe_ratio = data.get('pe_ratio')
        if pe_ratio and pe_ratio > 30:
            risks.append("High P/E ratio suggests valuation risk")
        
        # Low liquidity risk (for small caps)
        market_cap = data.get('market_cap')
        if market_cap and market_cap < 1000000000:  # <1B
            risks.append("Small market cap may indicate liquidity risk")
        
        logger.debug(f"FinancialAnalysisTool: Identified {len(risks)} risk factors")
        return risks
    
    def _generate_recommendations(self, data: Dict[str, Any], insights: Dict[str, Any]) -> list:
        """Generate investment recommendations based on analysis."""
        logger.debug("FinancialAnalysisTool: Generating recommendations")
        
        recommendations = []
        
        # Based on valuation
        valuation = insights.get('valuation', {})
        pe_assessment = valuation.get('pe_assessment', '')
        
        if 'undervalued' in pe_assessment.lower():
            recommendations.append("Consider for value investment based on attractive P/E ratio")
        elif 'overvalued' in pe_assessment.lower():
            recommendations.append("Exercise caution due to high valuation metrics")
        
        # Based on performance
        performance = insights.get('performance', {})
        profitability = performance.get('profitability', '')
        
        if 'excellent' in profitability.lower():
            recommendations.append("Strong profitability metrics support investment thesis")
        elif 'low' in profitability.lower():
            recommendations.append("Monitor profitability improvements before investing")
        
        # Market cap based recommendations
        market_cap_category = valuation.get('market_cap_category', '')
        if 'Large Cap' in market_cap_category:
            recommendations.append("Large cap stock suitable for conservative portfolios")
        elif 'Small Cap' in market_cap_category:
            recommendations.append("Small cap stock carries higher risk but potential for growth")
        
        # Default recommendation if none generated
        if not recommendations:
            recommendations.append("Perform additional research and consider portfolio allocation")
        
        logger.debug(f"FinancialAnalysisTool: Generated {len(recommendations)} recommendations")
        return recommendations
    
    async def _arun(self, stock_data: str, analysis_type: str = "comprehensive") -> str:
        """Async version of the run method."""
        logger.info(f"FinancialAnalysisTool: Async execution requested for {analysis_type} analysis")
        # For now, use the sync version
        return self._run(stock_data, analysis_type)


def create_financial_analysis_tool() -> FinancialAnalysisTool:
    """
    Factory function to create a financial analysis tool.
    
    Returns:
        Configured FinancialAnalysisTool instance
    """
    logger.info("Creating FinancialAnalysisTool")
    tool = FinancialAnalysisTool()
    logger.info("FinancialAnalysisTool created successfully")
    return tool