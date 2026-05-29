const API_BASE = import.meta.env.VITE_API_URL || '/api';

export async function analyzeVideos(youtubeUrl, instagramUrl) {
  const response = await fetch(`${API_BASE}/analyze-videos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      youtube_url: youtubeUrl,
      instagram_url: instagramUrl,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Analysis failed' }));
    throw new Error(error.detail || 'Analysis failed');
  }

  return response.json();
}

export async function streamChat(message, sessionId = 'default', onToken, onDone, onError) {
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);

            if (data.error) {
              onError(data.error);
              return;
            }

            if (data.done) {
              onDone();
              return;
            }

            if (data.token) {
              onToken(data.token);
            }
          } catch (e) {
            // skip malformed JSON
          }
        }
      }
    }

    onDone();
  } catch (error) {
    onError(error.message);
  }
}

export async function getHealth() {
  const response = await fetch(`${API_BASE}/health`);
  return response.json();
}

export async function getConversationHistory(sessionId = 'default') {
  const response = await fetch(`${API_BASE}/conversation-history?session_id=${sessionId}`);
  return response.json();
}