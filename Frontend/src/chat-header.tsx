"use client"

import { Activity } from "lucide-react"

interface ChatHeaderProps {
  onClear: () => void
  onNewChat?: () => void
  hasMessages: boolean
  isLoading: boolean
  onToggleSidebar: () => void
  isSidebarOpen: boolean
  isStreaming: boolean
}

export default function ChatHeader({ 
  onClear,
  onNewChat,
  hasMessages, 
  isLoading, 
  onToggleSidebar,
  isSidebarOpen,
  isStreaming 
}: ChatHeaderProps) {
  return (
    <header className="px-6 py-4 shadow-sm border-b border-border">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Finance Bro</h1>
          <p className="text-sm text-muted-foreground">Your AI powered Financial Agent</p>
        </div>
        <div className="flex items-center gap-2">
          {/* Agent Progress Button */}
          <button
            onClick={onToggleSidebar}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
              isStreaming
                ? 'bg-green-500/10 text-green-500 hover:bg-green-500/20 animate-pulse'
                : 'bg-muted hover:bg-muted/80 text-muted-foreground'
            } ${isSidebarOpen ? 'ring-2 ring-primary' : ''}`}
            title="View agent progress"
          >
            <Activity className="w-4 h-4" />
            <span className="text-sm font-medium">
              {isStreaming ? 'Processing...' : 'Agent Progress'}
            </span>
          </button>
          
          {hasMessages && (
            <>
              {onNewChat && (
                <button
                  onClick={onNewChat}
                  disabled={isLoading}
                  className="px-4 py-2 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
                >
                  New Chat
                </button>
              )}
              <button
                onClick={onClear}
                disabled={isLoading}
                className="px-4 py-2 rounded-lg bg-destructive/10 text-destructive hover:bg-destructive/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
              >
                Clear Chat
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
