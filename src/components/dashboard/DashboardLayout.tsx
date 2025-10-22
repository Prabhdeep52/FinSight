"use client"

import type React from "react"
import { useMemo } from "react"
import { TrendingUp, Newspaper, Eye } from "lucide-react"
import { FinancialDashboard } from "./FinancialDashboard"
import { NewsSection } from "./sections/NewsSection"
import { WatchlistSection } from "./sections/WatchlistSection"
import { ExecutionLogTable } from "./sections/ExecutionLogTable"

interface Stock {
  symbol: string
  stockData: Record<string, unknown>
  statementData: Record<string, unknown>
}

interface StreamEvent {
  type: string
  step: string
  message: string
  reasoning?: string
  progress?: number
}

interface DashboardLayoutProps {
  stocks: Stock[]
  streamEvents: StreamEvent[]
  isStreaming: boolean
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ stocks, streamEvents, isStreaming }) => {
  // Extract unique symbols for watchlist
  const watchlistSymbols = useMemo(() => {
    return [...new Set(stocks.map((s) => s.symbol))]
  }, [stocks])

  // Generate mock news based on stocks
  const newsItems = useMemo(() => {
    if (stocks.length === 0) return []

    return stocks
      .flatMap((stock) => [
        {
          id: `${stock.symbol}-1`,
          symbol: stock.symbol,
          title: `${stock.symbol} Reports Strong Q3 Earnings`,
          source: "Financial Times",
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
          sentiment: "positive",
        },
        {
          id: `${stock.symbol}-2`,
          symbol: stock.symbol,
          title: `Analyst Upgrades ${stock.symbol} to Buy`,
          source: "Bloomberg",
          timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000),
          sentiment: "positive",
        },
        {
          id: `${stock.symbol}-3`,
          symbol: stock.symbol,
          title: `${stock.symbol} Announces New Product Launch`,
          source: "Reuters",
          timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
          sentiment: "neutral",
        },
      ])
      .slice(0, 6)
  }, [stocks])

  return (
    <div className="h-full overflow-y-auto bg-background">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
        {/* Main Financial Dashboard - Takes 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          {/* Financial Tables */}
          <div className="bg-card rounded-lg border border-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold">Financial Analysis</h2>
            </div>
            <FinancialDashboard stocks={stocks} />
          </div>

          {/* Execution Log */}
          {streamEvents.length > 0 && (
            <div className="bg-card rounded-lg border border-border p-6">
              <h2 className="text-lg font-semibold mb-4">Agent Execution Log</h2>
              <ExecutionLogTable events={streamEvents} isStreaming={isStreaming} />
            </div>
          )}
        </div>

        {/* Right Sidebar - News & Watchlist */}
        <div className="space-y-6">
          {/* Watchlist */}
          <div className="bg-card rounded-lg border border-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Eye className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold">Watchlist</h2>
            </div>
            <WatchlistSection symbols={watchlistSymbols} stocks={stocks} />
          </div>

          {/* News */}
          <div className="bg-card rounded-lg border border-border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Newspaper className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold">Latest News</h2>
            </div>
            <NewsSection newsItems={newsItems} />
          </div>
        </div>
      </div>
    </div>
  )
}
