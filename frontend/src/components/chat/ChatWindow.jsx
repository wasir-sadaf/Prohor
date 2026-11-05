import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Plus,
  MessageSquare,
  Clock,
  ChevronLeft,
  Scale,
  Sparkles,
  Shield,
  FileText,
  AlertTriangle,
  HelpCircle,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { useLanguage } from "../../contexts/LanguageContext";
import { useChat } from "../../hooks/useChat";
import TypingIndicator from "../ui/TypingIndicator";
import ReactMarkdown from "react-markdown";
import toast from "react-hot-toast";

// ─── Suggestion cards shown in empty chat ───
const suggestions = [
  {
    icon: Shield,
    titleBn: "আমার অধিকার কী?",
    titleEn: "What are my rights?",
    promptBn: "বাংলাদেশে একজন ভাড়াটিয়া হিসেবে আমার আইনি অধিকার কী কী?",
    promptEn: "What are my legal rights as a tenant in Bangladesh?",
    color: "blue",
  },
  {
    icon: FileText,
    titleBn: "জিডি কীভাবে করবো?",
    titleEn: "How to file a GD?",
    promptBn: "থানায় জিডি (জেনারেল ডায়েরি) করার ধাপগুলো কী কী?",
    promptEn: "What are the steps to file a GD (General Diary) at a police station?",
    color: "purple",
  },
  {
    icon: AlertTriangle,
    titleBn: "ভোক্তা অধিকার",
    titleEn: "Consumer rights",
    promptBn: "বাংলাদেশে ভোক্তা অধিকার সংরক্ষণ আইন সম্পর্কে জানতে চাই।",
    promptEn: "Tell me about consumer rights protection law in Bangladesh.",
    color: "amber",
  },
  {
    icon: HelpCircle,
    titleBn: "শ্রম আইন",
    titleEn: "Labor law",
    promptBn: "বাংলাদেশ শ্রম আইন অনুযায়ী একজন কর্মীর মৌলিক অধিকার কী?",
    promptEn: "What are the fundamental rights of a worker under Bangladesh Labour Act?",
    color: "green",
  },
];

const colorMap = {
  blue: "bg-blue-50 text-blue-600 border-blue-100",
  purple: "bg-purple-50 text-purple-600 border-purple-100",
  amber: "bg-amber-50 text-amber-600 border-amber-100",
  green: "bg-green-50 text-green-600 border-green-100",
};

// ─── Single Message Bubble ───
function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex items-end gap-2.5 animate-fade-in ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center shadow-md mb-1">
          <Scale className="w-4 h-4 text-white" />
        </div>
      )}

      <div
        className={`max-w-[75%] sm:max-w-[65%] px-4 py-3 ${
          isUser ? "chat-user" : "chat-assistant"
        }`}
      >
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </p>
        ) : (
          <div className="prose-chat text-sm leading-relaxed">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center shadow-md mb-1">
          <span className="text-xs font-bold text-white">You</span>
        </div>
      )}
    </div>
  );
}

