import React from 'react';
import type { IncomeMetrics } from '../utils/metricExtractors';
import { formatCurrency, formatPercent } from '../utils/formatters';
import { getComparisonClasses, getComparisonIndicator, type ComparisonResult } from '../utils/comparisonUtils';

interface IncomeStatementTableProps {
  metrics: IncomeMetrics;
  comparisonResults?: Record<string, ComparisonResult>;
  isComparison?: boolean;
}

export const IncomeStatementTable: React.FC<IncomeStatementTableProps> = ({
  metrics,
  comparisonResults = {},
  isComparison = false,
}) => {
  const rows = [
    { label: 'Fiscal Year End', value: metrics.fiscalYearEnd, key: 'fiscalYearEnd', format: 'text' },
    { label: 'Total Revenue', value: metrics.revenue, key: 'revenue', format: 'currency' },
    { label: 'Cost of Revenue', value: metrics.costOfRevenue, key: 'costOfRevenue', format: 'currency' },
    { label: 'Gross Profit', value: metrics.grossProfit, key: 'grossProfit', format: 'currency' },
    { label: 'Gross Margin', value: metrics.grossMargin, key: 'grossMargin', format: 'percent' },
    { label: 'Operating Expenses', value: metrics.operatingExpenses, key: 'operatingExpenses', format: 'currency' },
    { label: 'Operating Income', value: metrics.operatingIncome, key: 'operatingIncome', format: 'currency' },
    { label: 'Operating Margin', value: metrics.operatingMargin, key: 'operatingMargin', format: 'percent' },
    { label: 'Interest Expense', value: metrics.interestExpense, key: 'interestExpense', format: 'currency' },
    { label: 'Tax Expense', value: metrics.taxExpense, key: 'taxExpense', format: 'currency' },
    { label: 'Net Income', value: metrics.netIncome, key: 'netIncome', format: 'currency' },
    { label: 'Net Margin', value: metrics.netMargin, key: 'netMargin', format: 'percent' },
    { label: 'EBITDA', value: metrics.ebitda, key: 'ebitda', format: 'currency' },
    { label: 'EBITDA Margin', value: metrics.ebitdaMargin, key: 'ebitdaMargin', format: 'percent' },
    { label: 'EPS (Diluted)', value: metrics.eps, key: 'eps', format: 'number' },
  ];

  const formatValue = (value: number | string | null, format: string) => {
    if (format === 'currency') return formatCurrency(value);
    if (format === 'percent') return formatPercent(value);
    if (format === 'number') return value?.toString() || 'N/A';
    return value || 'N/A';
  };

  return (
    <div className="bg-gray-800/50 rounded-lg border border-gray-700">
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white">📈 Income Statement (Annual)</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left p-3 text-sm font-medium text-gray-400">Metric</th>
              <th className="text-right p-3 text-sm font-medium text-gray-400">Value</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const comparisonResult = comparisonResults[row.key] || 'neutral';
              const classes = isComparison ? getComparisonClasses(comparisonResult) : '';
              const indicator = isComparison ? getComparisonIndicator(comparisonResult) : '';

              return (
                <tr key={row.key} className={`border-b border-gray-700/50 ${classes}`}>
                  <td className="p-3 text-sm text-gray-300">{row.label}</td>
                  <td className="p-3 text-sm text-right font-mono">
                    {formatValue(row.value, row.format)} {indicator}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
