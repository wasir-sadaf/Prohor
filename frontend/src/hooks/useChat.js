import { useState, useCallback } from "react";
import api from "../api/client";

export function useChat() {
  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  const fetchConversations = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getConversations();
      setConversations(data.conversations || []);
    } catch (err) {
      console.error("Failed to fetch conversations:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchMessages = useCallback(async (conversationId) => {
    setLoading(true);
    try {
      const data = await api.getMessages(conversationId);
      setMessages(data.messages || []);
      setCurrentConversation(conversationId);
    } catch (err) {
      console.error("Failed to fetch messages:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = useCallback(
    async (text) => {
      setSending(true);

      // Optimistic update — add user message immediately
      const optimisticMsg = {
        id: `temp-${Date.now()}`,
        role: "user",
        content: text,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimisticMsg]);

      try {
        const data = await api.sendMessage(text, currentConversation);

        // Update the conversation id if it was a new conversation
        if (!currentConversation && data.conversation_id) {
          setCurrentConversation(data.conversation_id);
        }

        // Replace optimistic message with real one
        setMessages((prev) =>
          prev.map((m) => (m.id === optimisticMsg.id ? data.data : m))
        );

        // Refresh conversations list
        fetchConversations();

        return data;
      } catch (err) {
        // Remove optimistic message on error
        setMessages((prev) => prev.filter((m) => m.id !== optimisticMsg.id));
        throw err;
      } finally {
        setSending(false);
      }
    },
    [currentConversation, fetchConversations]
  );

  const startNewConversation = useCallback(() => {
    setCurrentConversation(null);
    setMessages([]);
  }, []);

  return {
    conversations,
    messages,
    currentConversation,
    loading,
    sending,
    fetchConversations,
    fetchMessages,
    sendMessage,
    startNewConversation,
  };
}
