import React, { useMemo } from "react";
import { OverviewCard } from "./sections/OverviewCard";
import { IncomeStatementTable } from "./sections/IncomeStatementTable";
import { BalanceSheetTable } from "./sections/BalanceSheetTable";
import { CashFlowTable } from "./sections/CashFlowTable";
import { EarningsTable } from "./sections/EarningsTable";
import {
  extractIncomeMetrics,
  extractBalanceSheetMetrics,
  extractCashFlowMetrics,
  extractEarningsData,
} from "./utils/metricExtractors";
import {
  compareHigherBetter,
  compareLowerBetter,
  type ComparisonResult,
} from "./utils/comparisonUtils";

interface Stock {
  symbol: string;
  stockData: Record<string, unknown>;
  statementData: Record<string, unknown>;
}

interface FinancialDashboardProps {
  stocks: Stock[];
}

export const FinancialDashboard: React.FC<FinancialDashboardProps> = ({
  stocks,
}) => {
  const isComparison = stocks.length === 2;

  // Extract metrics for each stock
  const stock1Metrics = useMemo(() => {
    if (stocks.length === 0) return null;
    return {
      income: extractIncomeMetrics(stocks[0].statementData),
      balance: extractBalanceSheetMetrics(stocks[0].statementData),
      cashFlow: extractCashFlowMetrics(stocks[0].statementData),
      earnings: extractEarningsData(stocks[0].statementData),
    };
  }, [stocks]);

  const stock2Metrics = useMemo(() => {
    if (stocks.length < 2) return null;
    return {
      income: extractIncomeMetrics(stocks[1].statementData),
      balance: extractBalanceSheetMetrics(stocks[1].statementData),
      cashFlow: extractCashFlowMetrics(stocks[1].statementData),
      earnings: extractEarningsData(stocks[1].statementData),
    };
  }, [stocks]);

  // Compute comparison results
  const comparisonResults = useMemo(() => {
    if (!isComparison || !stock1Metrics || !stock2Metrics) {
      return { stock1: {}, stock2: {} };
    }

    const stock1Results: Record<string, ComparisonResult> = {};
    const stock2Results: Record<string, ComparisonResult> = {};

    // Income statement comparisons (higher is better for most)
    const revenueComp = compareHigherBetter(
      stock1Metrics.income.revenue,
      stock2Metrics.income.revenue,
    );
    stock1Results.revenue = revenueComp.stock1Result;
    stock2Results.revenue = revenueComp.stock2Result;

    const grossMarginComp = compareHigherBetter(
      stock1Metrics.income.grossMargin,
      stock2Metrics.income.grossMargin,
    );
    stock1Results.grossMargin = grossMarginComp.stock1Result;
    stock2Results.grossMargin = grossMarginComp.stock2Result;

    const operatingMarginComp = compareHigherBetter(
      stock1Metrics.income.operatingMargin,
      stock2Metrics.income.operatingMargin,
    );
    stock1Results.operatingMargin = operatingMarginComp.stock1Result;
    stock2Results.operatingMargin = operatingMarginComp.stock2Result;

    const netMarginComp = compareHigherBetter(
      stock1Metrics.income.netMargin,
      stock2Metrics.income.netMargin,
    );
    stock1Results.netMargin = netMarginComp.stock1Result;
    stock2Results.netMargin = netMarginComp.stock2Result;

    const ebitdaComp = compareHigherBetter(
      stock1Metrics.income.ebitda,
      stock2Metrics.income.ebitda,
    );
    stock1Results.ebitda = ebitdaComp.stock1Result;
    stock2Results.ebitda = ebitdaComp.stock2Result;

    // Balance sheet comparisons
    const currentRatioComp = compareHigherBetter(
      stock1Metrics.balance.currentRatio,
      stock2Metrics.balance.currentRatio,
    );
    stock1Results.currentRatio = currentRatioComp.stock1Result;
    stock2Results.currentRatio = currentRatioComp.stock2Result;

    const debtToEquityComp = compareLowerBetter(
      stock1Metrics.balance.debtToEquity,
      stock2Metrics.balance.debtToEquity,
    );
    stock1Results.debtToEquity = debtToEquityComp.stock1Result;
    stock2Results.debtToEquity = debtToEquityComp.stock2Result;

    // Cash flow comparisons
    const fcfComp = compareHigherBetter(
      stock1Metrics.cashFlow.freeCashFlow,
      stock2Metrics.cashFlow.freeCashFlow,
    );
    stock1Results.freeCashFlow = fcfComp.stock1Result;
    stock2Results.freeCashFlow = fcfComp.stock2Result;

    const fcfMarginComp = compareHigherBetter(
      stock1Metrics.cashFlow.fcfMargin,
      stock2Metrics.cashFlow.fcfMargin,
    );
    stock1Results.fcfMargin = fcfMarginComp.stock1Result;
    stock2Results.fcfMargin = fcfMarginComp.stock2Result;

    return { stock1: stock1Results, stock2: stock2Results };
  }, [isComparison, stock1Metrics, stock2Metrics]);

  if (stocks.length === 0 || !stock1Metrics) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <p>No financial data available. Ask about a stock to see analysis.</p>
      </div>
    );
  }

  // Single stock view
  if (!isComparison) {
    return (
      <div className="h-full overflow-y-auto p-6 space-y-6 no-scrollbar">
        <OverviewCard
          symbol={stocks[0].symbol}
          stockData={stocks[0].stockData}
        />

        <IncomeStatementTable metrics={stock1Metrics.income} />
        <BalanceSheetTable metrics={stock1Metrics.balance} />
        <CashFlowTable metrics={stock1Metrics.cashFlow} />
        <EarningsTable earningsData={stock1Metrics.earnings} />
      </div>
    );
  }

  // Comparison view (side-by-side)
  return (
    <div className="h-full overflow-y-auto p-6 no-scrollbar">
      <div className="grid grid-cols-2 gap-6">
        {/* Stock 1 Column */}
        <div className="space-y-6">
          <OverviewCard
            symbol={stocks[0].symbol}
            stockData={stocks[0].stockData}
          />

          <IncomeStatementTable
            metrics={stock1Metrics.income}
            comparisonResults={comparisonResults.stock1}
            isComparison={true}
          />

          <BalanceSheetTable
            metrics={stock1Metrics.balance}
            comparisonResults={comparisonResults.stock1}
            isComparison={true}
          />

          <CashFlowTable
            metrics={stock1Metrics.cashFlow}
            comparisonResults={comparisonResults.stock1}
            isComparison={true}
          />

          <EarningsTable earningsData={stock1Metrics.earnings} />
        </div>

        {/* Stock 2 Column */}
        <div className="space-y-6">
          <OverviewCard
            symbol={stocks[1].symbol}
            stockData={stocks[1].stockData}
          />

          <IncomeStatementTable
            metrics={stock2Metrics!.income}
            comparisonResults={comparisonResults.stock2}
            isComparison={true}
          />

          <BalanceSheetTable
            metrics={stock2Metrics!.balance}
            comparisonResults={comparisonResults.stock2}
            isComparison={true}
          />

          <CashFlowTable
            metrics={stock2Metrics!.cashFlow}
            comparisonResults={comparisonResults.stock2}
            isComparison={true}
          />

          <EarningsTable earningsData={stock2Metrics!.earnings} />
        </div>
      </div>
    </div>
  );
};
