import { create } from 'zustand';

const useAppStore = create((set, get) => ({
  // Video state
  videoA: null,
  videoB: null,
  isAnalyzing: false,
  analysisError: null,
  analysisComplete: false,
  chunksCreated: 0,

  // Chat state
  messages: [],
  isStreaming: false,
  chatError: null,

  // Toast state
  toasts: [],

  // Actions - Video
  setVideoA: (data) => set({ videoA: data }),
  setVideoB: (data) => set({ videoB: data }),
  setAnalyzing: (val) => set({ isAnalyzing: val }),
  setAnalysisError: (err) => set({ analysisError: err }),
  setAnalysisComplete: (val) => set({ analysisComplete: val }),
  setChunksCreated: (count) => set({ chunksCreated: count }),

  // Actions - Chat
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  updateLastAssistantMessage: (content) =>
    set((state) => {
      const messages = [...state.messages];
      for (let i = messages.length - 1; i >= 0; i--) {
        if (messages[i].role === 'assistant') {
          messages[i] = { ...messages[i], content };
          break;
        }
      }
      return { messages };
    }),

  setStreaming: (val) => set({ isStreaming: val }),
  setChatError: (err) => set({ chatError: err }),
  clearMessages: () => set({ messages: [] }),

  // Actions - Toast
  addToast: (toast) =>
    set((state) => ({
      toasts: [
        ...state.toasts,
        { id: Date.now(), ...toast },
      ],
    })),

  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),

  // Reset
  resetAll: () =>
    set({
      videoA: null,
      videoB: null,
      isAnalyzing: false,
      analysisError: null,
      analysisComplete: false,
      chunksCreated: 0,
      messages: [],
      isStreaming: false,
      chatError: null,
    }),
}));

export default useAppStore;