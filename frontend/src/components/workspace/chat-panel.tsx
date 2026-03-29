"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { ErrorMessage } from "@/components/ui/error-message";
import { CitationBadge } from "@/components/workspace/citation-badge";
import { useChatHistory, useSendMessage } from "@/hooks/use-chat";
import { getApiErrorMessage } from "@/lib/utils";
import type { ChatMessage } from "@/types/api";

interface ChatPanelProps {
  documentId: string;
}

export function ChatPanel({ documentId }: ChatPanelProps) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: historyData } = useChatHistory(documentId, sessionId);
  const sendMessage = useSendMessage(documentId);

  // Sync history into local messages when loaded
  useEffect(() => {
    if (historyData?.messages) {
      setLocalMessages(historyData.messages);
    }
  }, [historyData]);

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [localMessages, sendMessage.isPending]);

  const handleSend = () => {
    const message = input.trim();
    if (!message || sendMessage.isPending) return;

    // Optimistic: add user message locally
    const optimisticMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: message,
      citations: null,
    };
    setLocalMessages((prev) => [...prev, optimisticMsg]);
    setInput("");

    sendMessage.mutate(
      { message, sessionId },
      {
        onSuccess: (data) => {
          // Set session ID if new
          if (!sessionId) {
            setSessionId(data.session_id);
          }
          // Add assistant message
          setLocalMessages((prev) => [...prev, data.message]);
        },
        onError: () => {
          // Remove optimistic message on error
          setLocalMessages((prev) => prev.filter((m) => m.id !== optimisticMsg.id));
        },
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {localMessages.length === 0 && !sendMessage.isPending && (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-400 dark:text-gray-500 text-sm">
              Ask a question about this document to get started.
            </p>
          </div>
        )}

        {localMessages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Typing indicator */}
        {sendMessage.isPending && (
          <div className="flex gap-2 items-start">
            <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl rounded-tl-none px-4 py-3 max-w-[80%]">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error display */}
      {sendMessage.isError && (
        <div className="pb-3">
          <ErrorMessage
            message={getApiErrorMessage(sendMessage.error) || "Failed to send message"}
          />
        </div>
      )}

      {/* Input area */}
      <div className="border-t dark:border-gray-700 pt-3">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about this document..."
            rows={1}
            className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder:text-gray-400 dark:placeholder:text-gray-500"
            disabled={sendMessage.isPending}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || sendMessage.isPending}
            isLoading={sendMessage.isPending}
            size="md"
          >
            Send
          </Button>
        </div>
        <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
          isUser
            ? "bg-blue-600 text-white rounded-tr-none"
            : "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-tl-none"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {message.citations.map((citation) => (
              <CitationBadge key={citation.chunk_id} citation={citation} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
