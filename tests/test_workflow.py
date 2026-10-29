"""
Automated checks for the CI pipeline (Task 5).

These deliberately avoid the network and the API key, so the pipeline
is fast and does not need a secret to run. They test the pure helpers
and confirm that the graph assembles correctly.
"""

import workflow


def test_format_results_builds_numbered_text():
    results = [
        {"title": "First result", "body": "Some summary text.", "href": "https://a.example"},
        {"title": "Second result", "body": "More text.", "href": "https://b.example"},
    ]
    out = workflow.format_results(results)

    assert "[1] First result" in out
    assert "[2] Second result" in out
    assert "Source: https://a.example" in out


def test_format_results_handles_empty_list():
    assert workflow.format_results([]) == "No search results found."


def test_extract_text_handles_plain_string():
    class FakeResponse:
        content = "  a plain string reply  "

    assert workflow.extract_text(FakeResponse()) == "a plain string reply"


def test_extract_text_handles_block_list():
    class FakeResponse:
        content = [
            {"type": "text", "text": "first part"},
            {"type": "other", "data": "ignored"},
            {"type": "text", "text": "second part"},
        ]

    assert workflow.extract_text(FakeResponse()) == "first part\nsecond part"


def test_graph_has_both_nodes_in_order():
    graph = workflow.build_graph()
    nodes = graph.get_graph().nodes

    assert "search" in nodes
    assert "summarize" in nodes


def test_prompt_requires_exactly_three_bullets():
    rendered = workflow.SUMMARY_PROMPT.format(
        topic="test topic", raw_results="test results"
    )
    assert "exactly three bullet points" in rendered
    assert "ONLY the search results" in rendered
