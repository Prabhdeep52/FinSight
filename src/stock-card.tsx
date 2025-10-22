interface StockCardProps {
  symbol: string
  data: Record<string, unknown>
}

function formatCurrency(value: unknown, currency = "USD") {
  const numericValue = typeof value === "number" ? value : typeof value === "string" ? Number(value) : Number.NaN

  if (!Number.isFinite(numericValue)) {
    return "N/A"
  }

  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      maximumFractionDigits: numericValue >= 1 ? 2 : 4,
    }).format(numericValue)
  } catch {
    return numericValue.toFixed(2)
  }
}

function formatNumber(value: unknown, options: Intl.NumberFormatOptions = {}) {
  const numericValue = typeof value === "number" ? value : typeof value === "string" ? Number(value) : Number.NaN

  if (!Number.isFinite(numericValue)) {
    return "N/A"
  }

  return new Intl.NumberFormat("en-US", options).format(numericValue)
}

export default function StockCard({ symbol, data }: StockCardProps) {
  const currency = (data.currency as string) || "USD"
  
  // Check if this is an empty/missing data scenario (all key fields are missing)
  const hasAnyData = data.current_price || data.market_cap || data.pe_ratio || data.name
  
  if (!hasAnyData) {
    return (
      <div className="bg-background border border-amber-500/50 rounded-lg p-4 space-y-3">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-amber-500/10 flex items-center justify-center">
            <span className="text-amber-500 text-lg">⚠</span>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-foreground mb-1">{symbol}</h3>
            <p className="text-sm text-amber-500/90 font-medium mb-2">Stock Overview Data Unavailable</p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              API rate limit exceeded. Stock overview metrics (Market Cap, P/E Ratio, Price) cannot be fetched at this time. 
              Financial statement data (Income, Balance Sheet, Cash Flow) is still available below if cached.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-background border border-border rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between border-b border-border pb-3">
        <div>
          <h3 className="text-lg font-bold text-foreground">{symbol}</h3>
          <p className="text-sm text-muted-foreground">{(data.name as string) ?? "N/A"}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-primary">{formatCurrency(data.current_price, currency)}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground uppercase">Market Cap</p>
          <p className="text-sm font-semibold text-foreground">
            {formatNumber(data.market_cap as number, { notation: "compact", maximumFractionDigits: 2 })}
          </p>
        </div>
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground uppercase">P/E Ratio</p>
          <p className="text-sm font-semibold text-foreground">
            {formatNumber(data.pe_ratio as number, { maximumFractionDigits: 2 })}
          </p>
        </div>
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground uppercase">52W Low</p>
          <p className="text-sm font-semibold text-foreground">{formatCurrency(data.low_52week, currency)}</p>
        </div>
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground uppercase">52W High</p>
          <p className="text-sm font-semibold text-foreground">{formatCurrency(data.high_52week, currency)}</p>
        </div>
      </div>
    </div>
  )
}