// ─── Main Chat Component ───
export default function ChatWindow() {
  const {
    conversations,
    messages,
    currentConversation,
    loading,
    sending,
    fetchConversations,
    fetchMessages,
    sendMessage,
    startNewConversation,
  } = useChat();

  const { t, lang } = useLanguage();
  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Fetch conversations on mount
  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  // Focus input on conversation change
  useEffect(() => {
    inputRef.current?.focus();
  }, [currentConversation]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;

    setInput("");
    try {
      await sendMessage(text);
    } catch (err) {
      toast.error(err.message || "Failed to send message");
    }
  }, [input, sending, sendMessage]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestion = (suggestion) => {
    const prompt = lang === "bn" ? suggestion.promptBn : suggestion.promptEn;
    setInput(prompt);
    // Auto-send after short delay
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  };

  const selectConversation = (id) => {
    fetchMessages(id);
    setMobileSidebarOpen(false);
  };

  const handleNewChat = () => {
    startNewConversation();
    setMobileSidebarOpen(false);
  };

  const isEmptyChat = !currentConversation && messages.length === 0;

  return (
    <div className="flex h-full overflow-hidden relative">
      {/* ─── Sidebar ─── */}
      {/* Desktop sidebar */}
      <div
        className={`hidden md:flex flex-col border-r border-slate-200 bg-slate-50/50 transition-all duration-300 ${
          sidebarOpen ? "w-72" : "w-0 overflow-hidden"
        }`}
      >
        <SidebarContent
          conversations={conversations}
          currentConversation={currentConversation}
          onSelect={selectConversation}
          onNewChat={handleNewChat}
          loading={loading}
          t={t}
        />
      </div>

      {/* Mobile sidebar overlay */}
      {mobileSidebarOpen && (
        <div
          className="md:hidden fixed inset-0 z-30 bg-black/30 backdrop-blur-sm"
          onClick={() => setMobileSidebarOpen(false)}
        >
          <div
            className="w-72 h-full bg-white border-r border-slate-200 animate-slide-in-left"
            onClick={(e) => e.stopPropagation()}
          >
            <SidebarContent
              conversations={conversations}
              currentConversation={currentConversation}
              onSelect={selectConversation}
              onNewChat={handleNewChat}
              loading={loading}
              t={t}
            />
          </div>
        </div>
      )}

      {/* ─── Main Chat Area ─── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-200 bg-white/80 backdrop-blur-sm">
          {/* Mobile sidebar toggle */}
          <button
            onClick={() => setMobileSidebarOpen(true)}
            className="md:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
          >
            <PanelLeftOpen className="h-4 w-4" />
          </button>

          {/* Desktop sidebar toggle */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="hidden md:flex p-2 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
            title={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
          >
            {sidebarOpen ? (
              <PanelLeftClose className="h-4 w-4" />
            ) : (
              <PanelLeftOpen className="h-4 w-4" />
            )}
          </button>

          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center">
              <Sparkles className="h-3.5 w-3.5 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-800">
                {lang === "bn" ? "প্রহর AI সহকারী" : "Prohor AI Assistant"}
              </h2>
              <p className="text-[11px] text-green-600 font-medium">
                {lang === "bn" ? "অনলাইন" : "Online"}
              </p>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5">
          {isEmptyChat ? (
            /* Empty state with suggestions */
            <div className="h-full flex flex-col items-center justify-center max-w-2xl mx-auto animate-fade-in">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center mb-6 shadow-xl shadow-green-500/20 animate-float">
                <Scale className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-slate-800 mb-2 text-center">
                {lang === "bn"
                  ? "প্রহরে স্বাগতম!"
                  : "Welcome to Prohor!"}
              </h2>
              <p className="text-sm text-slate-500 mb-8 text-center max-w-md">
                {lang === "bn"
                  ? "আপনার আইনি প্রশ্ন জিজ্ঞাসা করুন অথবা নিচের বিষয়গুলো থেকে বেছে নিন:"
                  : "Ask a legal question or choose from the topics below:"}
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
                {suggestions.map((s, i) => {
                  const Icon = s.icon;
                  return (
                    <button
                      key={i}
                      onClick={() => handleSuggestion(s)}
                      className={`flex items-center gap-3 p-4 rounded-xl border text-left
                        hover:shadow-md hover:-translate-y-0.5 transition-all duration-200
                        ${colorMap[s.color]}`}
                    >
                      <Icon className="h-5 w-5 flex-shrink-0" />
                      <span className="text-sm font-medium">
                        {lang === "bn" ? s.titleBn : s.titleEn}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            /* Messages list */
            <>
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}
              {sending && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-200 bg-white p-4">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-end gap-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={t("chatPlaceholder")}
                  rows={1}
                  className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50/50
                    px-4 py-3 text-sm text-slate-800
                    placeholder:text-slate-400
                    focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500 focus:bg-white
                    hover:border-slate-300 transition-all
                    max-h-32 overflow-y-auto"
                  style={{
                    height: "auto",
                    minHeight: "48px",
                  }}
                  onInput={(e) => {
                    e.target.style.height = "auto";
                    e.target.style.height = `${Math.min(e.target.scrollHeight, 128)}px`;
                  }}
                />
              </div>
              <button
                onClick={handleSend}
                disabled={!input.trim() || sending}
                className="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-r from-green-500 to-green-600
                  text-white flex items-center justify-center
                  hover:from-green-600 hover:to-green-700
                  disabled:opacity-40 disabled:cursor-not-allowed
                  shadow-lg shadow-green-500/25 hover:shadow-green-500/40
                  active:scale-95 transition-all duration-200"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
            <p className="text-[10px] text-slate-400 mt-2 text-center">
              {t("disclaimer")}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Sidebar Content (Shared between mobile/desktop) ───
function SidebarContent({
  conversations,
  currentConversation,
  onSelect,
  onNewChat,
  loading,
  t,
}) {
  return (
    <div className="flex flex-col h-full">
      {/* New Chat Button */}
      <div className="p-3 border-b border-slate-200">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl
            bg-gradient-to-r from-green-500 to-green-600 text-white text-sm font-medium
            hover:from-green-600 hover:to-green-700
            shadow-md shadow-green-500/20 hover:shadow-green-500/30
            active:scale-[0.98] transition-all duration-200"
        >
          <Plus className="h-4 w-4" />
          {t("newChat")}
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-2">
        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-3 py-2">
          {t("conversations")}
        </p>

        {conversations.length === 0 ? (
          <div className="text-center py-8">
            <MessageSquare className="h-8 w-8 text-slate-300 mx-auto mb-2" />
            <p className="text-xs text-slate-400">{t("noConversations")}</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all duration-150
                  ${
                    currentConversation === conv.id
                      ? "bg-green-50 text-green-700 font-medium border border-green-100"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
              >
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-3.5 w-3.5 flex-shrink-0 opacity-60" />
                  <span className="truncate">
                    {conv.title || "New Conversation"}
                  </span>
                </div>
                <div className="flex items-center gap-1 mt-1 ml-5">
                  <Clock className="h-2.5 w-2.5 text-slate-400" />
                  <span className="text-[10px] text-slate-400">
                    {new Date(conv.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

