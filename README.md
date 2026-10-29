---
title: Research Brief Agent
emoji: 🔎
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Research Brief Agent

A two-stage task-automation agent: it searches the web for a topic and
summarises the findings into exactly three bullet points.

Built for Experiment 10 (MLOps deployment) of the Generative AI &
Agentic AI laboratory, deploying the LangGraph workflow from Experiment 9.

## Architecture

```
topic ──> [ search node ] ──> raw_results ──> [ summarize node ] ──> brief
            DuckDuckGo                           Gemini + prompt
```

The path is fixed at build time as a LangGraph `StateGraph`. The model
does not choose the route — this is a predictable pipeline, not an
autonomous tool-choosing agent.

| File | Purpose |
|---|---|
| `workflow.py` | State schema, both nodes, graph construction |
| `app.py` | Streamlit interface and request logging |
| `tests/test_workflow.py` | Automated checks run by CI |
| `Dockerfile` | Container definition |
| `.github/workflows/ci.yml` | CI pipeline: tests + Docker build |

## Stack

- **LangGraph** — the two-node state graph
- **Gemini** — the summarisation model
- **DuckDuckGo (`ddgs`)** — web search, no API key required
- **Streamlit** — web interface
- **Docker** — containerisation
- **GitHub Actions** — CI
- **Hugging Face Spaces** — hosting, rebuilds automatically on push

## Running locally

```bash
pip install -r requirements.txt
export GOOGLE_API_KEY=your_key_here
streamlit run app.py
```

## Running in Docker

```bash
docker build -t research-brief-agent .
docker run -p 7860:7860 -e GOOGLE_API_KEY=your_key_here research-brief-agent
```

Then open http://localhost:7860

## Configuration

| Variable | Required | Purpose |
|---|---|---|
| `GOOGLE_API_KEY` | yes | Gemini API key |
| `MODEL_NAME` | no | Overrides the default model |

The API key is never written into the source, the Dockerfile or the
image. It is passed as an environment variable at run time, and stored
in the Hugging Face Space's secrets settings when deployed.
