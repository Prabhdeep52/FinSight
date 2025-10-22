import type React from "react"
import { TrendingUp, TrendingDown } from "lucide-react"

interface Stock {
  symbol: string
  stockData: Record<string, unknown>
  statementData: Record<string, unknown>
}

interface WatchlistSectionProps {
  symbols: string[]
  stocks: Stock[]
}

export const WatchlistSection: React.FC<WatchlistSectionProps> = ({ symbols, stocks }) => {
  // Mock price data - in real app, this would come from API
  const getPriceData = (symbol: string) => {
    const stock = stocks.find((s) => s.symbol === symbol)
    const basePrice = Math.random() * 300 + 50
    const change = (Math.random() - 0.5) * 20
    const changePercent = (change / basePrice) * 100

    return {
      price: basePrice.toFixed(2),
      change: change.toFixed(2),
      changePercent: changePercent.toFixed(2),
      isPositive: change > 0,
    }
  }

  if (symbols.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p className="text-sm">No stocks in watchlist</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {symbols.map((symbol) => {
        const priceData = getPriceData(symbol)
        return (
          <div
            key={symbol}
            className="p-3 rounded-lg border border-border hover:border-primary/50 transition-colors cursor-pointer group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-foreground group-hover:text-primary transition-colors">{symbol}</span>
              <span className="text-sm font-medium text-foreground">${priceData.price}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1">
                {priceData.isPositive ? (
                  <TrendingUp className="w-4 h-4 text-green-500" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-500" />
                )}
                <span className={`text-xs font-medium ${priceData.isPositive ? "text-green-500" : "text-red-500"}`}>
                  {priceData.isPositive ? "+" : ""}
                  {priceData.change} ({priceData.changePercent}%)
                </span>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
