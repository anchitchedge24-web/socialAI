import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Youtube, Instagram, Zap, Loader2 } from 'lucide-react';
import URLInput from './URLInput';
import useAppStore from '../../store/appStore';
import { useVideoAnalysis } from '../../hooks/useVideoAnalysis';

export default function VideoInputForm() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [instagramUrl, setInstagramUrl] = useState('');
  const [errors, setErrors] = useState({});

  const { isAnalyzing } = useAppStore();
  const { analyze } = useVideoAnalysis();

  const validateUrls = () => {
    const newErrors = {};
    if (!youtubeUrl.trim()) {
      newErrors.youtube = 'YouTube URL is required';
    } else if (
      !/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)/.test(youtubeUrl)
    ) {
      newErrors.youtube = 'Invalid YouTube URL format';
    }

    if (!instagramUrl.trim()) {
      newErrors.instagram = 'Instagram URL is required';
    } else if (
      !/instagram\.com\/(?:reel|reels|p|tv)\//.test(instagramUrl)
    ) {
      newErrors.instagram = 'Invalid Instagram URL format';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateUrls()) return;
    await analyze(youtubeUrl, instagramUrl);
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className="glassmorphism rounded-2xl p-6 space-y-4"
    >
      <h2 className="font-heading text-lg font-bold text-white flex items-center gap-2">
        <Zap className="w-5 h-5 text-accent-purple" />
        Compare Videos
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <URLInput
          label="YouTube Video"
          placeholder="https://youtube.com/watch?v=..."
          value={youtubeUrl}
          onChange={setYoutubeUrl}
          icon={Youtube}
          error={errors.youtube}
        />
        <URLInput
          label="Instagram Reel"
          placeholder="https://instagram.com/reel/..."
          value={instagramUrl}
          onChange={setInstagramUrl}
          icon={Instagram}
          error={errors.instagram}
        />
      </div>

      <motion.button
        type="submit"
        disabled={isAnalyzing}
        whileHover={{ scale: isAnalyzing ? 1 : 1.02 }}
        whileTap={{ scale: isAnalyzing ? 1 : 0.98 }}
        className={`w-full py-3 px-6 rounded-xl font-semibold text-sm transition-all duration-200 flex items-center justify-center gap-2 ${
          isAnalyzing
            ? 'bg-accent-purple/50 cursor-not-allowed text-white/70'
            : 'bg-gradient-to-r from-accent-purple to-accent-cyan text-white hover:shadow-lg hover:shadow-accent-purple/25'
        }`}
      >
        {isAnalyzing ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Analyzing Videos...
          </>
        ) : (
          <>
            <Zap className="w-4 h-4" />
            Analyze & Compare
          </>
        )}
      </motion.button>
    </motion.form>
  );
}