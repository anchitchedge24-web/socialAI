import logging
import json
import re
from typing import Dict, Any
from rag.graph.state import GraphState
from rag.retriever import Retriever
from memory.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)

retriever = Retriever()
memory = ConversationMemory()


def input_parser(state: GraphState) -> GraphState:
    logger.info(f"Parsing input: {state['query'][:50]}...")
    history = memory.get_formatted_history(state["session_id"])
    state["conversation_history"] = history
    video_ctx = memory.get_video_context(state["session_id"])
    state["video_context"] = video_ctx
    return state


def metadata_retriever(state: GraphState) -> GraphState:
    logger.info("Retrieving metadata context...")
    video_ctx = state.get("video_context", {})
    if not video_ctx:
        state["metadata_context"] = "No video metadata available."
        return state

    parts = []
    for label, key in [("Video A (YouTube)", "video_a"), ("Video B (Instagram)", "video_b")]:
        v = video_ctx.get(key, {})
        if v:
            parts.append(
                f"{label}:\n"
                f"  Title: {v.get('title', 'N/A')}\n"
                f"  Creator: {v.get('creator_name', 'N/A')}\n"
                f"  Views: {v.get('views', 0):,}\n"
                f"  Likes: {v.get('likes', 0):,}\n"
                f"  Comments: {v.get('comments', 0):,}\n"
                f"  Engagement Rate: {v.get('engagement_rate', 0)}%\n"
                f"  Duration: {v.get('duration_formatted', 'N/A')}\n"
                f"  Platform: {v.get('platform', 'N/A')}\n"
                f"  Upload Date: {v.get('upload_date', 'N/A')}\n"
                f"  Hashtags: {', '.join(v.get('hashtags', []))}\n"
                f"  Followers: {v.get('follower_count', 'N/A')}"
            )

    state["metadata_context"] = "\n\n".join(parts) if parts else "No metadata available."
    return state


def vector_retrieval(state: GraphState) -> GraphState:
    logger.info("Performing vector retrieval...")
    query = state["query"]

    try:
        results = retriever.retrieve(query, n_results=6)
        state["retrieved_chunks"] = results

        evidence = []
        sources = []
        for r in results:
            video_label = f"Video {r['video_id']}"
            snippet = r["text"][:300]
            evidence.append(f"[{video_label} - {r['chunk_id']}]: {snippet}")
            sources.append({
                "video_id": r["video_id"],
                "chunk_id": r["chunk_id"],
                "text_snippet": snippet,
                "relevance_score": r["relevance_score"],
                "timestamp_start": r.get("metadata", {}).get("timestamp_start"),
                "timestamp_end": r.get("metadata", {}).get("timestamp_end"),
            })

        state["evidence"] = evidence
        state["sources"] = sources
    except Exception as e:
        logger.error(f"Vector retrieval failed: {e}")
        state["retrieved_chunks"] = []
        state["evidence"] = []
        state["sources"] = []

    return state


def reasoning_node(state: GraphState) -> GraphState:
    logger.info("Generating reasoning...")
    query = state["query"]
    metadata = state.get("metadata_context", "")
    evidence = state.get("evidence", [])
    history = state.get("conversation_history", "")

    evidence_text = "\n".join(evidence[:5]) if evidence else "No transcript evidence available."

    prompt = build_reasoning_prompt(query, metadata, evidence_text, history)
    state["reasoning"] = prompt
    return state


def build_reasoning_prompt(query: str, metadata: str, evidence: str, history: str) -> str:
    prompt = f"""You are an expert social media analyst comparing two videos.

VIDEO METADATA:
{metadata}

TRANSCRIPT EVIDENCE:
{evidence}

"""
    if history:
        prompt += f"""CONVERSATION HISTORY:
{history}

"""
    prompt += f"""USER QUESTION: {query}

Provide a thorough, data-driven analysis. Include specific numbers and comparisons.
Ground your answer in the evidence provided. Be specific about which video you're referencing.
If comparing, explain WHY one performs better based on content, hooks, and engagement patterns."""

    return prompt


def response_formatter(state: GraphState) -> GraphState:
    logger.info("Formatting response...")
    if not state.get("answer"):
        state["answer"] = ""

    sources = state.get("sources", [])
    if sources and state.get("answer"):
        citation_block = "\n\n**Sources:**\n"
        seen = set()
        for s in sources[:5]:
            key = f"{s['video_id']}_{s['chunk_id']}"
            if key not in seen:
                seen.add(key)
                ts = ""
                if s.get("timestamp_start") is not None:
                    ts = f" (t={s['timestamp_start']:.1f}s-{s['timestamp_end']:.1f}s)"
                citation_block += f"- [{s['video_id']} - {s['chunk_id']}]{ts} (relevance: {s['relevance_score']:.2f})\n"
        state["answer"] += citation_block

    return state


def confidence_scorer(state: GraphState) -> GraphState:
    sources = state.get("sources", [])
    if sources:
        avg_relevance = sum(s["relevance_score"] for s in sources) / len(sources)
        has_both_videos = len(set(s["video_id"] for s in sources)) >= 2
        bonus = 0.1 if has_both_videos else 0.0
        state["confidence"] = min(round(avg_relevance + bonus, 2), 1.0)
    else:
        state["confidence"] = 0.3
    return state


def memory_updater(state: GraphState) -> GraphState:
    session_id = state.get("session_id", "default")
    memory.add_message(session_id, "user", state["query"])
    answer = state.get("answer", "")
    if answer:
        clean_answer = answer.split("**Sources:**")[0].strip()
        memory.add_message(session_id, "assistant", clean_answer[:500])
    return state