import React from 'react';
import type { EarningsData } from '../utils/metricExtractors';
import { formatPercent } from '../utils/formatters';

interface EarningsTableProps {
  earningsData: EarningsData[];
}

export const EarningsTable: React.FC<EarningsTableProps> = ({
  earningsData,
}) => {
  return (
    <div className="bg-gray-800/50 rounded-lg border border-gray-700">
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white">📊 Quarterly Earnings</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left p-3 text-sm font-medium text-gray-400">Quarter</th>
              <th className="text-right p-3 text-sm font-medium text-gray-400">Reported EPS</th>
              <th className="text-right p-3 text-sm font-medium text-gray-400">Estimated EPS</th>
              <th className="text-right p-3 text-sm font-medium text-gray-400">Surprise</th>
            </tr>
          </thead>
          <tbody>
            {earningsData.map((earning, idx) => {
              const isBeat = earning.surprisePercent !== null && earning.surprisePercent > 0;
              const surpriseClass = isBeat 
                ? 'text-green-400' 
                : earning.surprisePercent !== null && earning.surprisePercent < 0 
                  ? 'text-red-400' 
                  : '';
              
              return (
                <tr key={`${earning.quarter}-${idx}`} className="border-b border-gray-700/50">
                  <td className="p-3 text-sm text-gray-300">{earning.quarter}</td>
                  <td className="p-3 text-sm text-right font-mono">
                    {earning.reportedEPS?.toFixed(2) || 'N/A'}
                  </td>
                  <td className="p-3 text-sm text-right font-mono">
                    {earning.estimatedEPS?.toFixed(2) || 'N/A'}
                  </td>
                  <td className={`p-3 text-sm text-right font-mono ${surpriseClass}`}>
                    {earning.surprisePercent !== null ? (
                      <>
                        {isBeat ? '🟢' : '🔴'} {formatPercent(earning.surprisePercent)}
                      </>
                    ) : (
                      'N/A'
                    )}
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
