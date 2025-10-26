/**
 * Extract and compute financial metrics from raw API data
 */

import { parseFinancialValue } from "./formatters";

export interface IncomeMetrics {
  fiscalYearEnd: string;
  revenue: number | null;
  costOfRevenue: number | null;
  grossProfit: number | null;
  grossMargin: number | null;
  operatingExpenses: number | null;
  operatingIncome: number | null;
  operatingMargin: number | null;
  interestExpense: number | null;
  taxExpense: number | null;
  netIncome: number | null;
  netMargin: number | null;
  ebitda: number | null;
  ebitdaMargin: number | null;
  eps: number | null;
}

export interface BalanceSheetMetrics {
  totalAssets: number | null;
  currentAssets: number | null;
  cash: number | null;
  receivables: number | null;
  inventory: number | null;
  totalLiabilities: number | null;
  currentLiabilities: number | null;
  longTermDebt: number | null;
  totalDebt: number | null;
  shareholderEquity: number | null;
  currentRatio: number | null;
  quickRatio: number | null;
  debtToEquity: number | null;
  workingCapital: number | null;
}

export interface CashFlowMetrics {
  operatingCashFlow: number | null;
  investingCashFlow: number | null;
  financingCashFlow: number | null;
  capex: number | null;
  freeCashFlow: number | null;
  fcfMargin: number | null;
  dividendsPaid: number | null;
}

export interface EarningsData {
  quarter: string;
  reportedEPS: number | null;
  estimatedEPS: number | null;
  surprise: number | null;
  surprisePercent: number | null;
}

// Define types for API response structures
type FinancialData = Record<string, unknown>;

interface StatementData {
  income_statement?: {
    data?: {
      annualReports?: FinancialData[];
    };
    annualReports?: FinancialData[];
  };
  balance_sheet?: {
    data?: {
      annualReports?: FinancialData[];
    };
  };
  cash_flow?: {
    data?: {
      annualReports?: FinancialData[];
    };
  };
  earnings?: {
    data?: {
      quarterlyEarnings?: FinancialData[];
    };
  };
  annualReports?: FinancialData[];
}

// Type-safe wrapper for parseFinancialValue
const safeParse = (value: unknown): number | null => {
  return (parseFinancialValue as (value: unknown) => number | null)(value);
};

/**
 * Extract metrics from Income Statement
 */
export const extractIncomeMetrics = (
  statementData: StatementData,
): IncomeMetrics => {
  const income =
    statementData?.income_statement?.data?.annualReports?.[0] ||
    statementData?.annualReports?.[0] ||
    {};

  const revenue = safeParse(income.totalRevenue);
  const grossProfit = safeParse(income.grossProfit);
  const operatingIncome = safeParse(income.operatingIncome);
  const netIncome = safeParse(income.netIncome);
  const ebitda = safeParse(income.ebitda);

  return {
    fiscalYearEnd: (income.fiscalDateEnding as string) || "N/A",
    revenue,
    costOfRevenue: safeParse(income.costOfRevenue),
    grossProfit,
    grossMargin:
      revenue && grossProfit !== null ? (grossProfit / revenue) * 100 : null,
    operatingExpenses: safeParse(
      income.operatingExpenses || income.sellingGeneralAdministrative,
    ),
    operatingIncome,
    operatingMargin:
      revenue && operatingIncome !== null
        ? (operatingIncome / revenue) * 100
        : null,
    interestExpense: safeParse(income.interestExpense),
    taxExpense: safeParse(income.incomeTaxExpense),
    netIncome,
    netMargin:
      revenue && netIncome !== null ? (netIncome / revenue) * 100 : null,
    ebitda,
    ebitdaMargin: revenue && ebitda !== null ? (ebitda / revenue) * 100 : null,
    eps: safeParse(income.dilutedEPS || income.eps),
  };
};

/**
 * Extract metrics from Balance Sheet
 */
