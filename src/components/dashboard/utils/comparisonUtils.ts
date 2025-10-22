/**
 * Comparison utilities for highlighting winners in financial metrics
 */

export type ComparisonResult = 'better' | 'worse' | 'neutral';

export interface MetricComparison {
  stock1Value: number | null;
  stock2Value: number | null;
  stock1Result: ComparisonResult;
  stock2Result: ComparisonResult;
}

/**
 * Compare two values where higher is better
 */
export const compareHigherBetter = (
  value1: number | null,
  value2: number | null
): MetricComparison => {
  if (value1 === null || value2 === null) {
    return {
      stock1Value: value1,
      stock2Value: value2,
      stock1Result: 'neutral',
      stock2Result: 'neutral',
    };
  }

  const diff = Math.abs(value1 - value2);
  const avg = (value1 + value2) / 2;
  const percentDiff = (diff / avg) * 100;

  // Only highlight if difference is > 5%
  if (percentDiff < 5) {
    return {
      stock1Value: value1,
      stock2Value: value2,
      stock1Result: 'neutral',
      stock2Result: 'neutral',
    };
  }

  return {
    stock1Value: value1,
    stock2Value: value2,
    stock1Result: value1 > value2 ? 'better' : 'worse',
    stock2Result: value2 > value1 ? 'better' : 'worse',
  };
};

/**
 * Compare two values where lower is better
 */
export const compareLowerBetter = (
  value1: number | null,
  value2: number | null
): MetricComparison => {
  if (value1 === null || value2 === null) {
    return {
      stock1Value: value1,
      stock2Value: value2,
      stock1Result: 'neutral',
      stock2Result: 'neutral',
    };
  }

  const diff = Math.abs(value1 - value2);
  const avg = (value1 + value2) / 2;
  const percentDiff = (diff / avg) * 100;

  // Only highlight if difference is > 5%
  if (percentDiff < 5) {
    return {
      stock1Value: value1,
      stock2Value: value2,
      stock1Result: 'neutral',
      stock2Result: 'neutral',
    };
  }

  return {
    stock1Value: value1,
    stock2Value: value2,
    stock1Result: value1 < value2 ? 'better' : 'worse',
    stock2Result: value2 < value1 ? 'better' : 'worse',
  };
};

/**
 * Get CSS classes for comparison result
 */
export const getComparisonClasses = (result: ComparisonResult): string => {
  switch (result) {
    case 'better':
      return 'bg-green-500/10 text-green-400 font-semibold';
    case 'worse':
      return 'bg-red-500/10 text-red-400';
    case 'neutral':
    default:
      return '';
  }
};

/**
 * Get indicator icon for comparison result
 */
export const getComparisonIndicator = (result: ComparisonResult): string => {
  switch (result) {
    case 'better':
      return '✅';
    case 'worse':
      return '⚠️';
    case 'neutral':
    default:
      return '';
  }
};
