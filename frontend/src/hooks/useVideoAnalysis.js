import { useCallback } from 'react';
import useAppStore from '../store/appStore';
import { analyzeVideos } from '../services/api';

export function useVideoAnalysis() {
  const {
    setVideoA,
    setVideoB,
    setAnalyzing,
    setAnalysisError,
    setAnalysisComplete,
    setChunksCreated,
    addToast,
    clearMessages,
  } = useAppStore();

  const analyze = useCallback(async (youtubeUrl, instagramUrl) => {
    setAnalyzing(true);
    setAnalysisError(null);
    setAnalysisComplete(false);
    clearMessages();

    try {
      const result = await analyzeVideos(youtubeUrl, instagramUrl);

      setVideoA(result.video_a);
      setVideoB(result.video_b);
      setChunksCreated(result.chunks_created);
      setAnalysisComplete(true);

      addToast({
        type: 'success',
        message: `Analysis complete! ${result.chunks_created} chunks created.`,
      });
    } catch (error) {
      setAnalysisError(error.message);
      addToast({
        type: 'error',
        message: error.message,
      });
    } finally {
      setAnalyzing(false);
    }
  }, []);

  return { analyze };
}