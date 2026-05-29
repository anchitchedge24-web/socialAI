import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Bot, Copy, Check, ThumbsUp, ThumbsDown } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { SourceCitationList } from './SourceCitation';

export default function ChatMessage({ message, index = 0 }) {
  const isUser = message.role === 'user';
  const sources = message.sources || [];
  const confidence = message.confidence;
  const reasoning = message.reasoning;
  const evidence = message.evidence || [];

  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Copy failed:', err);
    }
  };

  const handleFeedback = (type) => {
    setFeedback(type === feedback ? null : type);
  };

  // Confidence badge color
  const getConfidenceColor = (score) => {
    if (score >= 0.75) return 'text-accent-green border-accent-green/30 bg-accent-green/10';
    if (score >= 0.5) return 'text-accent-cyan border-accent-cyan/30 bg-accent-cyan/10';
    if (score >= 0.3) return 'text-accent-warning border-accent-warning/30 bg-accent-warning/10';
    return 'text-gray-500 border-white/10 bg-white/5';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: Math.min(index * 0.03, 0.2) }}
      className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'} group`}
    >
      {/* Assistant Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-purple to-accent-cyan flex items-center justify-center flex-shrink-0 mt-1 shadow-lg shadow-accent-purple/20">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}

      {/* Message Body */}
      <div className={`flex flex-col gap-1.5 max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? 'bg-accent-purple/20 border border-accent-purple/30 text-gray-200'
              : 'bg-white/5 border border-white/5 text-gray-300'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          ) : message.content ? (
            <>
              {/* Markdown rendered answer */}
              <div className="prose prose-invert prose-sm max-w-none
                prose-p:my-1.5 prose-p:leading-relaxed
                prose-headings:my-2 prose-headings:text-white prose-headings:font-heading
                prose-h1:text-base prose-h2:text-sm prose-h3:text-sm
                prose-ul:my-1.5 prose-ol:my-1.5
                prose-li:my-0.5 prose-li:text-gray-300
                prose-strong:text-accent-cyan prose-strong:font-semibold
                prose-em:text-gray-200
                prose-code:text-accent-warning prose-code:bg-white/5 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:before:content-none prose-code:after:content-none
                prose-pre:bg-black/40 prose-pre:border prose-pre:border-white/5 prose-pre:rounded-lg
                prose-blockquote:border-l-accent-purple prose-blockquote:text-gray-400 prose-blockquote:not-italic
                prose-a:text-accent-cyan prose-a:no-underline hover:prose-a:underline
                prose-hr:border-white/10
              ">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>

              {/* Confidence badge */}
              {typeof confidence === 'number' && confidence > 0 && (
                <div className="mt-3 pt-3 border-t border-white/5 flex items-center gap-2 flex-wrap">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full border font-medium ${getConfidenceColor(
                      confidence
                    )}`}
                  >
                    Confidence: {(confidence * 100).toFixed(0)}%
                  </span>
                  {evidence.length > 0 && (
                    <span className="text-xs text-gray-500">
                      • {evidence.length} evidence chunk{evidence.length !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              )}

              {/* Reasoning (collapsed by default — could expand later) */}
              {reasoning && (
                <details className="mt-3 pt-3 border-t border-white/5 group/reasoning">
                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-300 transition-colors select-none">
                    <span className="group-open/reasoning:hidden">▸ Show reasoning</span>
                    <span className="hidden group-open/reasoning:inline">▾ Hide reasoning</span>
                  </summary>
                  <p className="text-xs text-gray-500 mt-2 italic leading-relaxed whitespace-pre-wrap">
                    {reasoning}
                  </p>
                </details>
              )}

              {/* Source citations */}
              {sources.length > 0 && (
                <SourceCitationList sources={sources} title="Cited Sources" />
              )}
            </>
          ) : (
            /* Empty assistant message — typing dots */
            <div className="flex items-center gap-1.5 py-0.5">
              <Dot delay={0} />
              <Dot delay={0.15} />
              <Dot delay={0.3} />
            </div>
          )}
        </div>

        {/* Action buttons (assistant only, when content exists) */}
        {!isUser && message.content && (
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 px-1">
            <ActionButton
              onClick={handleCopy}
              icon={copied ? Check : Copy}
              label={copied ? 'Copied!' : 'Copy'}
              active={copied}
              activeColor="text-accent-green"
            />
            <ActionButton
              onClick={() => handleFeedback('up')}
              icon={ThumbsUp}
              label="Good response"
              active={feedback === 'up'}
              activeColor="text-accent-green"
            />
            <ActionButton
              onClick={() => handleFeedback('down')}
              icon={ThumbsDown}
              label="Bad response"
              active={feedback === 'down'}
              activeColor="text-red-400"
            />
          </div>
        )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-lg bg-white/10 border border-white/10 flex items-center justify-center flex-shrink-0 mt-1">
          <User className="w-4 h-4 text-gray-400" />
        </div>
      )}
    </motion.div>
  );
}

/* ---------- Sub-components ---------- */

function ActionButton({ onClick, icon: Icon, label, active, activeColor = 'text-accent-cyan' }) {
  return (
    <button
      onClick={onClick}
      title={label}
      aria-label={label}
      className={`p-1.5 rounded-md transition-all duration-200 ${
        active
          ? `${activeColor} bg-white/5`
          : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
      }`}
    >
      <Icon className="w-3.5 h-3.5" />
    </button>
  );
}

function Dot({ delay = 0 }) {
  return (
    <motion.span
      className="w-2 h-2 rounded-full bg-accent-purple inline-block"
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