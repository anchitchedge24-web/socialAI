import React, { useState } from 'react';
import { Link, AlertCircle } from 'lucide-react';

export default function URLInput({ label, placeholder, value, onChange, icon: Icon, error }) {
  const [focused, setFocused] = useState(false);

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
        {Icon && <Icon className="w-4 h-4 text-accent-purple" />}
        {label}
      </label>
      <div
        className={`relative rounded-xl border transition-all duration-200 ${
          focused
            ? 'border-accent-purple/50 ring-2 ring-accent-purple/20'
            : error
            ? 'border-red-400/50'
            : 'border-white/10'
        } bg-white/5`}
      >
        <div className="absolute left-3 top-1/2 -translate-y-1/2">
          <Link className="w-4 h-4 text-gray-500" />
        </div>
        <input
          type="url"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={placeholder}
          className="w-full bg-transparent text-gray-200 pl-10 pr-4 py-3 rounded-xl text-sm focus:outline-none placeholder:text-gray-600"
        />
      </div>
      {error && (
        <p className="text-xs text-red-400 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          {error}
        </p>
      )}
    </div>
  );
}