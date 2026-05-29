import React from 'react';
import { motion } from 'framer-motion';

export default function EngagementBar({ rate, maxRate = 10, color = '#7C3AED' }) {
  const percentage = Math.min((rate / maxRate) * 100, 100);

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs">
        <span className="text-gray-400">Engagement Rate</span>
        <span className="font-bold" style={{ color }}>
          {rate.toFixed(2)}%
        </span>
      </div>
      <div className="h-2 rounded-full bg-white/5 overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, delay: 0.3, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}