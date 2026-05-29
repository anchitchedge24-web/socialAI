import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3, Sparkles } from 'lucide-react';
import VideoInputForm from './components/VideoInput/VideoInputForm';
import VideoCard from './components/VideoCard/VideoCard';
import SkeletonCard from './components/VideoCard/SkeletonCard';
import ChatPanel from './components/Chat/ChatPanel';
import ToastContainer from './components/UI/Toast';
import useAppStore from './store/appStore';

export default function App() {
  const { videoA, videoB, isAnalyzing, analysisComplete, analysisError, chunksCreated } = useAppStore();

  return (
    <div className="min-h-screen bg-bg-primary">
      <ToastContainer />

      {/* Header */}
      <header className="border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-purple to-accent-cyan flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-heading text-xl font-bold text-white">SocialRAG</h1>
              <p className="text-xs text-gray-500">AI-Powered Video Comparison</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {analysisComplete && (
              <motion.span
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-xs px-3 py-1 rounded-full bg-accent-green/10 text-accent-green border border-accent-green/20 flex items-center gap-1"
              >
                <Sparkles className="w-3 h-3" />
                {chunksCreated} chunks indexed
              </motion.span>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Input Form */}
        <VideoInputForm />

        {/* Error State */}
        {analysisError && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="p-4 rounded-xl bg-red-400/10 border border-red-400/20 text-red-300 text-sm"
          >
            <strong>Error:</strong> {analysisError}
          </motion.div>
        )}

        {/* Video Cards */}
        {(isAnalyzing || analysisComplete) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {isAnalyzing && !videoA ? (
              <>
                <SkeletonCard />
                <SkeletonCard />
              </>
            ) : (
              <>
                {videoA && <VideoCard video={videoA} label="Video A — YouTube" delay={0} />}
                {videoB && <VideoCard video={videoB} label="Video B — Instagram" delay={0.15} />}
              </>
            )}
          </div>
        )}

        {/* Chat Panel */}
        <ChatPanel />
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center text-xs text-gray-600">
          Built with FastAPI • React • ChromaDB • LangGraph • Llama
        </div>
      </footer>
    </div>
  );
}