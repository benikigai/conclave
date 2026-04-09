#!/usr/bin/env python3
"""
Ingest source material into per-persona vector stores.

Reads files from council/<persona>/corpus/, chunks them, embeds them
using OpenAI's text-embedding-3-small, and stores them in a ChromaDB
collection for that persona.

Usage:
    python scripts/ingest.py --persona warren-buffett
    python scripts/ingest.py --all
    python scripts/ingest.py --persona sun-tzu --chunk-size 800 --overlap 150
"""

import os
import sys
from pathlib import Path

import click
import chromadb
import tiktoken

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COUNCIL_DIR = PROJECT_ROOT / "council"
VECTOR_STORE_DIR = PROJECT_ROOT / "vector_stores"
EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_CHUNK_SIZE = 1000  # tokens
DEFAULT_OVERLAP = 200  # tokens


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in a string."""
    enc = tiktoken.get_encoding(encoding_name)
    return len(enc.encode(text))


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """
    Split text into chunks of approximately chunk_size tokens with overlap.

    Uses a separator hierarchy: paragraphs > lines > sentences > words.
    """
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)

    if len(tokens) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)

        if end >= len(tokens):
            break
        start = end - overlap

    return chunks


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings from OpenAI API."""
    from openai import OpenAI

    client = OpenAI()  # uses OPENAI_API_KEY env var
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

def get_persona_names() -> list[str]:
    """List all persona directory names."""
    return sorted(
        d.name
        for d in COUNCIL_DIR.iterdir()
        if d.is_dir() and (d / "corpus").is_dir()
    )


def ingest_persona(persona: str, chunk_size: int, overlap: int) -> None:
    """Ingest all files in a persona's corpus/ directory."""
    corpus_dir = COUNCIL_DIR / persona / "corpus"
    if not corpus_dir.exists():
        click.echo(f"  No corpus directory for {persona}, skipping.")
        return

    # Collect all text files
    files = sorted(
        f
        for f in corpus_dir.iterdir()
        if f.is_file() and f.suffix in (".txt", ".md") and f.name != ".gitkeep"
    )

    if not files:
        click.echo(f"  No source files found in {corpus_dir}/")
        click.echo(f"  Add .txt or .md files to council/{persona}/corpus/ first.")
        return

    click.echo(f"  Found {len(files)} source file(s)")

    # Chunk all files
    all_chunks = []
    all_metadata = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        click.echo(f"    {f.name}: {count_tokens(text)} tokens -> {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "source": f.name,
                "persona": persona,
                "chunk_index": i,
                "total_chunks": len(chunks),
            })

    if not all_chunks:
        click.echo("  No chunks generated.")
        return

    click.echo(f"  Total chunks: {len(all_chunks)}")
    click.echo(f"  Generating embeddings...")

    # Embed in batches of 100
    all_embeddings = []
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        embeddings = get_embeddings(batch)
        all_embeddings.extend(embeddings)
        if len(all_chunks) > batch_size:
            click.echo(
                f"    Embedded batch {i // batch_size + 1}/"
                f"{(len(all_chunks) - 1) // batch_size + 1}"
            )

    # Store in ChromaDB
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR / persona))

    # Delete existing collection if it exists (clean re-ingest)
    try:
        client.delete_collection(name=persona)
    except ValueError:
        pass

    collection = client.create_collection(
        name=persona,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[f"{persona}-{i}" for i in range(len(all_chunks))],
        embeddings=all_embeddings,
        documents=all_chunks,
        metadatas=all_metadata,
    )

    click.echo(f"  Stored {len(all_chunks)} chunks in vector_stores/{persona}/")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.option(
    "--persona",
    type=str,
    help="Name of the persona to ingest (e.g., 'warren-buffett').",
)
@click.option("--all", "ingest_all", is_flag=True, help="Ingest all personas.")
@click.option(
    "--chunk-size",
    type=int,
    default=DEFAULT_CHUNK_SIZE,
    show_default=True,
    help="Target chunk size in tokens.",
)
@click.option(
    "--overlap",
    type=int,
    default=DEFAULT_OVERLAP,
    show_default=True,
    help="Overlap between chunks in tokens.",
)
def main(persona: str | None, ingest_all: bool, chunk_size: int, overlap: int):
    """Ingest source material into per-persona vector stores."""
    if not persona and not ingest_all:
        click.echo("Specify --persona <name> or --all")
        click.echo(f"\nAvailable personas: {', '.join(get_persona_names())}")
        sys.exit(1)

    personas = get_persona_names() if ingest_all else [persona]

    for p in personas:
        if p not in get_persona_names():
            click.echo(f"Unknown persona: {p}")
            click.echo(f"Available: {', '.join(get_persona_names())}")
            sys.exit(1)

        click.echo(f"\nIngesting: {p}")
        ingest_persona(p, chunk_size=chunk_size, overlap=overlap)

    click.echo("\nDone.")


if __name__ == "__main__":
    main()
