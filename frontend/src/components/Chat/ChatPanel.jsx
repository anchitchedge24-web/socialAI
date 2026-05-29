import React, { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, MessageSquare, Loader2, Sparkles, RotateCcw } from 'lucide-react';
import useAppStore from '../../store/appStore';
import { useChat } from '../../hooks/useChat';
import ChatMessage from './ChatMessage';

const SUGGESTED_QUERIES = [
  "Why did Video A get more engagement than Video B?",
  "Compare the hooks in the first 5 seconds",
  "What's the engagement rate of each?",
  "Suggest improvements for Video B",
  "Which content style performed better?",
  "Summarize the storytelling differences",
];

export default function ChatPanel() {
  const { messages, isStreaming, analysisComplete } = useAppStore();
  const { sendMessage } = useChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input.trim());
    setInput('');
  };

  const handleSuggestion = (query) => {
    if (isStreaming) return;
    sendMessage(query);
  };

  if (!analysisComplete) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="glassmorphism rounded-2xl p-8 flex flex-col items-center justify-center text-center min-h-[400px]"
      >
        <div className="w-16 h-16 rounded-2xl bg-accent-purple/10 border border-accent-purple/20 flex items-center justify-center mb-4">
          <MessageSquare className="w-8 h-8 text-accent-purple" />
        </div>
        <h3 className="font-heading text-xl font-bold text-white mb-2">RAG Chat Assistant</h3>
        <p className="text-gray-400 text-sm max-w-md">
          Analyze two videos above to start chatting. The AI will compare transcripts,
          engagement metrics, and content strategy.
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      className="glassmorphism rounded-2xl flex flex-col"
      style={{ height: '600px' }}
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-accent-purple" />
          <h3 className="font-heading font-bold text-white">RAG Chat</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-accent-green/10 text-accent-green border border-accent-green/20">
            Live
          </span>
        </div>
        {messages.length > 0 && (
          <button
            onClick={() => useAppStore.getState().clearMessages()}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1"
          >
            <RotateCcw className="w-3 h-3" />
            Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="space-y-3">
            <p className="text-sm text-gray-400 text-center mb-4">
              Try asking one of these questions:
            </p>
            <div className="grid grid-cols-1 gap-2">
              {SUGGESTED_QUERIES.map((query, i) => (
                <motion.button
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  onClick={() => handleSuggestion(query)}
                  className="text-left text-sm px-4 py-2.5 rounded-xl bg-white/5 border border-white/5 text-gray-300 hover:bg-white/10 hover:border-accent-purple/30 transition-all duration-200"
                >
                  {query}
                </motion.button>
              ))}
            </div>
          </div>
        )}

        <AnimatePresence>
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} index={i} />
          ))}
        </AnimatePresence>

        {isStreaming && (
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Loader2 className="w-3 h-3 animate-spin" />
            AI is thinking...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-white/5">
        <div className="flex items-center gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about the videos..."
            disabled={isStreaming}
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:border-accent-purple/50 focus:ring-2 focus:ring-accent-purple/20 transition-all disabled:opacity-50"
          />
          <motion.button
            type="submit"
            disabled={isStreaming || !input.trim()}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`p-3 rounded-xl transition-all ${
              isStreaming || !input.trim()
                ? 'bg-white/5 text-gray-600 cursor-not-allowed'
                : 'bg-accent-purple text-white hover:bg-accent-purple/80'
            }`}
          >
            <Send className="w-4 h-4" />
          </motion.button>
        </div>
      </form>
    </motion.div>
  );
}