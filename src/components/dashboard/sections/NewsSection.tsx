import type React from "react"
import { ExternalLink } from "lucide-react"

interface NewsItem {
  id: string
  symbol: string
  title: string
  source: string
  timestamp: Date
  sentiment: "positive" | "negative" | "neutral"
}

interface NewsSectionProps {
  newsItems: NewsItem[]
}

export const NewsSection: React.FC<NewsSectionProps> = ({ newsItems }) => {
  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "bg-green-500/10 text-green-600 border-green-500/20"
      case "negative":
        return "bg-red-500/10 text-red-600 border-red-500/20"
      default:
        return "bg-blue-500/10 text-blue-600 border-blue-500/20"
    }
  }

  const formatTime = (date: Date) => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  if (newsItems.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p className="text-sm">No news available</p>
      </div>
    )
  }

  return (
    <div className="space-y-3 max-h-96 overflow-y-auto">
      {newsItems.map((item) => (
        <div
          key={item.id}
          className="p-3 rounded-lg border border-border hover:border-primary/50 transition-colors cursor-pointer group"
        >
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-semibold text-primary">{item.symbol}</span>
                <span className={`text-xs px-2 py-0.5 rounded border ${getSentimentColor(item.sentiment)}`}>
                  {item.sentiment}
                </span>
              </div>
              <h3 className="text-sm font-medium text-foreground group-hover:text-primary transition-colors line-clamp-2">
                {item.title}
              </h3>
            </div>
            <ExternalLink className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0 mt-1" />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">{item.source}</span>
            <span className="text-xs text-muted-foreground">{formatTime(item.timestamp)}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
