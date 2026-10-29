"""
app.py — Streamlit web interface for the task-automation agent.

Task 1: the user enters a topic and receives the three-point brief.
Task 7: timing and errors are logged to stdout, which the hosting
platform collects and displays as application logs.
"""

import logging
import time

import streamlit as st

from workflow import run_workflow

# ----------------------------------------------------------------------
# Logging (Task 7)
# Logs go to stdout so that Hugging Face Spaces captures them without
# any extra configuration.
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("app")

st.set_page_config(page_title="Research Brief Agent", page_icon="::", layout="centered")

st.title("AI Research Brief Generator")
st.caption(
    "Enter a topic. The agent searches the web, then summarises the findings "
    "into exactly three bullet points."
)

topic = st.text_input(
    "Topic",
    placeholder="e.g. ISRO Gaganyaan mission latest status",
)

if st.button("Generate brief", type="primary"):
    if not topic.strip():
        st.warning("Please enter a topic first.")
    else:
        logger.info("REQUEST received | topic=%s", topic)
        started = time.time()

        try:
            with st.status("Running workflow...", expanded=True) as status:
                st.write("Stage 1 of 2 — searching the web")
                brief = run_workflow(topic)
                st.write("Stage 2 of 2 — summarising the findings")
                status.update(label="Workflow complete", state="complete")

            elapsed = time.time() - started
            logger.info(
                "REQUEST completed | topic=%s | seconds=%.2f", topic, elapsed
            )

            st.subheader("Research brief")
            st.markdown(brief)
            st.caption(f"Generated in {elapsed:.2f} seconds")

        except Exception as exc:
            elapsed = time.time() - started
            logger.exception(
                "REQUEST failed | topic=%s | seconds=%.2f | error=%s",
                topic, elapsed, exc,
            )
            st.error(f"Something went wrong: {exc}")

st.divider()
st.caption(
    "Experiment 10 — MLOps deployment of the Experiment 9 workflow. "
    "Built with LangGraph, Gemini and Streamlit."
)
