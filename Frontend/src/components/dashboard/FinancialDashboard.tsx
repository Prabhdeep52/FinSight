/** eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useMemo } from "react";
import { OverviewCard } from "./sections/OverviewCard";
import { IncomeStatementTable } from "./sections/IncomeStatementTable";
import { BalanceSheetTable } from "./sections/BalanceSheetTable";
import { CashFlowTable } from "./sections/CashFlowTable";
import { EarningsTable } from "./sections/EarningsTable";
import { NewsSidebar } from "./sections/NewsSidebar";
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
  stockData: Record<string, any>;
  statementData: Record<string, any>;
  events?: any[];
}

interface FinancialDashboardProps {
  stocks: Stock[];
}

export const FinancialDashboard: React.FC<FinancialDashboardProps> = ({
  stocks,
}) => {
  const isComparison = stocks.length === 2;

  // Helper function to check if a metrics object has valid data
  const hasValidData = (
    metrics: Record<string, any> | null | undefined,
  ): boolean => {
    if (!metrics) return false;
    return Object.values(metrics).some(
      (value) =>
        value !== null &&
        value !== undefined &&
        value !== "N/A" &&
        value !== "" &&
        !Number.isNaN(value),
    );
  };

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

    const addComparison = (
      key: string,
      compFunc: (a: number, b: number) => any,
      a: any,
      b: any,
    ) => {
      const res = compFunc(a, b);
      stock1Results[key] = res.stock1Result;
      stock2Results[key] = res.stock2Result;
    };

    // Income comparisons
    addComparison(
      "revenue",
      compareHigherBetter,
      stock1Metrics.income.revenue,
      stock2Metrics.income.revenue,
    );
    addComparison(
      "grossMargin",
      compareHigherBetter,
      stock1Metrics.income.grossMargin,
      stock2Metrics.income.grossMargin,
    );
    addComparison(
      "operatingMargin",
      compareHigherBetter,
      stock1Metrics.income.operatingMargin,
      stock2Metrics.income.operatingMargin,
    );
    addComparison(
      "netMargin",
      compareHigherBetter,
      stock1Metrics.income.netMargin,
      stock2Metrics.income.netMargin,
    );
    addComparison(
      "ebitda",
      compareHigherBetter,
      stock1Metrics.income.ebitda,
      stock2Metrics.income.ebitda,
    );

    // Balance comparisons
    addComparison(
      "currentRatio",
      compareHigherBetter,
      stock1Metrics.balance.currentRatio,
      stock2Metrics.balance.currentRatio,
    );
    addComparison(
      "debtToEquity",
      compareLowerBetter,
      stock1Metrics.balance.debtToEquity,
      stock2Metrics.balance.debtToEquity,
    );

    // Cash flow comparisons
    addComparison(
      "freeCashFlow",
      compareHigherBetter,
      stock1Metrics.cashFlow.freeCashFlow,
      stock2Metrics.cashFlow.freeCashFlow,
    );
    addComparison(
      "fcfMargin",
      compareHigherBetter,
      stock1Metrics.cashFlow.fcfMargin,
      stock2Metrics.cashFlow.fcfMargin,
    );

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

        {hasValidData(stock1Metrics.income) && (
          <IncomeStatementTable metrics={stock1Metrics.income} />
        )}

        {hasValidData(stock1Metrics.balance) && (
          <BalanceSheetTable metrics={stock1Metrics.balance} />
        )}

        {hasValidData(stock1Metrics.cashFlow) && (
          <CashFlowTable metrics={stock1Metrics.cashFlow} />
        )}

        {hasValidData(stock1Metrics.earnings) && (
          <EarningsTable earningsData={stock1Metrics.earnings} />
        )}

        {/* Integrated News Section */}
        {stocks[0].events && stocks[0].events.length > 0 && (
          <NewsSidebar
            events={stocks[0].events}
            heading={`Latest News on ${stocks[0].symbol}`}
          />
        )}
      </div>
    );
  }

  // Comparison view
  return (
    <div className="h-full overflow-y-auto p-6 no-scrollbar">
      <div className="grid grid-cols-2 gap-6">
        {/* Stock 1 Column */}
        <div className="space-y-6">
          <OverviewCard
            symbol={stocks[0].symbol}
            stockData={stocks[0].stockData}
          />

          {hasValidData(stock1Metrics.income) && (
            <IncomeStatementTable
              metrics={stock1Metrics.income}
              comparisonResults={comparisonResults.stock1}
              isComparison
            />
          )}

          {hasValidData(stock1Metrics.balance) && (
            <BalanceSheetTable
              metrics={stock1Metrics.balance}
              comparisonResults={comparisonResults.stock1}
              isComparison
            />
          )}

          {hasValidData(stock1Metrics.cashFlow) && (
            <CashFlowTable
              metrics={stock1Metrics.cashFlow}
              comparisonResults={comparisonResults.stock1}
              isComparison
            />
          )}

          {hasValidData(stock1Metrics.earnings) && (
            <EarningsTable earningsData={stock1Metrics.earnings} />
          )}

          {stocks[0].events && stocks[0].events.length > 0 && (
            <NewsSidebar
              events={stocks[0].events}
              heading={`News: ${stocks[0].symbol}`}
            />
          )}
        </div>

        {/* Stock 2 Column */}
        <div className="space-y-6">
          <OverviewCard
            symbol={stocks[1].symbol}
            stockData={stocks[1].stockData}
          />

          {hasValidData(stock2Metrics!.income) && (
            <IncomeStatementTable
              metrics={stock2Metrics!.income}
              comparisonResults={comparisonResults.stock2}
              isComparison
            />
          )}

          {hasValidData(stock2Metrics!.balance) && (
            <BalanceSheetTable
              metrics={stock2Metrics!.balance}
              comparisonResults={comparisonResults.stock2}
              isComparison
            />
          )}

          {hasValidData(stock2Metrics!.cashFlow) && (
            <CashFlowTable
              metrics={stock2Metrics!.cashFlow}
              comparisonResults={comparisonResults.stock2}
              isComparison
            />
          )}

          {hasValidData(stock2Metrics!.earnings) && (
            <EarningsTable earningsData={stock2Metrics!.earnings} />
          )}

          {stocks[1].events && stocks[1].events.length > 0 && (
            <NewsSidebar
              events={stocks[1].events}
              heading={`News: ${stocks[1].symbol}`}
            />
          )}
        </div>
      </div>
    </div>
  );
};
