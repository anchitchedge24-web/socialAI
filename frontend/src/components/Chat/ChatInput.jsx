import React, { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, Loader2, Sparkles } from 'lucide-react';

export default function ChatInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
  placeholder = 'Ask about the videos...',
  autoFocus = true,
}) {
  const inputRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (autoFocus && inputRef.current && !disabled) {
      inputRef.current.focus();
    }
  }, [autoFocus, disabled]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = Math.min(scrollHeight, 120) + 'px';
    }
  }, [value]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!value.trim() || disabled) return;
    onSubmit(value.trim());
  };

  const canSubmit = value.trim().length > 0 && !disabled;

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div
        className={`relative flex items-end gap-3 p-2 rounded-2xl border transition-all duration-200 ${
          disabled
            ? 'border-white/5 bg-white/[0.02]'
            : 'border-white/10 bg-white/5 hover:border-white/15 focus-within:border-accent-purple/40 focus-within:ring-2 focus-within:ring-accent-purple/20'
        }`}
      >
        {/* Sparkles icon */}
        <div className="flex items-center justify-center w-9 h-9 flex-shrink-0">
          <Sparkles
            className={`w-4 h-4 ${
              disabled ? 'text-gray-700' : 'text-accent-purple'
            } transition-colors`}
          />
        </div>

        {/* Textarea */}
        <textarea
          ref={(el) => {
            inputRef.current = el;
            textareaRef.current = el;
          }}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none resize-none py-2 max-h-[120px] disabled:cursor-not-allowed disabled:opacity-50"
          style={{ minHeight: '24px' }}
        />

        {/* Send button */}
        <motion.button
          type="submit"
          disabled={!canSubmit}
          whileHover={canSubmit ? { scale: 1.05 } : {}}
          whileTap={canSubmit ? { scale: 0.95 } : {}}
          className={`flex items-center justify-center w-9 h-9 rounded-xl flex-shrink-0 transition-all duration-200 ${
            canSubmit
              ? 'bg-gradient-to-br from-accent-purple to-accent-cyan text-white shadow-lg shadow-accent-purple/20 hover:shadow-accent-purple/40'
              : 'bg-white/5 text-gray-600 cursor-not-allowed'
          }`}
        >
          {disabled ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </motion.button>
      </div>

      {/* Helper text */}
      <div className="flex items-center justify-between mt-2 px-2">
        <p className="text-xs text-gray-600">
          {disabled
            ? 'AI is generating response...'
            : 'Press Enter to send, Shift+Enter for new line'}
        </p>
        {value.length > 0 && (
          <p className="text-xs text-gray-600">{value.length} chars</p>
        )}
      </div>
    </form>
  );
}