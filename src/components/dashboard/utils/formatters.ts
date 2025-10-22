/**
 * Formatting utilities for financial data display
 */

export const formatCurrency = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined || value === 'None') return 'N/A';
  
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return 'N/A';
  
  // Format in billions/millions
  if (Math.abs(num) >= 1e9) {
    return `$${(num / 1e9).toFixed(2)}B`;
  } else if (Math.abs(num) >= 1e6) {
    return `$${(num / 1e6).toFixed(2)}M`;
  } else if (Math.abs(num) >= 1e3) {
    return `$${(num / 1e3).toFixed(2)}K`;
  }
  return `$${num.toFixed(2)}`;
};

export const formatPercent = (value: number | string | null | undefined, decimals = 2): string => {
  if (value === null || value === undefined || value === 'None') return 'N/A';
  
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return 'N/A';
  
  return `${num.toFixed(decimals)}%`;
};

export const formatRatio = (value: number | string | null | undefined, decimals = 2): string => {
  if (value === null || value === undefined || value === 'None') return 'N/A';
  
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return 'N/A';
  
  return num.toFixed(decimals);
};

export const formatChange = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined || value === 'None') return 'N/A';
  
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return 'N/A';
  
  const sign = num >= 0 ? '+' : '';
  return `${sign}${num.toFixed(2)}%`;
};

export const formatNumber = (value: number | string | null | undefined, decimals = 0): string => {
  if (value === null || value === undefined || value === 'None') return 'N/A';
  
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return 'N/A';
  
  return num.toFixed(decimals);
};

export const parseFinancialValue = (value: never): number | null => {
  if (value === null || value === undefined || value === 'None') return null;
  
  if (typeof value === 'number') return value;
  if (typeof value === 'string') {
    const num = parseFloat(value);
    return isNaN(num) ? null : num;
  }
  
  return null;
};
