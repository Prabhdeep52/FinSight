/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";
import CollapsibleTable from "./collapsible-table";

interface FinancialTablesProps {
  symbol: string;
  data: Record<string, unknown>;
}

function formatCurrency(value: unknown) {
  const numericValue =
    typeof value === "number"
      ? value
      : typeof value === "string"
        ? Number(value)
        : Number.NaN;

  if (!Number.isFinite(numericValue)) {
    return "N/A";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(numericValue);
}

export default function FinancialTables({
  symbol,
  data,
}: FinancialTablesProps) {
  const incomeStatement = data.income_statement as Record<string, any>;
  const balanceSheet = data.balance_sheet as Record<string, any>;
  const cashFlow = data.cash_flow as Record<string, any>;
  const earnings = data.earnings as Record<string, any>;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold text-foreground">
        Detailed Financial Data - {symbol}
      </h3>

      {/* Income Statement */}
      <CollapsibleTable title="Income Statement" defaultOpen={true}>
        {incomeStatement?.available === false ? (
          <p className="text-sm text-muted-foreground p-4">
            {incomeStatement.message}
          </p>
        ) : incomeStatement?.data?.annualReports?.[0] ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-4 py-3 font-semibold text-foreground">
                    Metric
                  </th>
                  <th className="text-right px-4 py-3 font-semibold text-foreground">
                    Value
                  </th>
                </tr>
              </thead>
              <tbody>
                {(() => {
                  const latest = incomeStatement.data.annualReports[0];
                  return (
                    <>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Fiscal Year End
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {latest.fiscalDateEnding}
                        </td>
                      </tr>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Total Revenue
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(
                            Number.parseFloat(latest.totalRevenue || 0),
                          )}
                        </td>
                      </tr>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Gross Profit
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(
                            Number.parseFloat(latest.grossProfit || 0),
                          )}
                        </td>
                      </tr>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Operating Income
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(
                            Number.parseFloat(latest.operatingIncome || 0),
                          )}
                        </td>
                      </tr>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Net Income
                        </td>
                        <td className="text-right px-4 py-3 font-medium text-primary">
                          {formatCurrency(
                            Number.parseFloat(latest.netIncome || 0),
                          )}
                        </td>
                      </tr>
                      <tr className="hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          EBITDA
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(
                            Number.parseFloat(latest.ebitda || 0),
                          )}
                        </td>
                      </tr>
                    </>
                  );
                })()}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground p-4">
            No income statement data available
          </p>
        )}
      </CollapsibleTable>

      {/* Balance Sheet */}
      <CollapsibleTable title="Balance Sheet" defaultOpen={false}>
        {balanceSheet?.available === false ? (
          <p className="text-sm text-muted-foreground p-4">
            {balanceSheet.message}
          </p>
        ) : balanceSheet?.data?.annualReports?.[0] ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-4 py-3 font-semibold text-foreground">
                    Metric
                  </th>
                  <th className="text-right px-4 py-3 font-semibold text-foreground">
                    Value
                  </th>
                </tr>
              </thead>
              <tbody>
                {(() => {
                  const latest = balanceSheet.data.annualReports[0];
                  return (
                    <>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Total Assets
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(
                            Number.parseFloat(latest.totalAssets || 0),
                          )}
                        </td>
                      </tr>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Total Liabilities
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(
                            Number.parseFloat(latest.totalLiabilities || 0),
                          )}
                        </td>
                      </tr>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Shareholder Equity
                        </td>
                        <td className="text-right px-4 py-3 font-medium text-primary">
                          {formatCurrency(
                            Number.parseFloat(
                              latest.totalShareholderEquity || 0,
                            ),
                          )}
                        </td>
                      </tr>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Cash & Equivalents
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(
                            Number.parseFloat(
                              latest.cashAndCashEquivalentsAtCarryingValue || 0,
                            ),
                          )}
                        </td>
                      </tr>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Total Debt
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(
                            Number.parseFloat(
                              latest.shortLongTermDebtTotal || 0,
                            ),
                          )}
                        </td>
                      </tr>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Current Assets
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(
                            Number.parseFloat(latest.totalCurrentAssets || 0),
                          )}
                        </td>
                      </tr>
                      <tr className="hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Current Liabilities
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(
                            Number.parseFloat(
                              latest.totalCurrentLiabilities || 0,
                            ),
                          )}
                        </td>
                      </tr>
                    </>
                  );
                })()}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground p-4">
            No balance sheet data available
          </p>
        )}
      </CollapsibleTable>

      {/* Cash Flow */}
      <CollapsibleTable title="Cash Flow Statement" defaultOpen={false}>
        {cashFlow?.available === false ? (
          <p className="text-sm text-muted-foreground p-4">
            {cashFlow.message}
          </p>
        ) : cashFlow?.data?.annualReports?.[0] ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-4 py-3 font-semibold text-foreground">
                    Metric
                  </th>
                  <th className="text-right px-4 py-3 font-semibold text-foreground">
                    Value
                  </th>
                </tr>
              </thead>
              <tbody>
                {(() => {
                  const latest = cashFlow.data.annualReports[0];
                  const opCF = Number.parseFloat(latest.operatingCashflow || 0);
                  const capex = Math.abs(
                    Number.parseFloat(latest.capitalExpenditures || 0),
                  );
                  return (
                    <>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Operating Cash Flow
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(opCF)}
                        </td>
                      </tr>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Capital Expenditures
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(capex)}
                        </td>
                      </tr>
                      <tr className="border-b border-border/50 hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Free Cash Flow
                        </td>
                        <td className="text-right px-4 py-3 font-medium text-primary">
                          {formatCurrency(opCF - capex)}
                        </td>
                      </tr>
                      <tr className="hover:bg-background/50">
                        <td className="px-4 py-3 text-muted-foreground">
                          Dividends Paid
                        </td>
                        <td className="text-right px-4 py-3 font-medium">
                          {formatCurrency(
                            Math.abs(
                              Number.parseFloat(latest.dividendPayout || 0),
                            ),
                          )}
                        </td>
                      </tr>
                    </>
                  );
                })()}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground p-4">
            No cash flow data available
          </p>
        )}
      </CollapsibleTable>

      {/* Earnings */}
      <CollapsibleTable title="Quarterly Earnings" defaultOpen={false}>
        {earnings?.available === false ? (
          <p className="text-sm text-muted-foreground p-4">
            {earnings.message}
          </p>
        ) : earnings?.data?.quarterlyEarnings?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-4 py-3 font-semibold text-foreground">
                    Quarter
                  </th>
                  <th className="text-right px-4 py-3 font-semibold text-foreground">
                    Reported EPS
                  </th>
                  <th className="text-right px-4 py-3 font-semibold text-foreground">
                    Estimated EPS
                  </th>
                  <th className="text-right px-4 py-3 font-semibold text-foreground">
                    Surprise
                  </th>
                </tr>
              </thead>
              <tbody>
                {earnings.data.quarterlyEarnings
                  .slice(0, 8)
                  .map((quarter: any, idx: number) => (
                    <tr
                      key={idx}
                      className="border-b border-border/50 hover:bg-background/50"
                    >
                      <td className="px-4 py-3 text-muted-foreground">
                        {quarter.fiscalDateEnding}
                      </td>
                      <td className="text-right px-4 py-3 font-medium">
                        ${quarter.reportedEPS}
                      </td>
                      <td className="text-right px-4 py-3 font-medium">
                        ${quarter.estimatedEPS}
                      </td>
                      <td
                        className={`text-right px-4 py-3 font-medium ${Number.parseFloat(quarter.surprise || 0) >= 0 ? "text-green-500" : "text-red-500"}`}
                      >
                        {quarter.surprise} ({quarter.surprisePercentage}%)
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground p-4">
            No earnings data available
          </p>
        )}
      </CollapsibleTable>
    </div>
  );
}
