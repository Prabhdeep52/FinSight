import React from 'react';
import type { CashFlowMetrics } from '../utils/metricExtractors';
import { formatCurrency, formatPercent } from '../utils/formatters';
import { getComparisonClasses, getComparisonIndicator, type ComparisonResult } from '../utils/comparisonUtils';

interface CashFlowTableProps {
  metrics: CashFlowMetrics;
  comparisonResults?: Record<string, ComparisonResult>;
  isComparison?: boolean;
}

export const CashFlowTable: React.FC<CashFlowTableProps> = ({
  metrics,
  comparisonResults = {},
  isComparison = false,
}) => {
  const rows = [
    { label: 'Operating Cash Flow', value: metrics.operatingCashFlow, key: 'operatingCashFlow', format: 'currency' },
    { label: 'Investing Cash Flow', value: metrics.investingCashFlow, key: 'investingCashFlow', format: 'currency' },
    { label: 'Financing Cash Flow', value: metrics.financingCashFlow, key: 'financingCashFlow', format: 'currency' },
    { label: 'Capital Expenditures', value: metrics.capex, key: 'capex', format: 'currency' },
    { label: 'Free Cash Flow', value: metrics.freeCashFlow, key: 'freeCashFlow', format: 'currency' },
    { label: 'FCF Margin', value: metrics.fcfMargin, key: 'fcfMargin', format: 'percent' },
    { label: 'Dividends Paid', value: metrics.dividendsPaid, key: 'dividendsPaid', format: 'currency' },
  ];

  const formatValue = (value: number | null, format: string) => {
    if (format === 'currency') return formatCurrency(value);
    if (format === 'percent') return formatPercent(value);
    return value?.toString() || 'N/A';
  };

  return (
    <div className="bg-gray-800/50 rounded-lg border border-gray-700">
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white">💵 Cash Flow</h3>
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
