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

/**
 * Extract metrics from Income Statement
 */
export const extractIncomeMetrics = (
  statementData: Record<string, any>,
): IncomeMetrics => {
  const income =
    statementData?.income_statement?.data?.annualReports?.[0] ||
    statementData?.annualReports?.[0] ||
    {};

  const revenue = parseFinancialValue(income.totalRevenue);
  const grossProfit = parseFinancialValue(income.grossProfit);
  const operatingIncome = parseFinancialValue(income.operatingIncome);
  const netIncome = parseFinancialValue(income.netIncome);
  const ebitda = parseFinancialValue(income.ebitda);

  return {
    fiscalYearEnd: income.fiscalDateEnding || "N/A",
    revenue,
    costOfRevenue: parseFinancialValue(income.costOfRevenue),
    grossProfit,
    grossMargin:
      revenue && grossProfit !== null ? (grossProfit / revenue) * 100 : null,
    operatingExpenses: parseFinancialValue(
      income.operatingExpenses || income.sellingGeneralAdministrative,
    ),
    operatingIncome,
    operatingMargin:
      revenue && operatingIncome !== null
        ? (operatingIncome / revenue) * 100
        : null,
    interestExpense: parseFinancialValue(income.interestExpense),
    taxExpense: parseFinancialValue(income.incomeTaxExpense),
    netIncome,
    netMargin:
      revenue && netIncome !== null ? (netIncome / revenue) * 100 : null,
    ebitda,
    ebitdaMargin: revenue && ebitda !== null ? (ebitda / revenue) * 100 : null,
    eps: parseFinancialValue(income.dilutedEPS || income.eps),
  };
};

/**
 * Extract metrics from Balance Sheet
 */
export const extractBalanceSheetMetrics = (
  statementData: Record<string, any>,
): BalanceSheetMetrics => {
  const balance =
    statementData?.balance_sheet?.data?.annualReports?.[0] ||
    statementData?.annualReports?.[0] ||
    {};

  const currentAssets = parseFinancialValue(balance.totalCurrentAssets);
  const currentLiabilities = parseFinancialValue(
    balance.totalCurrentLiabilities,
  );
  const totalAssets = parseFinancialValue(balance.totalAssets);
  const totalLiabilities = parseFinancialValue(balance.totalLiabilities);
  const shareholderEquity = parseFinancialValue(balance.totalShareholderEquity);
  const cash = parseFinancialValue(
    balance.cashAndCashEquivalentsAtCarryingValue || balance.cash,
  );
  const inventory = parseFinancialValue(balance.inventory);
  const receivables = parseFinancialValue(
    balance.currentNetReceivables || balance.accountsReceivable,
  );
  const totalDebt = parseFinancialValue(
    balance.shortLongTermDebtTotal || balance.totalDebt,
  );
  const longTermDebt = parseFinancialValue(balance.longTermDebt);

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
      currentAssets && currentLiabilities
        ? currentAssets / currentLiabilities
        : null,
    quickRatio:
      currentAssets && currentLiabilities
        ? (currentAssets - (inventory || 0)) / currentLiabilities
        : null,
    debtToEquity:
      totalDebt && shareholderEquity ? totalDebt / shareholderEquity : null,
    workingCapital:
      currentAssets && currentLiabilities
        ? currentAssets - currentLiabilities
        : null,
  };
};

/**
 * Extract metrics from Cash Flow Statement
 */
export const extractCashFlowMetrics = (
  statementData: Record<string, any>,
): CashFlowMetrics => {
  const cashFlow =
    statementData?.cash_flow?.data?.annualReports?.[0] ||
    statementData?.annualReports?.[0] ||
    {};

  const operatingCashFlow = parseFinancialValue(
    cashFlow.operatingCashflow || cashFlow.operatingActivitiesNetCash,
  );
  const capex = parseFinancialValue(
    cashFlow.capitalExpenditures || cashFlow.capitalExpenditure,
  );

  const freeCashFlow =
    operatingCashFlow !== null && capex !== null
      ? operatingCashFlow - Math.abs(capex)
      : null;

  const revenue = parseFinancialValue(
    statementData?.income_statement?.[0]?.totalRevenue,
  );

  return {
    operatingCashFlow,
    investingCashFlow: parseFinancialValue(
      cashFlow.cashflowFromInvestment || cashFlow.investingCashflow,
    ),
    financingCashFlow: parseFinancialValue(
      cashFlow.cashflowFromFinancing || cashFlow.financingCashflow,
    ),
    capex,
    freeCashFlow,
    fcfMargin:
      freeCashFlow !== null && revenue ? (freeCashFlow / revenue) * 100 : null,
    dividendsPaid: parseFinancialValue(
      cashFlow.dividendPayout || cashFlow.dividendsPaid,
    ),
  };
};

/**
 * Extract EPS Surprise Data
 */
export const extractEarningsData = (
  statementData: Record<string, any>,
): EarningsData[] => {
  const earnings = statementData?.earnings?.data?.quarterlyEarnings || [];

  return earnings.slice(0, 8).map((q: Record<string, any>) => {
    const reported = parseFinancialValue(q.reportedEPS);
    const estimated = parseFinancialValue(q.estimatedEPS);

    const surprise =
      reported !== null && estimated !== null ? reported - estimated : null;

    const surprisePercent =
      surprise !== null && estimated !== null && estimated !== 0
        ? (surprise / estimated) * 100
        : null;

    return {
      quarter: q.fiscalDateEnding || "N/A",
      reportedEPS: reported,
      estimatedEPS: estimated,
      surprise,
      surprisePercent,
    };
  });
};
