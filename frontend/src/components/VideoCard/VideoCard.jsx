import React from 'react';
import { motion } from 'framer-motion';
import {
  Eye,
  Heart,
  MessageCircle,
  Clock,
  Calendar,
  User,
  Users,
  Hash,
  Youtube,
  Instagram,
} from 'lucide-react';
import MetadataBadge from './MetadataBadge';
import EngagementBar from './EngagementBar';

function formatNumber(num) {
  if (num === null || num === undefined) return 'N/A';

  const absNum = Math.abs(num);

  if (absNum >= 1_000_000_000) {
    return (num / 1_000_000_000).toFixed(1).replace(/\.0$/, '') + 'B';
  }
  if (absNum >= 1_000_000) {
    return (num / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
  }
  if (absNum >= 1_000) {
    return (num / 1_000).toFixed(1).replace(/\.0$/, '') + 'K';
  }
  return num.toLocaleString();
}

export default function VideoCard({ video, label, delay = 0 }) {
  if (!video) return null;

  const isYouTube = video.platform === 'youtube';
  const PlatformIcon = isYouTube ? Youtube : Instagram;
  const accentColor = isYouTube ? '#7C3AED' : '#06B6D4';
  const labelBg = isYouTube
    ? 'bg-accent-purple/20 text-accent-purple border-accent-purple/30'
    : 'bg-accent-cyan/20 text-accent-cyan border-accent-cyan/30';

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay, ease: 'easeOut' }}
      className="glassmorphism rounded-2xl overflow-hidden hover:border-white/15 transition-all duration-300"
    >
      {/* Header Badge */}
      <div className="px-6 pt-5 pb-2 flex items-center justify-between">
        <span className={`text-xs font-bold px-3 py-1 rounded-full border ${labelBg}`}>
          {label}
        </span>
        <PlatformIcon className="w-5 h-5 text-gray-500" />
      </div>

      {/* Thumbnail */}
      {video.thumbnail && (
        <div className="px-6 pb-3">
          <div className="relative rounded-xl overflow-hidden group">
            <img
              src={video.thumbnail}
              alt={video.title}
              className="w-full h-44 object-cover transition-transform duration-300 group-hover:scale-105"
              onError={(e) => {
                e.target.src = `https://placehold.co/640x360/1f2937/6b7280?text=${label}`;
              }}
            />
            {video.duration_formatted && (
              <span className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded-md flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {video.duration_formatted}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Title & Creator */}
      <div className="px-6 pb-3 space-y-2">
        <h3 className="font-heading font-bold text-white text-sm line-clamp-2 leading-tight">
          {video.title || 'Untitled'}
        </h3>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-accent-purple to-accent-cyan flex items-center justify-center">
            <User className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-200">{video.creator_name}</p>
            {video.follower_count && (
              <p className="text-xs text-gray-500 flex items-center gap-1">
                <Users className="w-3 h-3" />
                {formatNumber(video.follower_count)} followers
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="px-6 pb-3">
        <div className="grid grid-cols-3 gap-2">
          <MetadataBadge icon={Eye} label="Views" value={formatNumber(video.views)} color="text-accent-cyan" />
          <MetadataBadge icon={Heart} label="Likes" value={formatNumber(video.likes)} color="text-red-400" />
          <MetadataBadge
            icon={MessageCircle}
            label="Comments"
            value={formatNumber(video.comments)}
            color="text-accent-green"
          />
        </div>
      </div>

      {/* Engagement Bar */}
      <div className="px-6 pb-3">
        <EngagementBar rate={video.engagement_rate || 0} color={accentColor} />
      </div>

      {/* Meta Info */}
      <div className="px-6 pb-5 space-y-2">
        {video.upload_date && (
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Calendar className="w-3 h-3" />
            <span>{video.upload_date}</span>
          </div>
        )}
        {video.hashtags && video.hashtags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {video.hashtags.slice(0, 5).map((tag, i) => (
              <span
                key={i}
                className="text-xs px-2 py-0.5 rounded-full bg-accent-purple/10 text-accent-purple border border-accent-purple/20 flex items-center gap-0.5"
              >
                <Hash className="w-2.5 h-2.5" />
                {tag}
              </span>
            ))}
          </div>
        )}
        {video.transcript_available && (
          <div className="flex items-center gap-1 text-xs text-accent-green">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-green" />
            Transcript available
          </div>
        )}
      </div>
    </motion.div>
  );
}