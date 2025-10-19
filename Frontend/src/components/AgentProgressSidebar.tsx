"use client"

import type React from "react"
import type { StreamEvent } from "../services/streamingService"
import { X, CheckCircle, XCircle, AlertCircle, SkipForward } from "lucide-react"

interface AgentProgressSidebarProps {
  events: StreamEvent[]
  isOpen: boolean
  onClose: () => void
  isStreaming: boolean
}

export const AgentProgressSidebar: React.FC<AgentProgressSidebarProps> = ({ events, isOpen, onClose, isStreaming }) => {
  const latestEvent = events[events.length - 1]
  const progress = latestEvent?.progress || 0

  // Get icon based on event type
  const getEventIcon = (event: StreamEvent) => {
    switch (event.type) {
      case "tool_success":
        return <CheckCircle className="w-4 h-4 text-emerald-400" />
      case "tool_error":
        return <XCircle className="w-4 h-4 text-red-400" />
      case "tool_skip":
        return <SkipForward className="w-4 h-4 text-amber-400" />
      case "warning":
        return <AlertCircle className="w-4 h-4 text-amber-400" />
      case "error":
        return <XCircle className="w-4 h-4 text-red-400" />
      case "complete":
        return <CheckCircle className="w-4 h-4 text-emerald-400" />
      default:
        return null
    }
  }

  return (
    <>
      {/* Backdrop */}
      {isOpen && <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden" onClick={onClose} />}

      {/* Sidebar */}
      <div
        className={`fixed top-0 right-0 h-screen w-full sm:w-96 bg-slate-950 border-l border-slate-800 shadow-2xl z-50 transition-transform duration-300 ease-in-out flex flex-col ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-950/95 backdrop-blur-sm sticky top-0">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isStreaming ? "bg-purple-500 animate-pulse" : "bg-slate-600"}`} />
            <h2 className="text-sm font-medium text-slate-200">Agent Activity</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* Progress Bar */}
        {isStreaming && (
          <div className="px-4 py-3 border-b border-slate-800 bg-slate-950/80">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-400">Progress</span>
              <span className="text-xs font-medium text-slate-300">{progress}%</span>
            </div>
            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-500 to-purple-600 transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Current Status */}
        {latestEvent && (
          <div className="px-4 py-3 border-b border-slate-800 bg-slate-950/60">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 mt-0.5">{getEventIcon(latestEvent)}</div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-slate-200 break-words">{latestEvent.message}</p>
                {latestEvent.symbol && (
                  <p className="text-xs text-slate-500 mt-1">
                    <span className="font-mono text-purple-400">{latestEvent.symbol}</span>
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Event Timeline */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {events.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500">
              <p className="text-xs">Waiting for agent to start...</p>
            </div>
          ) : (
            <div className="space-y-3">
              {events.map((event, idx) => (
                <div key={idx} className="animate-in slide-in-from-right">
                  {/* New Query Separator */}
                  {event.step === 'new_query' ? (
                    <div className="py-4">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-purple-500/30 to-transparent" />
                        <span className="text-xs font-medium text-purple-400">New Query</span>
                        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-purple-500/30 to-transparent" />
                      </div>
                      {event.reasoning && (
                        <p className="text-xs text-slate-400 text-center italic mt-2">
                          {event.reasoning}
                        </p>
                      )}
                    </div>
                  ) : (
                    /* Regular event */
                    <div className="flex items-start space-x-3 text-xs">
                      <div className="flex-shrink-0 mt-0.5">{getEventIcon(event)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-slate-300 break-words font-medium">{event.message}</p>
                          {event.iteration && <span className="text-slate-500 flex-shrink-0 text-[10px]">#{event.iteration}</span>}
                        </div>
                        {event.symbol && (
                          <p className="text-slate-500 mt-1">
                            <span className="font-mono text-purple-400">{event.symbol}</span>
                          </p>
                        )}
                        {event.tool && (
                          <p className="text-slate-500 mt-1">{event.tool.replace("get_", "").replace(/_/g, " ")}</p>
                        )}
                        
                        {/* Reasoning - conversational explanation */}
                        {event.reasoning && (
                          <div className="mt-2 pl-3 border-l-2 border-slate-700">
                            <p className="text-slate-400 text-xs italic leading-relaxed">
                              {event.reasoning}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
