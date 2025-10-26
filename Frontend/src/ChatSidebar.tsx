import { PlusCircle, MessageSquare } from "lucide-react";

type ChatHistoryItem = {
  session_id: string;
  title: string;
};

type ChatSidebarProps = {
  chatHistory: ChatHistoryItem[];
  currentChatId: string;
  onNewChat: () => void;
  onSelectChat: (sessionId: string) => void;
};

export function ChatSidebar({
  chatHistory,
  currentChatId,
  onNewChat,
  onSelectChat,
}: ChatSidebarProps) {
  return (
    <div className="flex flex-col h-full bg-gray-800 text-white w-64 p-4">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">Chats</h2>
        <button
          onClick={onNewChat}
          className="p-2 rounded-full hover:bg-gray-700 transition-colors"
          title="New Chat"
        >
          <PlusCircle size={20} />
        </button>
      </div>

      <nav className="flex-grow overflow-y-auto">
        <ul>
          {chatHistory.map((chat) => (
            <li key={chat.session_id} className="mb-2">
              <button
                onClick={() => onSelectChat(chat.session_id)}
                className={`flex items-center w-full p-2 rounded-md text-left transition-colors ${
                  currentChatId === chat.session_id
                    ? "bg-blue-600 hover:bg-blue-700"
                    : "hover:bg-gray-700"
                }`}
              >
                <MessageSquare size={18} className="mr-2" />
                <span className="truncate">{chat.title || "New Chat"}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
