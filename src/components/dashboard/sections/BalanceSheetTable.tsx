import React from 'react';
import type { BalanceSheetMetrics } from '../utils/metricExtractors';
import { formatCurrency, formatRatio } from '../utils/formatters';
import { getComparisonClasses, getComparisonIndicator, type ComparisonResult } from '../utils/comparisonUtils';

interface BalanceSheetTableProps {
  metrics: BalanceSheetMetrics;
  comparisonResults?: Record<string, ComparisonResult>;
  isComparison?: boolean;
}

export const BalanceSheetTable: React.FC<BalanceSheetTableProps> = ({
  metrics,
  comparisonResults = {},
  isComparison = false,
}) => {
  const rows = [
    { label: 'Total Assets', value: metrics.totalAssets, key: 'totalAssets', format: 'currency' },
    { label: 'Current Assets', value: metrics.currentAssets, key: 'currentAssets', format: 'currency' },
    { label: 'Cash & Equivalents', value: metrics.cash, key: 'cash', format: 'currency' },
    { label: 'Receivables', value: metrics.receivables, key: 'receivables', format: 'currency' },
    { label: 'Inventory', value: metrics.inventory, key: 'inventory', format: 'currency' },
    { label: 'Total Liabilities', value: metrics.totalLiabilities, key: 'totalLiabilities', format: 'currency' },
    { label: 'Current Liabilities', value: metrics.currentLiabilities, key: 'currentLiabilities', format: 'currency' },
    { label: 'Long-term Debt', value: metrics.longTermDebt, key: 'longTermDebt', format: 'currency' },
    { label: 'Total Debt', value: metrics.totalDebt, key: 'totalDebt', format: 'currency' },
    { label: 'Shareholder Equity', value: metrics.shareholderEquity, key: 'shareholderEquity', format: 'currency' },
    { label: 'Working Capital', value: metrics.workingCapital, key: 'workingCapital', format: 'currency' },
    { label: 'Current Ratio', value: metrics.currentRatio, key: 'currentRatio', format: 'ratio' },
    { label: 'Quick Ratio', value: metrics.quickRatio, key: 'quickRatio', format: 'ratio' },
    { label: 'Debt-to-Equity', value: metrics.debtToEquity, key: 'debtToEquity', format: 'ratio' },
  ];

  const formatValue = (value: number | null, format: string) => {
    if (format === 'currency') return formatCurrency(value);
    if (format === 'ratio') return formatRatio(value);
    return value?.toString() || 'N/A';
  };

  return (
    <div className="bg-gray-800/50 rounded-lg border border-gray-700">
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white">💰 Balance Sheet</h3>
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
