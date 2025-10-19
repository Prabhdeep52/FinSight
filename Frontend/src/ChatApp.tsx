/* eslint-disable @typescript-eslint/no-unused-vars */

"use client"

import type React from "react"

import { type FormEvent, useState, useEffect, useRef } from "react"
import ChatHeader from "./chat-header"
import ChatMessages from "./chat-messages"
import ChatInput from  "./chat-input"
import { AgentProgressSidebar } from "./components/AgentProgressSidebar"
import { streamAgentQuery, type StreamEvent, type StreamEventData } from "./services/streamingService"
import { Activity } from "lucide-react"

type AgentResponse = {
  query: string
  response: string
  symbols_analyzed: string[]
  stock_data: Record<string, Record<string, unknown>>
  statement_data?: Record<string, Record<string, unknown>>
  analysis_results: Record<string, unknown>
  status: string
  error_message?: string | null
}

type ChatMessage = {
  id: string
  role: "user" | "assistant"
  content: string
  symbols?: string[]
  stockData?: Record<string, Record<string, unknown>>
  statementData?: Record<string, Record<string, unknown>>
  timestamp: Date
  isError?: boolean
}

const API_ENDPOINT = "http://localhost:8000/api/v1/agent/query" ; 

export default function ChatApp() {
  const [query, setQuery] = useState("")
  const [analysisType, setAnalysisType] = useState("comprehensive")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  
  // Session management for conversation continuity
  const [sessionId, setSessionId] = useState<string>("")
  const [userId] = useState<string>("user_" + Date.now()) // In production, get from auth
  
  // Streaming state
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([])
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)

  const abortControllerRef = useRef<AbortController | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  // Generate session ID on mount (creates new conversation)
  useEffect(() => {
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    setSessionId(newSessionId)
    console.log("🆕 New chat session started:", newSessionId)
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [query])

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort()
    }
  }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!query.trim()) {
      return
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: query.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const userQuery = query.trim()
    setQuery("")
    setIsLoading(true)
    setIsStreaming(true)
    
    // Add a separator for follow-up questions instead of clearing
    if (streamEvents.length > 0) {
      setStreamEvents((prev) => [...prev, {
        type: 'step',
        step: 'new_query',
        message: '─── New Query ───',
        reasoning: `Starting analysis for: "${userQuery}"`,
        progress: 0
      }])
    }
    
    setIsSidebarOpen(true) // Auto-open sidebar when query starts

    console.log('🚀 Starting query with session:', sessionId, 'user:', userId);

    try {
      await streamAgentQuery(
        userQuery,
        sessionId,
        userId,
        // onProgress
        (event: StreamEvent) => {
          console.log('📊 Progress event:', event);
          setStreamEvents((prev) => [...prev, event])
        },
        // onComplete
        (data: StreamEventData) => {
          const assistantMessage: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: data.response || "No response generated",
            symbols: data.symbols_analyzed,
            stockData: data.stock_data as Record<string, Record<string, unknown>>,
            statementData: data.statement_data as Record<string, Record<string, unknown>>,
            timestamp: new Date(),
          }
          setMessages((prev) => [...prev, assistantMessage])
          setIsLoading(false)
          setIsStreaming(false)
        },
        // onError
        (error) => {
          console.error('❌ Stream error:', error)
          const errorMessage: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: `Error: ${error}`,
            timestamp: new Date(),
            isError: true,
          }
          setMessages((prev) => [...prev, errorMessage])
          setIsLoading(false)
          setIsStreaming(false)
        }
      )
    } catch (err) {
      const errorMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: "Something went wrong while contacting the agent. Please try again.",
        timestamp: new Date(),
        isError: true,
      }
      setMessages((prev) => [...prev, errorMessage])
      setIsLoading(false)
      setIsStreaming(false)
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      handleSubmit(event as unknown as FormEvent<HTMLFormElement>)
    }
  }

  const handleClear = () => {
    abortControllerRef.current?.abort()
    setMessages([])
    setQuery("")
    setIsLoading(false)
    setStreamEvents([])  // Clear thinking panel too
  }
  
  const handleNewChat = async () => {
    // Clear session cache on backend
    try {
      await fetch('http://localhost:8000/api/v1/agent/clear-session-cache', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      })
      console.log("🧹 Cleared session cache for:", sessionId)
    } catch (error) {
      console.warn("Failed to clear session cache:", error)
    }
    
    // Start a completely new conversation with new session ID
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    setSessionId(newSessionId)
    setMessages([])
    setQuery("")
    setIsLoading(false)
    setStreamEvents([])
    console.log("🆕 New chat session started:", newSessionId)
  }

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <ChatHeader 
        onClear={handleClear}
        onNewChat={handleNewChat}
        hasMessages={messages.length > 0} 
        isLoading={isLoading}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        isSidebarOpen={isSidebarOpen}
        isStreaming={isStreaming}
      />
      <ChatMessages messages={messages} isLoading={isLoading} chatEndRef={chatEndRef} />
      <ChatInput
        query={query}
        setQuery={setQuery}
        analysisType={analysisType}
        setAnalysisType={setAnalysisType}
        isLoading={isLoading}
        onSubmit={handleSubmit}
        onKeyDown={handleKeyDown}
        textareaRef={textareaRef}
      />
      
      {/* Agent Progress Sidebar */}
      <AgentProgressSidebar 
        events={streamEvents}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        isStreaming={isStreaming}
      />
    </div>
  )
}
