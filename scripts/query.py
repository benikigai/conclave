#!/usr/bin/env python3
"""
Query a single council member with RAG-retrieved context.

Retrieves relevant chunks from the persona's vector store, assembles
the prompt with the persona's decision framework, and calls the configured LLM.

Usage:
    python scripts/query.py --persona sun-tzu --question "Should I expand into a new market?"
    python scripts/query.py --persona warren-buffett -q "Is this investment worth the risk?" --top-k 8
"""

import sys
from pathlib import Path

import click
import chromadb
from rich.console import Console
from rich.markdown import Markdown

from llm import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    SUPPORTED_PROVIDERS,
    create_client,
    model_for_provider,
    response_text,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COUNCIL_DIR = PROJECT_ROOT / "council"
VECTOR_STORE_DIR = PROJECT_ROOT / "vector_stores"
DEFAULT_TOP_K = 5
console = Console()


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def retrieve_context(persona: str, question: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """Retrieve top-k relevant chunks from a persona's vector store."""
    store_path = VECTOR_STORE_DIR / persona
    if not store_path.exists():
        return []

    client = chromadb.PersistentClient(path=str(store_path))
    try:
        collection = client.get_collection(name=persona)
    except ValueError:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=min(top_k, collection.count()),
    )

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i].get("source", "unknown"),
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })

    return chunks


# ---------------------------------------------------------------------------
# Persona loading
# ---------------------------------------------------------------------------

def load_persona(persona: str) -> dict:
    """Load persona.md and decision-framework.md for a council member."""
    persona_dir = COUNCIL_DIR / persona

    persona_md = persona_dir / "persona.md"
    framework_md = persona_dir / "decision-framework.md"

    return {
        "persona": persona_md.read_text() if persona_md.exists() else "",
        "framework": framework_md.read_text() if framework_md.exists() else "",
    }


def get_persona_names() -> list[str]:
    """List all persona directory names."""
    return sorted(
        d.name
        for d in COUNCIL_DIR.iterdir()
        if d.is_dir() and (d / "persona.md").exists()
    )


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

def build_system_prompt(persona_content: dict, retrieved_chunks: list[dict]) -> str:
    """Assemble the system prompt from persona, framework, and retrieved context."""
    parts = []

    parts.append("You are a member of a personal advisory council. Respond in character.\n")
    parts.append(persona_content["persona"])
    parts.append("\n\n---\n\n")
    parts.append(persona_content["framework"])

    if retrieved_chunks:
        parts.append("\n\n---\n\n")
        parts.append("The following passages from your knowledge base are relevant:\n")
        for chunk in retrieved_chunks:
            parts.append(f"\n---\n{chunk['text']}\n[Source: {chunk['source']}]\n---\n")
        parts.append(
            "\nDraw on these passages where relevant, but trust your lived wisdom "
            "over any single quote.\n"
        )

    parts.append(
        "\n\nStructure your response with these sections:\n"
        "### Analysis\n"
        "### Key Insight\n"
        "### Recommendation\n"
        "### Verdict\n"
    )

    return "".join(parts)


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def query_persona(
    persona: str,
    question: str,
    top_k: int = DEFAULT_TOP_K,
    model: str | None = None,
    provider: str = DEFAULT_PROVIDER,
) -> str:
    """Query a single council member and return their response."""
    persona_content = load_persona(persona)
    retrieved_chunks = retrieve_context(persona, question, top_k=top_k)

    system_prompt = build_system_prompt(persona_content, retrieved_chunks)

    selected_model = model or model_for_provider(provider)
    client = create_client(provider)
    response = client.messages.create(
        model=selected_model,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": question}],
    )

    return response_text(response)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.option(
    "--persona",
    "-p",
    type=str,
    required=True,
    help="Name of the council member to query.",
)
@click.option(
    "--question",
    "-q",
    type=str,
    required=True,
    help="Your question or situation.",
)
@click.option(
    "--top-k",
    type=int,
    default=DEFAULT_TOP_K,
    show_default=True,
    help="Number of chunks to retrieve.",
)
@click.option(
    "--provider",
    type=click.Choice(SUPPORTED_PROVIDERS),
    default=DEFAULT_PROVIDER,
    show_default=True,
    help="LLM provider to use.",
)
@click.option(
    "--model",
    type=str,
    default=None,
    help=f"Model override (provider default: {DEFAULT_MODEL}).",
)
def main(persona: str, question: str, top_k: int, provider: str, model: str | None):
    """Query a single council member with RAG-retrieved context."""
    if persona not in get_persona_names():
        click.echo(f"Unknown persona: {persona}")
        click.echo(f"Available: {', '.join(get_persona_names())}")
        sys.exit(1)

    selected_model = model or model_for_provider(provider)
    console.print(
        f"\n[bold]Consulting {persona}...[/bold] "
        f"[dim]({provider}/{selected_model})[/dim]\n"
    )

    response = query_persona(
        persona,
        question,
        top_k=top_k,
        model=selected_model,
        provider=provider,
    )

    console.print(Markdown(f"## {persona.replace('-', ' ').title()}\n\n{response}"))


if __name__ == "__main__":
    main()
