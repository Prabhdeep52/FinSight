import React from 'react';
import { FinancialDashboard } from './components/dashboard/FinancialDashboard';
import { AgentProgressSidebar } from './components/AgentProgressSidebar';
import { ChatHistorySidebar, type ChatHistorySidebarHandle } from "./components/ChatHistorySidebar";
import ChatInput from './chat-input';
import ChatMessages from './chat-messages';
import { type StreamEvent } from "./services/streamingService";
import { type ChatMessage } from "./ChatApp";

type DashboardProps = {
  stocks: any[];
  events: StreamEvent[];
  messages: ChatMessage[];
  isLoading: boolean;
  chatEndRef: React.RefObject<HTMLDivElement>;
  isStreaming: boolean;
  query: string;
  setQuery: (query: string) => void;
  analysisType: string;
  setAnalysisType: (analysisType: string) => void;
  handleSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  handleKeyDown: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  textareaRef: React.RefObject<HTMLTextAreaElement>;
  chatHistorySidebarRef: React.RefObject<ChatHistorySidebarHandle>;
  handleSelectChat: (sessionId: string) => void;
  handleNewChat: () => void;
  currentSessionId: string;
  userId: string | null;
  accessToken: string | null;
  watchedStocks: string[];
};

const Watchlist: React.FC<{ stocks: string[] }> = ({ stocks }) => {
    return (
        <div className="p-4 border-t border-gray-700">
            <h2 className="text-lg font-semibold">Watchlist</h2>
            {stocks.length === 0 ? (
                <p className="text-sm text-muted-foreground">No stocks in watchlist.</p>
            ) : (
                <ul className="list-disc list-inside">
                    {stocks.map((stock, index) => (
                        <li key={index} className="text-sm">{stock}</li>
                    ))}
                </ul>
            )}
        </div>
    );
};

const Dashboard: React.FC<DashboardProps> = ({
  stocks,
  events,
  messages,
  isLoading,
  chatEndRef,
  isStreaming,
  query,
  setQuery,
  analysisType,
  setAnalysisType,
  handleSubmit,
  handleKeyDown,
  textareaRef,
  chatHistorySidebarRef,
  handleSelectChat,
  handleNewChat,
  currentSessionId,
  userId,
  accessToken,
  watchedStocks,
}) => {
  return (
    <div className="flex h-screen bg-background text-foreground">
      <ChatHistorySidebar
        ref={chatHistorySidebarRef}
        isOpen={true}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        currentSessionId={currentSessionId}
        userId={userId}
        accessToken={accessToken}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 flex overflow-hidden">
          <div className="w-3/4 border-r border-gray-700 overflow-y-auto">
            <div className="h-1/3">
              <AgentProgressSidebar events={events} isOpen={true} onClose={() => {}} isStreaming={isStreaming} />
            </div>
            <div className="h-2/3">
              <FinancialDashboard stocks={stocks} />
            </div>
          </div>
          <div className="w-1/4 flex flex-col">
            <Watchlist stocks={watchedStocks} />
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
      </div>
    </div>
  );
};

export default Dashboard;
