import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, X, Github, Instagram } from 'lucide-react';

const STORAGE_KEY = 'socialrag_banner_dismissed';

export default function DeploymentBanner() {
  const [visible, setVisible] = useState(false);

  // Only show on deployed version (when VITE_API_URL is set)
  const isDeployed = Boolean(import.meta.env.VITE_API_URL);

  useEffect(() => {
    if (!isDeployed) return;

    // Check if user already dismissed it this session
    const dismissed = sessionStorage.getItem(STORAGE_KEY);
    if (!dismissed) {
      // Small delay so it doesn't pop in immediately
      const timer = setTimeout(() => setVisible(true), 800);
      return () => clearTimeout(timer);
    }
  }, [isDeployed]);

  const handleDismiss = () => {
    setVisible(false);
    sessionStorage.setItem(STORAGE_KEY, 'true');
  };

  if (!isDeployed) return null;

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          className="relative mb-6"
        >
          <div className="glassmorphism rounded-2xl border-accent-warning/30 bg-gradient-to-r from-accent-warning/5 via-accent-purple/5 to-accent-cyan/5 p-4 md:p-5">
            <div className="flex items-start gap-3">
              {/* Icon */}
              <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-accent-warning/10 border border-accent-warning/20 flex items-center justify-center">
                <Info className="w-4 h-4 text-accent-warning" />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5">
                  <h3 className="text-sm font-heading font-bold text-white">
                    Live Demo Notice
                  </h3>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-accent-warning/10 text-accent-warning border border-accent-warning/20">
                    Hosted
                  </span>
                </div>

                <p className="text-xs md:text-sm text-gray-400 leading-relaxed">
                  <span className="inline-flex items-center gap-1 text-gray-300 font-medium">
                    <Instagram className="w-3.5 h-3.5 text-accent-cyan" />
                    Instagram extraction
                  </span>{' '}
                  requires browser cookies and may be rate-limited on this hosted version.
                  For full functionality (Instagram Reels + Whisper transcription),{' '}
                  <a
                    href="https://github.com/cokefloat07/social-bot.git"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-accent-purple hover:text-accent-cyan inline-flex items-center gap-1 font-medium transition-colors underline-offset-2 hover:underline"
                  >
                    clone and run locally
                    <Github className="w-3 h-3" />
                  </a>.
                </p>

                <p className="text-xs text-gray-500 mt-2">
                  💡 Tip: Try with two YouTube URLs for the best experience.
                </p>
              </div>

              {/* Dismiss button */}
              <button
                onClick={handleDismiss}
                className="flex-shrink-0 w-7 h-7 rounded-lg text-gray-500 hover:text-gray-200 hover:bg-white/5 transition-all duration-200 flex items-center justify-center"
                aria-label="Dismiss notice"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}