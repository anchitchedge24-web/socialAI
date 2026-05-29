import logging
import json
import httpx
from typing import AsyncGenerator
from config.settings import get_settings
from rag.graph.state import GraphState
from rag.graph.nodes import (
    input_parser,
    metadata_retriever,
    vector_retrieval,
    reasoning_node,
    response_formatter,
    confidence_scorer,
    memory_updater,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class RAGPipeline:
    def __init__(self):
        self.use_ollama = settings.USE_OLLAMA
        self.use_groq = settings.USE_GROQ
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL
        self.groq_url = settings.GROQ_BASE_URL
        self.groq_model = settings.GROQ_MODEL
        self.groq_key = settings.GROQ_API_KEY

        # Decide which provider to use
        if self.use_groq and self.groq_key:
            self.provider = "groq"
            logger.info(f"🚀 LLM Provider: Groq ({self.groq_model})")
        elif self.use_ollama:
            self.provider = "ollama"
            logger.info(f"🚀 LLM Provider: Ollama ({self.ollama_model})")
        else:
            self.provider = "fallback"
            logger.warning("⚠️ No LLM provider configured — using fallback responses")

    def _run_graph_nodes(self, query: str, session_id: str) -> GraphState:
        state: GraphState = {
            "query": query,
            "session_id": session_id,
            "conversation_history": "",
            "video_context": {},
            "retrieved_chunks": [],
            "metadata_context": "",
            "reasoning": "",
            "answer": "",
            "evidence": [],
            "sources": [],
            "confidence": 0.0,
            "error": None,
        }

        state = input_parser(state)
        state = metadata_retriever(state)
        state = vector_retrieval(state)
        state = reasoning_node(state)
        state = confidence_scorer(state)
        return state

    async def stream_response(self, query: str, session_id: str = "default") -> AsyncGenerator[str, None]:
        try:
            state = self._run_graph_nodes(query, session_id)
            prompt = state["reasoning"]

            full_answer = ""

            # Route to correct provider
            if self.provider == "groq":
                async for token in self._stream_groq(prompt):
                    full_answer += token
                    yield token
            elif self.provider == "ollama":
                async for token in self._stream_ollama(prompt):
                    full_answer += token
                    yield token
            else:
                # Fallback (no LLM available)
                fallback = self._generate_fallback(state)
                words = fallback.split(" ")
                for i, word in enumerate(words):
                    token = word + (" " if i < len(words) - 1 else "")
                    full_answer += token
                    yield token

            # Append citations + confidence
            state["answer"] = full_answer
            state = response_formatter(state)

            sources_section = state["answer"][len(full_answer):]
            if sources_section:
                yield sources_section

            confidence = state.get("confidence", 0.0)
            yield f"\n\n**Confidence:** {confidence:.0%}"

            state = memory_updater(state)

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            yield f"I encountered an error while processing your question: {str(e)}"

    async def _stream_groq(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream response from Groq's OpenAI-compatible API."""
        url = f"{self.groq_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert social media analyst comparing two videos. Provide thorough, data-driven analysis with specific numbers. Ground your answers in the evidence provided.",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": True,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Groq API error {response.status_code}: {error_text.decode()[:300]}")
                        yield f"Groq API error: {response.status_code}. Check your API key."
                        return

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue

                        data = line[6:].strip()
                        if data == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data)
                            choices = chunk.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                token = delta.get("content", "")
                                if token:
                                    yield token
                        except json.JSONDecodeError:
                            continue

        except httpx.ConnectError:
            logger.error("Cannot reach Groq API")
            yield "Cannot reach Groq API. Check internet connection."
        except Exception as e:
            logger.error(f"Groq streaming failed: {e}", exc_info=True)
            yield f"Error: {str(e)}"

    async def _stream_ollama(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream response from local Ollama."""
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": settings.LLM_TEMPERATURE,
                "num_predict": settings.LLM_MAX_TOKENS,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                token = data.get("response", "")
                                if token:
                                    yield token
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError:
            logger.warning("Ollama not available, using fallback")
            yield "Ollama is not running. Please start it with `ollama serve`."
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            yield f"Error: {str(e)}"

    def _generate_fallback(self, state: GraphState) -> str:
        """Fallback when no LLM is available."""
        return (
            "No LLM provider is currently available. "
            "Please configure either Ollama (USE_OLLAMA=true) or Groq (USE_GROQ=true with GROQ_API_KEY)."
        )

    async def generate_response(self, query: str, session_id: str = "default") -> GraphState:
        state = self._run_graph_nodes(query, session_id)

        full_answer = ""
        if self.provider == "groq":
            async for token in self._stream_groq(state["reasoning"]):
                full_answer += token
        elif self.provider == "ollama":
            async for token in self._stream_ollama(state["reasoning"]):
                full_answer += token
        else:
            full_answer = self._generate_fallback(state)

        state["answer"] = full_answer
        state = response_formatter(state)
        state = confidence_scorer(state)
        state = memory_updater(state)
        return state