export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-3 py-4 px-1 animate-fade-in">
      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-green-600 shadow-md">
        <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2" />
          <circle cx="12" cy="12" r="10" strokeLinecap="round" />
        </svg>
      </div>
      <div className="chat-assistant px-5 py-3.5 shadow-sm">
        <div className="flex items-center gap-1.5">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    </div>
  );
}
