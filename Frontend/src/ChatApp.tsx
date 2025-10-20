/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */

"use client"

import type React from "react"

import { type FormEvent, useState, useEffect, useRef, useMemo } from "react"
import { useAuth } from "./contexts/AuthContext"
import { useNavigate } from "react-router-dom"
import ChatHeader from "./chat-header"
import ChatMessages from "./chat-messages"
import ChatInput from  "./chat-input"
import { AgentProgressSidebar } from "./components/AgentProgressSidebar"
import { ChatHistorySidebar, type ChatHistorySidebarHandle } from "./components/ChatHistorySidebar"
import { FinancialDashboard } from "./components/dashboard/FinancialDashboard"
import { streamAgentQuery, type StreamEvent, type StreamEventData } from "./services/streamingService"

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
  const { userId, accessToken, logout } = useAuth()
  const navigate = useNavigate()
  
  const [query, setQuery] = useState("")
  const [analysisType, setAnalysisType] = useState("comprehensive")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  
  // Session management for conversation continuity
  const [sessionId, setSessionId] = useState<string>("")
  
  // Streaming state
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([])
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [isChatHistoryOpen, setIsChatHistoryOpen] = useState(false)

  const abortControllerRef = useRef<AbortController | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const chatHistorySidebarRef = useRef<ChatHistorySidebarHandle>(null)
  
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

    // If this is the first message in a new chat, update the conversation title immediately
    if (messages.length === 0 && accessToken) {
      try {
        await fetch(`http://localhost:8000/api/v1/agent/update-conversation-title`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            session_id: sessionId,
            title: userQuery.length > 60 ? userQuery.substring(0, 57) + "..." : userQuery,
          }),
        });
        console.log('✅ Updated conversation title');
        
        // Refresh chat history sidebar to show the new conversation
        chatHistorySidebarRef.current?.refresh();
      } catch (err) {
        console.error('Failed to update conversation title:', err);
      }
    }

    // Track thinking events for this specific query
    const currentQueryEvents: StreamEvent[] = [];

    try {
      await streamAgentQuery(
        userQuery,
        sessionId,
        userId || '',
        accessToken,
        // onProgress
        (event: StreamEvent) => {
          console.log('📊 Progress event:', event);
          setStreamEvents((prev) => [...prev, event])
          // Collect events for this query only (exclude separators)
          if (event.step !== 'new_query') {
            currentQueryEvents.push(event);
          }
        },
        // onComplete
        async (data: StreamEventData) => {
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
          
          // Save thinking events to backend
          try {
            if (accessToken && currentQueryEvents.length > 0) {
              await fetch(`http://localhost:8000/api/v1/agent/save-thinking/${sessionId}`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${accessToken}`,
                },
                body: JSON.stringify({
                  thinking: currentQueryEvents,
                  query: userQuery,
                }),
              });
              console.log('✅ Saved thinking events to backend');
            }
          } catch (err) {
            console.error('Failed to save thinking events:', err);
          }
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
      const headers: HeadersInit = { 'Content-Type': 'application/json' };
      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }
      
      await fetch('http://localhost:8000/api/v1/agent/clear-session-cache', {
        method: 'POST',
        headers,
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

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleSelectChat = async (selectedSessionId: string) => {
    if (!accessToken) return;

    try {
      // Fetch messages for this conversation
      const response = await fetch(
        `http://localhost:8000/api/v1/agent/chat-messages/${selectedSessionId}`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to load conversation');
      }

      const data = await response.json();
      
      // Load messages
      const loadedMessages: ChatMessage[] = data.messages.map((msg: any) => ({
        id: `${msg.role}-${msg.id}`,
        role: msg.role,
        content: msg.content,
        symbols: msg.metadata?.symbols,
        stockData: msg.metadata?.stock_data,
        statementData: msg.metadata?.statement_data,
        timestamp: new Date(msg.created_at),
        isError: false,
      }));

      setMessages(loadedMessages);
      setSessionId(selectedSessionId);
      
      // Load thinking_history directly from conversation
      const thinkingHistory = data.thinking_history || [];
      setStreamEvents(thinkingHistory);
      
      console.log('✅ Loaded conversation:', selectedSessionId);
      console.log(`   Messages: ${loadedMessages.length}`);
      console.log(`   Thinking events: ${thinkingHistory.length}`);
      
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };

  // Extract stock data for dashboard
  const dashboardStocks = useMemo(() => {
    // Get the last assistant message with stock data
    const lastAssistantMsg = messages.slice().reverse().find(m => m.role === 'assistant' && m.stockData);
    
    if (!lastAssistantMsg || !lastAssistantMsg.symbols || !lastAssistantMsg.stockData) {
      return [];
    }

    return lastAssistantMsg.symbols.map(symbol => ({
      symbol,
      stockData: lastAssistantMsg.stockData?.[symbol] || {},
      statementData: lastAssistantMsg.statementData?.[symbol] || {},
    }));
  }, [messages]);

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <ChatHeader 
        onClear={handleClear}
        onNewChat={handleNewChat}
        onLogout={handleLogout}
        onToggleChatHistory={() => setIsChatHistoryOpen(!isChatHistoryOpen)}
        hasMessages={messages.length > 0} 
        isLoading={isLoading}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        isSidebarOpen={isSidebarOpen}
        isStreaming={isStreaming}
      />
      
      {/* Main Content: Dashboard (70%) + Chat (30%) */}
      <div className="flex flex-1 overflow-hidden">
        {/* Financial Dashboard */}
        <div className="flex-[7] border-r border-gray-700">
          <FinancialDashboard stocks={dashboardStocks} />
        </div>

        {/* Chat Section */}
        <div className="flex-[3] flex flex-col">
          <div className="flex-1 overflow-y-auto">
            <ChatMessages messages={messages} isLoading={isLoading} chatEndRef={chatEndRef} />
          </div>
          <div className="border-t border-gray-700">
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
          </div>
        </div>
      </div>
      
      {/* Agent Progress Sidebar */}
      <AgentProgressSidebar 
        events={streamEvents}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        isStreaming={isStreaming}
      />
      
      {/* Chat History Sidebar */}
      <ChatHistorySidebar
        ref={chatHistorySidebarRef}
        isOpen={isChatHistoryOpen}
        onClose={() => setIsChatHistoryOpen(false)}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        currentSessionId={sessionId}
        userId={userId}
        accessToken={accessToken}
      />
    </div>
  )
}
