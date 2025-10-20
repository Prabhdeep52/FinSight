import React, { useEffect, useState, useImperativeHandle, forwardRef } from "react";
import { MessageSquare, Trash2, Plus, X } from "lucide-react";

interface Conversation {
  id: number;
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface ChatHistorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectChat: (sessionId: string) => void;
  onNewChat: () => void;
  currentSessionId: string;
  userId: string | null;
  accessToken: string | null;
}

export interface ChatHistorySidebarHandle {
  refresh: () => void;
}

export const ChatHistorySidebar = forwardRef<
  ChatHistorySidebarHandle,
  ChatHistorySidebarProps
>(
  (
    {
      isOpen,
      onClose,
      onSelectChat,
      onNewChat,
      currentSessionId,
      userId,
      accessToken,
    },
    ref
  ) => {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
      if (isOpen && userId && accessToken) fetchChatHistory();
    }, [isOpen, userId, accessToken]);

    const fetchChatHistory = async () => {
      if (!accessToken) return;
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          "http://localhost:8000/api/v1/agent/chat-history",
          {
            headers: { Authorization: `Bearer ${accessToken}` },
          }
        );
        if (!response.ok) throw new Error("Failed to fetch chat history");
        const data = await response.json();
        setConversations(data.conversations || []);
      } catch (err) {
        console.error(err);
        setError("Failed to load chat history");
      } finally {
        setLoading(false);
      }
    };

    useImperativeHandle(ref, () => ({ refresh: fetchChatHistory }));

    const handleDeleteChat = async (sessionId: string, e: React.MouseEvent) => {
      e.stopPropagation();
      if (!confirm("Delete this conversation?")) return;

      try {
        const response = await fetch(
          `http://localhost:8000/api/v1/agent/chat-history/${sessionId}`,
          {
            method: "DELETE",
            headers: { Authorization: `Bearer ${accessToken}` },
          }
        );
        if (response.ok) {
          fetchChatHistory();
          if (sessionId === currentSessionId) onNewChat();
        }
      } catch (err) {
        console.error(err);
      }
    };

    const formatDate = (dateString: string) => {
      const date = new Date(dateString);
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      const mins = Math.floor(diff / 60000);
      const hrs = Math.floor(diff / 3600000);
      const days = Math.floor(diff / 86400000);
      if (mins < 1) return "Just now";
      if (mins < 60) return `${mins}m ago`;
      if (hrs < 24) return `${hrs}h ago`;
      if (days < 7) return `${days}d ago`;
      return date.toLocaleDateString();
    };

    if (!isOpen) return null;

    return (
      <>
        {/* Overlay */}
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />

        {/* Sidebar */}
        <div
          className={`fixed left-0 top-0 h-full w-80 bg-black/80 
          backdrop-blur-xl border-r border-white/10 
          shadow-[0_0_25px_rgba(168,85,247,0.15)] z-50 
          transform transition-transform duration-300 
          ${isOpen ? "translate-x-0" : "-translate-x-full"}`}
        >
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="p-4 border-b border-white/10 bg-white/5 backdrop-blur-sm">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white/90">
                  Analysis History
                </h2>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/10 rounded-lg text-white/60"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <button
                onClick={() => {
                  onNewChat();
                  onClose();
                }}
                className="w-full py-2 px-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white rounded-lg flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-purple-500/50"
              >
                <Plus className="w-4 h-4" /> New Analysis
              </button>
            </div>

{/* Chat List */}
<div className="flex-1 overflow-y-auto p-3">
  {loading && (
    <div className="text-center text-white/50 py-4 text-sm">
      Loading Analysis...
    </div>
  )}
  {error && (
    <div className="text-center text-red-400 py-4 text-sm">{error}</div>
  )}
  {!loading && !error && conversations.length === 0 && (
    <div className="text-center text-white/40 py-8">
      <MessageSquare className="w-10 h-10 mx-auto mb-2 opacity-40" />
      <p className="text-sm">No Analysis yet</p>
      <p className="text-xs mt-1 text-white/40">Start a new chat to begin</p>
    </div>
  )}

  {!loading && conversations.length > 0 && (
    <div className="space-y-1.5">
      {conversations.map((conv) => (
        <div
          key={conv.session_id}
          onClick={() => {
            onSelectChat(conv.session_id);
            onClose();
          }}
          className={`group flex items-center justify-between px-2.5 py-2 rounded-md cursor-pointer transition-all border text-sm ${
            conv.session_id === currentSessionId
              ? "bg-gradient-to-r from-purple-600/20 to-blue-600/20 border-purple-500/30"
              : "bg-white/5 hover:bg-white/10 border-transparent"
          }`}
        >
          <div className="flex-1 min-w-0">
            <h3 className="text-white/90 font-medium truncate text-[13px] leading-snug">
              {conv.title}
            </h3>
            <p className="text-white/50 text-[11px] leading-tight mt-0.5">
              {formatDate(conv.updated_at)}
            </p>
          </div>
          <button
            onClick={(e) => handleDeleteChat(conv.session_id, e)}
            className="opacity-0 group-hover:opacity-100 p-1 text-white/40 hover:text-red-400 transition-opacity flex-shrink-0"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  )}
</div>


            {/* Footer */}
            <div className="p-4 border-t border-white/10 text-center text-xs text-white/40">
              {conversations.length} conversation
              {conversations.length !== 1 ? "s" : ""}
            </div>
          </div>
        </div>
      </>
    );
  }
);

ChatHistorySidebar.displayName = "ChatHistorySidebar";
