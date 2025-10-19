"use client"

import type React from "react"

interface ChatInputProps {
  query: string
  setQuery: (query: string) => void
  analysisType: string
  setAnalysisType: (type: string) => void
  isLoading: boolean
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void
  textareaRef: React.RefObject<HTMLTextAreaElement | null>
}


export default function ChatInput({
  query,
  setQuery,
  isLoading,
  onSubmit,
  onKeyDown,
  textareaRef,
}: ChatInputProps) {
  return (
    <div className="border-border  px-4 py-4">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={onSubmit} className="space-y-3">
          <div className="flex gap-3">
            <textarea
              ref={textareaRef}
              className="flex-1 px-4 py-3 rounded-lg bg-background text-foreground placeholder-muted-foreground border-2 border-border focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary resize-none scrollbar-hide"
              placeholder="Ask about any stock or company..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-4 py-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isLoading ? "Sending..." : "Send"}
            </button>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Press Enter to send, Shift+Enter for new line</span>
          </div>
        </form>
      </div>
    </div>
  )
}
