import React from 'react';
import { motion } from 'framer-motion';
import { Bot, Sparkles } from 'lucide-react';

export default function TypingIndicator({ variant = 'bubble', message = 'AI is thinking' }) {
  if (variant === 'inline') {
    return <InlineTypingIndicator message={message} />;
  }

  if (variant === 'minimal') {
    return <MinimalTypingIndicator />;
  }

  return <BubbleTypingIndicator />;
}

// Full chat bubble style — used as a standalone "AI is typing" message
function BubbleTypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
      className="flex gap-3 justify-start"
    >
      {/* Avatar */}
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-purple to-accent-cyan flex items-center justify-center flex-shrink-0 mt-1">
        <Bot className="w-4 h-4 text-white" />
      </div>

      {/* Bubble */}
      <div className="bg-white/5 border border-white/5 rounded-2xl px-4 py-3 flex items-center gap-2">
        <Dot delay={0} />
        <Dot delay={0.15} />
        <Dot delay={0.3} />
      </div>
    </motion.div>
  );
}

// Inline indicator — for use under chat or near status text
function InlineTypingIndicator({ message }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex items-center gap-2 px-2 py-1.5"
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
      >
        <Sparkles className="w-3.5 h-3.5 text-accent-purple" />
      </motion.div>
      <span className="text-xs text-gray-500">{message}</span>
      <div className="flex items-center gap-0.5 ml-1">
        <Dot delay={0} size="sm" />
        <Dot delay={0.15} size="sm" />
        <Dot delay={0.3} size="sm" />
      </div>
    </motion.div>
  );
}

// Minimal — just the three dots
function MinimalTypingIndicator() {
  return (
    <div className="flex items-center gap-1.5">
      <Dot delay={0} />
      <Dot delay={0.15} />
      <Dot delay={0.3} />
    </div>
  );
}

// Animated dot subcomponent
function Dot({ delay = 0, size = 'md' }) {
  const sizeClass = size === 'sm' ? 'w-1 h-1' : 'w-2 h-2';

  return (
    <motion.span
      className={`${sizeClass} rounded-full bg-accent-purple inline-block`}
      animate={{
        y: [0, -4, 0],
        opacity: [0.4, 1, 0.4],
      }}
      transition={{
        duration: 1.2,
        repeat: Infinity,
        delay,
        ease: 'easeInOut',
      }}
    />
  );
}