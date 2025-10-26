/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
"use client";

import React, {
  useState,
  useEffect,
  useRef,
  useMemo,
  type FormEvent,
} from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";

import ChatHeader from "./chat-header";
import ChatMessages from "./chat-messages";
import ChatInput from "./chat-input";
import { BACKEND_URL } from "./contexts/settings";
import { FinancialDashboard } from "./components/dashboard/FinancialDashboard";
import { AgentProgressSidebar } from "./components/AgentProgressSidebar";
import {
  ChatHistorySidebar,
  type ChatHistorySidebarHandle,
} from "./components/ChatHistorySidebar";

import {
  streamAgentQuery,
  type StreamEvent,
  type StreamEventData,
} from "./services/streamingService";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  symbols?: string[];
  stockData?: Record<string, Record<string, unknown>>;
  statementData?: Record<string, Record<string, unknown>>;
  timestamp: Date;
  isError?: boolean;
};

export default function ChatApp() {
  const { userId, accessToken, logout } = useAuth();
  const navigate = useNavigate();

  const [query, setQuery] = useState("");
  const [analysisType, setAnalysisType] = useState("comprehensive");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const [sessionId, setSessionId] = useState<string>("");
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isChatHistoryOpen, setIsChatHistoryOpen] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const chatHistorySidebarRef = useRef<ChatHistorySidebarHandle>(null);

  // Generate a new session ID on mount
  useEffect(() => {
    const newSessionId = `session-${Date.now()}-${Math.random()
      .toString(36)
      .substr(2, 9)}`;
    setSessionId(newSessionId);
    console.log("🆕 New chat session started:", newSessionId);
  }, []);

  // Auto scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [query]);

  // Cleanup
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  // Handle query submission
  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!query.trim()) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: query.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const userQuery = query.trim();
    setQuery("");
    setIsLoading(true);
    setIsStreaming(true);

    if (streamEvents.length > 0) {
      setStreamEvents((prev) => [
        ...prev,
        {
          type: "step",
          step: "new_query",
          message: "─── New Query ───",
          reasoning: `Starting analysis for: "${userQuery}"`,
          progress: 0,
        },
      ]);
    }

    setIsSidebarOpen(true);

    console.log("🚀 Starting query with session:", sessionId, "user:", userId);

    if (messages.length === 0 && accessToken) {
      try {
        await fetch(`${BACKEND_URL}/api/v1/agent/update-conversation-title`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            session_id: sessionId,
            title:
              userQuery.length > 60
                ? userQuery.substring(0, 57) + "..."
                : userQuery,
          }),
        });
        console.log("✅ Updated conversation title");
        chatHistorySidebarRef.current?.refresh();
      } catch (err) {
        console.error("Failed to update conversation title:", err);
      }
    }

    const currentQueryEvents: StreamEvent[] = [];

    try {
      await streamAgentQuery(
        userQuery,
        sessionId,
        userId || "",
        accessToken,
        // onProgress
        (event: StreamEvent) => {
          console.log("📊 Progress event:", event);
          setStreamEvents((prev) => [...prev, event]);
          if (event.step !== "new_query") {
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
            stockData: data.stock_data as Record<
              string,
              Record<string, unknown>
            >,
            statementData: data.statement_data as Record<
              string,
              Record<string, unknown>
            >,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
          setIsLoading(false);
          setIsStreaming(false);

          try {
            if (accessToken && currentQueryEvents.length > 0) {
              await fetch(
                `${BACKEND_URL}/api/v1/agent/save-thinking/${sessionId}`,
                {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${accessToken}`,
                  },
                  body: JSON.stringify({
                    thinking: currentQueryEvents,
                    query: userQuery,
                  }),
                },
              );
              console.log("✅ Saved thinking events to backend");
            }
          } catch (err) {
            console.error("Failed to save thinking events:", err);
          }
        },
        // onError
        (error) => {
          console.error("❌ Stream error:", error);
          const errorMessage: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: `Error: ${error}`,
            timestamp: new Date(),
            isError: true,
          };
          setMessages((prev) => [...prev, errorMessage]);
          setIsLoading(false);
          setIsStreaming(false);
        },
      );
    } catch (err) {
      const errorMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content:
          "Something went wrong while contacting the agent. Please try again.",
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  // New function to handle example selection
  const handleSelectExample = (exampleText: string) => {
    setQuery(exampleText);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event as unknown as FormEvent<HTMLFormElement>);
    }
  };

  const handleClear = () => {
    abortControllerRef.current?.abort();
    setMessages([]);
    setQuery("");
    setIsLoading(false);
    setStreamEvents([]);
  };

  const handleNewChat = async () => {
    try {
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

      await fetch("${BACKEND_URL}/api/v1/agent/clear-session-cache", {
        method: "POST",
        headers,
        body: JSON.stringify({ session_id: sessionId }),
      });
      console.log("🧹 Cleared session cache for:", sessionId);
    } catch (error) {
      console.warn("Failed to clear session cache:", error);
    }

    const newSessionId = `session-${Date.now()}-${Math.random()
      .toString(36)
      .substr(2, 9)}`;
    setSessionId(newSessionId);
    setMessages([]);
    setQuery("");
    setIsLoading(false);
    setStreamEvents([]);
    console.log("🆕 New chat session started:", newSessionId);
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleSelectChat = async (selectedSessionId: string) => {
    if (!accessToken) return;
    try {
      const response = await fetch(
        `${BACKEND_URL}/api/v1/agent/chat-messages/${selectedSessionId}`,
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        },
      );

      if (!response.ok) throw new Error("Failed to load conversation");
      const data = await response.json();

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

      const thinkingHistory = data.thinking_history || [];
      setStreamEvents(thinkingHistory);

      console.log("✅ Loaded conversation:", selectedSessionId);
    } catch (error) {
      console.error("Error loading conversation:", error);
    }
  };

  // Prepare dashboard data
  const dashboardStocks = useMemo(() => {
    const lastAssistantMsg = messages
      .slice()
      .reverse()
      .find((m) => m.role === "assistant" && m.stockData);

    if (
      !lastAssistantMsg ||
      !lastAssistantMsg.symbols ||
      !lastAssistantMsg.stockData
    ) {
      return [];
    }

    return lastAssistantMsg.symbols.map((symbol) => ({
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

      {/* Resizable Main Layout */}
      <PanelGroup direction="horizontal" className="flex-1">
        <Panel defaultSize={70} minSize={40}>
          <div className="border-r border-gray-700 h-full overflow-hidden">
            <FinancialDashboard stocks={dashboardStocks} />
          </div>
        </Panel>

        <PanelResizeHandle className="w-1 bg-gray-700 hover:bg-primary cursor-col-resize transition" />

        <Panel defaultSize={30} minSize={20}>
          <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto custom-scrollbar">
              <ChatMessages
                messages={messages}
                isLoading={isLoading}
                chatEndRef={chatEndRef}
                onSelectExample={handleSelectExample}
              />
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
        </Panel>
      </PanelGroup>

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
  );
}
