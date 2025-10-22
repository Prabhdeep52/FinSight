"use client";

import type React from "react";

import { useEffect } from "react";
import ReactMarkdown from "react-markdown";
import StockCard from "./stock-card";
import FinancialTables from "./financial-tables";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  symbols?: string[];
  stockData?: Record<string, Record<string, unknown>>;
  statementData?: Record<string, Record<string, unknown>>;
  timestamp: Date;
  isError?: boolean;
};

interface ChatMessagesProps {
  messages: ChatMessage[];
  isLoading: boolean;
  chatEndRef: React.RefObject<HTMLDivElement | null>;
}

export default function ChatMessages({
  messages,
  isLoading,
  chatEndRef,
}: ChatMessagesProps) {
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chatEndRef]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="text-5xl font-light mb-4 text-primary">▲</div>
          <h2 className="text-2xl font-semibold mb-2">
            Welcome to Finance Bro
          </h2>
          <p className="text-muted-foreground mb-8">
            Ask me anything about stocks, companies, or financial markets
          </p>
          <div className="space-y-3">
            <p className="text-sm font-medium text-muted-foreground">
              Try asking:
            </p>
            <div className="space-y-2">
              <button className="w-full px-4 py-3 rounded-lg bg-card border border-border hover:border-primary/50 text-left text-sm transition-colors">
                Analyze Apple stock
              </button>
              <button className="w-full px-4 py-3 rounded-lg bg-card border border-border hover:border-primary/50 text-left text-sm transition-colors">
                Compare Microsoft and Google
              </button>
              <button className="w-full px-4 py-3 rounded-lg bg-card border border-border hover:border-primary/50 text-left text-sm transition-colors">
                What is the valuation of Tesla?
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto no-scrollbar">
      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-4 ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {message.role === "assistant" && (
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-semibold text-sm">
                AI
              </div>
            )}

            <div
              className={`flex-1 max-w-2xl ${message.role === "user" ? "text-right" : ""}`}
            >
              <div
                className={`inline-block px-4 py-3 rounded-lg ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-card border border-border"
                }`}
              >
                {message.role === "user" ? (
                  <p className="text-sm">{message.content}</p>
                ) : (
                  <div className="space-y-4">
                    {message.symbols &&
                      message.symbols.length > 0 &&
                      message.stockData && (
                        <div className="space-y-3">
                          {message.symbols.map((symbol) =>
                            message.stockData?.[symbol] ? (
                              <StockCard
                                key={symbol}
                                symbol={symbol}
                                data={message.stockData[symbol]}
                              />
                            ) : null,
                          )}
                        </div>
                      )}

                    {message.symbols &&
                      message.symbols.length > 0 &&
                      message.statementData && (
                        <div className="space-y-4">
                          {message.symbols.map((symbol) =>
                            message.statementData?.[symbol] ? (
                              <FinancialTables
                                key={symbol}
                                symbol={symbol}
                                data={message.statementData[symbol]}
                              />
                            ) : null,
                          )}
                        </div>
                      )}

                    <div
                      className={`text-sm prose prose-invert max-w-none ${message.isError ? "text-destructive" : "text-foreground"}`}
                    >
                      <ReactMarkdown
                        components={{
                          h1: ({ children }) => (
                            <h1 className="text-lg font-bold mt-4 mb-2">
                              {children}
                            </h1>
                          ),
                          h2: ({ children }) => (
                            <h2 className="text-base font-semibold mt-3 mb-2">
                              {children}
                            </h2>
                          ),
                          h3: ({ children }) => (
                            <h3 className="text-sm font-semibold mt-2 mb-1">
                              {children}
                            </h3>
                          ),
                          p: ({ children }) => (
                            <p className="mb-2">{children}</p>
                          ),
                          strong: ({ children }) => (
                            <strong className="font-semibold">
                              {children}
                            </strong>
                          ),
                          em: ({ children }) => (
                            <em className="italic">{children}</em>
                          ),
                          ul: ({ children }) => (
                            <ul className="list-disc list-inside mb-2 space-y-1">
                              {children}
                            </ul>
                          ),
                          ol: ({ children }) => (
                            <ol className="list-decimal list-inside mb-2 space-y-1">
                              {children}
                            </ol>
                          ),
                          li: ({ children }) => (
                            <li className="text-sm">{children}</li>
                          ),
                          code: ({ children }) => (
                            <code className="bg-muted px-2 py-1 rounded text-xs font-mono">
                              {children}
                            </code>
                          ),
                          pre: ({ children }) => (
                            <pre className="bg-muted p-3 rounded overflow-x-auto text-xs">
                              {children}
                            </pre>
                          ),
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                {message.timestamp.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>

            {message.role === "user" && (
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-semibold text-sm">
                U
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-semibold text-sm">
              AI
            </div>
            <div className="flex-1 max-w-2xl">
              <div className="inline-block px-4 py-3 rounded-lg bg-card border border-border">
                <div className="flex gap-2">
                  <div className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" />
                  <div
                    className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce"
                    style={{ animationDelay: "0.1s" }}
                  />
                  <div
                    className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce"
                    style={{ animationDelay: "0.2s" }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>
    </div>
  );
}