export const extractBalanceSheetMetrics = (
  statementData: StatementData,
): BalanceSheetMetrics => {
  const balance =
    statementData?.balance_sheet?.data?.annualReports?.[0] ||
    statementData?.annualReports?.[0] ||
    {};

  const currentAssets = safeParse(balance.totalCurrentAssets);
  const currentLiabilities = safeParse(balance.totalCurrentLiabilities);
  const totalAssets = safeParse(balance.totalAssets);
  const totalLiabilities = safeParse(balance.totalLiabilities);
  const shareholderEquity = safeParse(balance.totalShareholderEquity);
  const cash = safeParse(
    balance.cashAndCashEquivalentsAtCarryingValue || balance.cash,
  );
  const inventory = safeParse(balance.inventory);
  const receivables = safeParse(
    balance.currentNetReceivables || balance.accountsReceivable,
  );
  const totalDebt = safeParse(
    balance.shortLongTermDebtTotal || balance.totalDebt,
  );
  const longTermDebt = safeParse(balance.longTermDebt);

  return {
    totalAssets,
    currentAssets,
    cash,
    receivables,
    inventory,
    totalLiabilities,
    currentLiabilities,
    longTermDebt,
    totalDebt,
    shareholderEquity,
    currentRatio:
      currentAssets !== null && currentLiabilities !== null
        ? currentAssets / currentLiabilities
        : null,
    quickRatio:
      currentAssets !== null && currentLiabilities !== null
        ? (currentAssets - (inventory || 0)) / currentLiabilities
        : null,
    debtToEquity:
      totalDebt !== null && shareholderEquity !== null
        ? totalDebt / shareholderEquity
        : null,
    workingCapital:
      currentAssets !== null && currentLiabilities !== null
        ? currentAssets - currentLiabilities
        : null,
  };
};

/**
 * Extract metrics from Cash Flow Statement
 */
export const extractCashFlowMetrics = (
  statementData: StatementData,
): CashFlowMetrics => {
  const cashFlow =
    statementData?.cash_flow?.data?.annualReports?.[0] ||
    statementData?.annualReports?.[0] ||
    {};

  const operatingCashFlow = safeParse(
    cashFlow.operatingCashflow || cashFlow.operatingActivitiesNetCash,
  );
  const capex = safeParse(
    cashFlow.capitalExpenditures || cashFlow.capitalExpenditure,
  );

  const freeCashFlow =
    operatingCashFlow !== null && capex !== null
      ? operatingCashFlow - Math.abs(capex)
      : null;

  const incomeStatement =
    statementData?.income_statement?.data?.annualReports?.[0] ||
    statementData?.income_statement?.annualReports?.[0] ||
    {};
  const revenue = safeParse(incomeStatement.totalRevenue);

  return {
    operatingCashFlow,
    investingCashFlow: safeParse(
      cashFlow.cashflowFromInvestment || cashFlow.investingCashflow,
    ),
    financingCashFlow: safeParse(
      cashFlow.cashflowFromFinancing || cashFlow.financingCashflow,
    ),
    capex,
    freeCashFlow,
    fcfMargin:
      freeCashFlow !== null && revenue !== null
        ? (freeCashFlow / revenue) * 100
        : null,
    dividendsPaid: safeParse(cashFlow.dividendPayout || cashFlow.dividendsPaid),
  };
};

/**
 * Extract EPS Surprise Data
 */
export const extractEarningsData = (
  statementData: StatementData,
): EarningsData[] => {
  const earnings = statementData?.earnings?.data?.quarterlyEarnings || [];

  return earnings.slice(0, 8).map((q: FinancialData) => {
    const reported = safeParse(q.reportedEPS);
    const estimated = safeParse(q.estimatedEPS);

    const surprise =
      reported !== null && estimated !== null ? reported - estimated : null;

    const surprisePercent =
      surprise !== null && estimated !== null && estimated !== 0
        ? (surprise / estimated) * 100
        : null;

    return {
      quarter: (q.fiscalDateEnding as string) || "N/A",
      reportedEPS: reported,
      estimatedEPS: estimated,
      surprise,
      surprisePercent,
    };
  });
};
