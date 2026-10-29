"""
workflow.py — the Experiment 9 search-and-summarize pipeline, packaged
as an importable module.

Kept separate from app.py so that the graph logic can be unit-tested in
CI without starting Streamlit and without needing an API key.
"""

import logging
import os
from typing import TypedDict

from ddgs import DDGS
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

logger = logging.getLogger(__name__)

MODEL_NAME = os.environ.get("MODEL_NAME", "gemini-3.1-flash-lite-preview")


# --------------------------------------------------------------------
# State
# --------------------------------------------------------------------
class WorkflowState(TypedDict):
    """Shared state passed between nodes.

    Each node returns only the keys it updates; LangGraph merges them.
    """
    topic: str
    raw_results: str
    brief: str


# --------------------------------------------------------------------
# Model — created lazily
# --------------------------------------------------------------------
def get_llm(temperature: float = 0.3) -> ChatGoogleGenerativeAI:
    """Build the model object on demand.

    Lazy construction matters for CI: importing this module must not
    require GOOGLE_API_KEY, otherwise the test job fails before it runs.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Pass it as an environment variable "
            "at run time; never write it into the code or the image."
        )
    return ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=temperature)


# --------------------------------------------------------------------
# Pure helpers — these are what CI tests, since they need no network
# --------------------------------------------------------------------
def format_results(results: list[dict]) -> str:
    """Flatten DuckDuckGo result dicts into numbered readable text.

    The model reads text, so the results are structured clearly rather
    than passed as raw JSON.
    """
    if not results:
        return "No search results found."

    blocks = []
    for i, r in enumerate(results, 1):
        blocks.append(
            f"[{i}] {r.get('title', '')}\n"
            f"{r.get('body', '')}\n"
            f"Source: {r.get('href', '')}"
        )
    return "\n\n".join(blocks)


def extract_text(response) -> str:
    """Normalise a model reply to plain text.

    Newer Gemini models may return .content as a list of content blocks
    rather than a string.
    """
    content = response.content
    if isinstance(content, str):
        return content.strip()
    parts = [
        b["text"] for b in content
        if isinstance(b, dict) and b.get("type") == "text"
    ]
    return "\n".join(parts).strip()


SUMMARY_PROMPT = ChatPromptTemplate.from_template(
    """You are a research assistant preparing a short brief.

Using ONLY the search results below, write exactly three bullet points
summarising the current state of the topic. Each bullet should be one
sentence, factual, and specific. Do not add an introduction or conclusion.
If the results do not cover something, do not invent it.

Topic: {topic}

Search results:
{raw_results}

Three-bullet brief:"""
)


# --------------------------------------------------------------------
# Nodes
# --------------------------------------------------------------------
def search_node(state: WorkflowState) -> dict:
    """Stage 1 — query DuckDuckGo and return the results as text."""
    topic = state["topic"]
    logger.info("SEARCH stage started | topic=%s", topic)

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(topic, max_results=5))
    except Exception as exc:
        logger.error("SEARCH stage failed | topic=%s | error=%s", topic, exc)
        return {"raw_results": f"Search failed: {exc}"}

    text = format_results(results)
    logger.info(
        "SEARCH stage finished | results=%d | chars=%d", len(results), len(text)
    )
    return {"raw_results": text}


def summarize_node(state: WorkflowState) -> dict:
    """Stage 2 — condense the raw results into a three-bullet brief."""
    logger.info("SUMMARIZE stage started")

    try:
        response = (SUMMARY_PROMPT | get_llm()).invoke({
            "topic": state["topic"],
            "raw_results": state["raw_results"],
        })
        brief = extract_text(response)
    except Exception as exc:
        logger.error("SUMMARIZE stage failed | error=%s", exc)
        return {"brief": f"Summarization failed: {exc}"}

    logger.info("SUMMARIZE stage finished | chars=%d", len(brief))
    return {"brief": brief}


# --------------------------------------------------------------------
# Graph
# --------------------------------------------------------------------
def build_graph():
    """Wire the two stages into a fixed sequential workflow.

    The path is decided here at build time, not by the model — this is a
    predictable pipeline, not an autonomous agent.
    """
    builder = StateGraph(WorkflowState)
    builder.add_node("search", search_node)
    builder.add_node("summarize", summarize_node)
    builder.add_edge(START, "search")
    builder.add_edge("search", "summarize")
    builder.add_edge("summarize", END)
    return builder.compile()


def run_workflow(topic: str) -> str:
    """Entry point — takes only a topic and returns the finished brief."""
    graph = build_graph()
    final_state = graph.invoke({"topic": topic})
    return final_state["brief"]
