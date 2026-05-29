import { useCallback } from 'react';
import useAppStore from '../store/appStore';
import { streamChat } from '../services/api';

export function useChat() {
  const {
    addMessage,
    updateLastAssistantMessage,
    setStreaming,
    setChatError,
    isStreaming,
  } = useAppStore();

  const sendMessage = useCallback(async (message) => {
    if (isStreaming || !message.trim()) return;

    addMessage({ role: 'user', content: message });
    addMessage({ role: 'assistant', content: '' });
    setStreaming(true);
    setChatError(null);

    let accumulated = '';

    await streamChat(
      message,
      'default',
      (token) => {
        accumulated += token;
        updateLastAssistantMessage(accumulated);
      },
      () => {
        setStreaming(false);
      },
      (error) => {
        setChatError(error);
        setStreaming(false);
        updateLastAssistantMessage(
          `Error: ${error}. Please try again.`
        );
      }
    );
  }, [isStreaming]);

  return { sendMessage };
}