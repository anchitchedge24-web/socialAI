import React from 'react';

export default function SkeletonCard() {
  return (
    <div className="glassmorphism rounded-2xl p-6 space-y-4 animate-pulse">
      <div className="w-full h-40 rounded-xl shimmer-bg" />
      <div className="space-y-3">
        <div className="h-5 w-3/4 rounded shimmer-bg" />
        <div className="h-4 w-1/2 rounded shimmer-bg" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="h-16 rounded-lg shimmer-bg" />
        <div className="h-16 rounded-lg shimmer-bg" />
        <div className="h-16 rounded-lg shimmer-bg" />
      </div>
      <div className="h-8 rounded-lg shimmer-bg" />
    </div>
  );
}