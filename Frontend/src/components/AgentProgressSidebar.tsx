"use client";

import type React from "react";
import type { StreamEvent } from "../services/streamingService";
import { X, CheckCircle, XCircle, AlertCircle, SkipForward } from "lucide-react";

interface AgentProgressSidebarProps {
  events: StreamEvent[];
  isOpen: boolean;
  onClose: () => void;
  isStreaming: boolean;
}

export const AgentProgressSidebar: React.FC<AgentProgressSidebarProps> = ({
  events,
  isOpen,
  onClose,
  isStreaming,
}) => {
  const latestEvent = events[events.length - 1];
  const progress = latestEvent?.progress || 0;

  const getEventIcon = (event: StreamEvent) => {
    switch (event.type) {
      case "tool_success":
      case "complete":
        return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case "tool_error":
      case "error":
        return <XCircle className="w-4 h-4 text-red-400" />;
      case "tool_skip":
      case "warning":
        return <AlertCircle className="w-4 h-4 text-amber-400" />;
      default:
        return <SkipForward className="w-4 h-4 text-purple-400" />;
    }
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed top-0 right-0 h-screen w-full sm:w-96 
        bg-black/80 backdrop-blur-xl border-l border-white/10 
        shadow-[0_0_25px_rgba(168,85,247,0.15)] z-50 
        transition-transform duration-300 ease-in-out 
        flex flex-col ${isOpen ? "translate-x-0" : "translate-x-full"}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10 bg-white/5 backdrop-blur-sm sticky top-0">
          <div className="flex items-center space-x-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isStreaming ? "bg-purple-500 animate-pulse" : "bg-slate-600"
              }`}
            />
            <h2 className="text-sm font-medium text-white/80">
              Excecution logs
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5 text-white/60" />
          </button>
        </div>

        {/* Progress Bar */}
        {isStreaming && (
          <div className="px-4 py-3 border-b border-white/10 bg-white/5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-white/50">Progress</span>
              <span className="text-xs font-medium text-white/80">
                {progress}%
              </span>
            </div>
            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Current Status */}
        {latestEvent && (
          <div className="px-4 py-3 border-b border-white/10 bg-white/5">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 mt-0.5">
                {getEventIcon(latestEvent)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-white/80 break-words">
                  {latestEvent.message}
                </p>
                {latestEvent.symbol && (
                  <p className="text-xs text-purple-400 mt-1 font-mono">
                    {latestEvent.symbol}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Event Timeline */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {events.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-white/40">
              <p className="text-xs">Waiting for agent to start...</p>
            </div>
          ) : (
            <div className="space-y-3">
              {events.map((event, idx) => (
                <div key={idx} className="animate-in slide-in-from-right">
                  {event.step === "new_query" ? (
                    <div className="py-4">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-purple-500/40 to-transparent" />
                        <span className="text-xs font-medium text-purple-400">
                          New Query
                        </span>
                        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-purple-500/40 to-transparent" />
                      </div>
                      {event.reasoning && (
                        <p className="text-xs text-white/50 text-center italic mt-2">
                          {event.reasoning}
                        </p>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-start space-x-3 text-xs">
                      <div className="flex-shrink-0 mt-0.5">
                        {getEventIcon(event)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-white/80 font-medium break-words">
                            {event.message}
                          </p>
                          {event.iteration && (
                            <span className="text-white/40 text-[10px]">
                              #{event.iteration}
                            </span>
                          )}
                        </div>
                        {event.symbol && (
                          <p className="text-purple-400 font-mono mt-1">
                            {event.symbol}
                          </p>
                        )}
                        {event.tool && (
                          <p className="text-white/40 mt-1">
                            {event.tool
                              .replace("get_", "")
                              .replace(/_/g, " ")}
                          </p>
                        )}
                        {event.reasoning && (
                          <div className="mt-2 pl-3 border-l-2 border-white/10">
                            <p className="text-white/60 text-xs italic leading-relaxed">
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
  );
};
