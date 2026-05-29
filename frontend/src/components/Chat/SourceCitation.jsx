import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Youtube,
  Instagram,
  Clock,
  ChevronDown,
  ChevronUp,
  Quote,
  TrendingUp,
} from 'lucide-react';

function formatTimestamp(seconds) {
  if (seconds === null || seconds === undefined) return null;
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function getRelevanceColor(score) {
  if (score >= 0.75) return 'text-accent-green border-accent-green/30 bg-accent-green/10';
  if (score >= 0.5) return 'text-accent-cyan border-accent-cyan/30 bg-accent-cyan/10';
  if (score >= 0.3) return 'text-accent-warning border-accent-warning/30 bg-accent-warning/10';
  return 'text-gray-500 border-white/10 bg-white/5';
}

function getRelevanceLabel(score) {
  if (score >= 0.75) return 'High';
  if (score >= 0.5) return 'Medium';
  if (score >= 0.3) return 'Low';
  return 'Weak';
}

export default function SourceCitation({ source, index = 0 }) {
  const [expanded, setExpanded] = useState(false);

  if (!source) return null;

  const isYouTube = source.video_id === 'A';
  const PlatformIcon = isYouTube ? Youtube : Instagram;
  const videoLabel = isYouTube ? 'Video A — YouTube' : 'Video B — Instagram';
  const accentColor = isYouTube ? 'text-accent-purple' : 'text-accent-cyan';
  const accentBorder = isYouTube
    ? 'border-accent-purple/20 hover:border-accent-purple/40'
    : 'border-accent-cyan/20 hover:border-accent-cyan/40';

  const tsStart = formatTimestamp(source.timestamp_start);
  const tsEnd = formatTimestamp(source.timestamp_end);
  const hasTimestamp = tsStart !== null;

  const relevance = source.relevance_score || 0;
  const relevanceClass = getRelevanceColor(relevance);
  const relevanceLabel = getRelevanceLabel(relevance);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`rounded-xl border bg-white/[0.02] ${accentBorder} transition-all duration-200 overflow-hidden`}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-3 hover:bg-white/[0.03] transition-colors text-left"
      >
        {/* Platform icon */}
        <div className={`flex items-center justify-center w-8 h-8 rounded-lg bg-white/5 ${accentColor} flex-shrink-0`}>
          <PlatformIcon className="w-4 h-4" />
        </div>

        {/* Source info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-semibold ${accentColor}`}>{videoLabel}</span>
            <span className="text-xs text-gray-600">•</span>
            <span className="text-xs text-gray-500 truncate">{source.chunk_id}</span>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {hasTimestamp && (
              <span className="text-xs text-gray-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {tsStart}
                {tsEnd && tsEnd !== tsStart && ` – ${tsEnd}`}
              </span>
            )}
            <span
              className={`text-xs px-2 py-0.5 rounded-full border flex items-center gap-1 ${relevanceClass}`}
            >
              <TrendingUp className="w-2.5 h-2.5" />
              {relevanceLabel} ({(relevance * 100).toFixed(0)}%)
            </span>
          </div>
        </div>

        {/* Expand chevron */}
        <div className="text-gray-500 flex-shrink-0">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expandable snippet */}
      <AnimatePresence initial={false}>
        {expanded && source.text_snippet && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 pt-1 border-t border-white/5">
              <div className="flex gap-2 mt-2">
                <Quote className="w-3.5 h-3.5 text-gray-600 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-gray-400 leading-relaxed italic">
                  "{source.text_snippet}"
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Container component for a list of citations
export function SourceCitationList({ sources = [], title = 'Sources' }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-4 space-y-2">
      <div className="flex items-center gap-2 mb-2">
        <FileText className="w-3.5 h-3.5 text-gray-500" />
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
          {title} ({sources.length})
        </h4>
      </div>
      <div className="space-y-2">
        {sources.map((source, i) => (
          <SourceCitation key={`${source.chunk_id}-${i}`} source={source} index={i} />
        ))}
      </div>
    </div>
  );
}