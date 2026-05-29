import React from 'react';

export default function MetadataBadge({ icon: Icon, label, value, color = 'text-gray-300' }) {
  return (
    <div className="flex flex-col items-center p-3 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
      {Icon && <Icon className={`w-4 h-4 mb-1 ${color}`} />}
      <span className={`text-lg font-bold ${color}`}>{value}</span>
      <span className="text-xs text-gray-500 mt-0.5">{label}</span>
    </div>
  );
}