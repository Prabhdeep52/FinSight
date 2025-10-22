import React from 'react';
import { formatCurrency, formatRatio } from '../utils/formatters';

interface OverviewCardProps {
  symbol: string;
  companyName?: string;
  stockData: Record<string, unknown>;
}

export const OverviewCard: React.FC<OverviewCardProps> = ({
  symbol,
  companyName,
  stockData,
}) => {
  const overview = (stockData?.get_stock_overview as Record<string, unknown>) || {};
  
  const marketCap = overview.MarketCapitalization as string | undefined;
  const peRatio = overview.PERatio as string | undefined;
  const week52High = overview['52WeekHigh'] as string | undefined;
  const week52Low = overview['52WeekLow'] as string | undefined;
  const beta = overview.Beta as string | undefined;
  const dividendYield = overview.DividendYield as string | undefined;
  const sector = overview.Sector as string | undefined;
  const industry = overview.Industry as string | undefined;

  return (
    <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 rounded-lg border border-blue-500/30 p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-3xl font-bold text-white">{symbol}</h2>
          {companyName && (
            <p className="text-gray-400 mt-1">{companyName}</p>
          )}
          {sector && (
            <p className="text-sm text-gray-500 mt-1">{sector} • {industry}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
        <div>
          <p className="text-xs text-gray-400 mb-1">Market Cap</p>
          <p className="text-lg font-semibold text-white">
            {marketCap ? formatCurrency(parseFloat(marketCap)) : 'N/A'}
          </p>
        </div>

        <div>
          <p className="text-xs text-gray-400 mb-1">P/E Ratio</p>
          <p className="text-lg font-semibold text-white">
            {peRatio ? formatRatio(parseFloat(peRatio)) : 'N/A'}
          </p>
        </div>

        <div>
          <p className="text-xs text-gray-400 mb-1">52W Range</p>
          <p className="text-lg font-semibold text-white">
            {week52Low && week52High 
              ? `$${parseFloat(week52Low).toFixed(2)} - $${parseFloat(week52High).toFixed(2)}`
              : 'N/A'}
          </p>
        </div>

        <div>
          <p className="text-xs text-gray-400 mb-1">Beta</p>
          <p className="text-lg font-semibold text-white">
            {beta ? formatRatio(parseFloat(beta)) : 'N/A'}
          </p>
        </div>

        <div>
          <p className="text-xs text-gray-400 mb-1">Dividend Yield</p>
          <p className="text-lg font-semibold text-white">
            {dividendYield ? `${(parseFloat(dividendYield) * 100).toFixed(2)}%` : 'N/A'}
          </p>
        </div>
      </div>
    </div>
  );
};
