# Architecture

## Overview

Conclave uses a per-persona RAG (Retrieval-Augmented Generation) architecture. Each council member has an independent vector store built from source material specific to how that person thinks. An orchestration layer convenes all seven, retrieves relevant context for each, and synthesizes a unified verdict.

```
                         ┌─────────────┐
                         │   Question   │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │  Orchestrator │
                         │ (convene.py)  │
                         └──────┬───────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                  │
        ┌─────▼─────┐   ┌─────▼─────┐     ┌─────▼─────┐
        │  Persona 1 │   │  Persona 2 │ ... │  Persona 7 │
        │  Retrieval │   │  Retrieval │     │  Retrieval │
        └─────┬─────┘   └─────┬─────┘     └─────┬─────┘
              │                │                  │
        ┌─────▼─────┐   ┌─────▼─────┐     ┌─────▼─────┐
        │  Vector DB │   │  Vector DB │     │  Vector DB │
        │  (Arnold)  │   │  (Jobs)    │     │  (Bezos)   │
        └───────────┘   └───────────┘     └───────────┘
              │                │                  │
              └─────────────────┼─────────────────┘
                                │
                         ┌──────▼───────┐
                         │  Synthesis   │
                         │  Prompt      │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                         │Council Verdict│
                         └──────────────┘
```

## Per-Persona Vector Stores

Each council member gets their own isolated vector store. This matters because:

1. **Source fidelity** — Buffett's retrieved chunks come only from Buffett's material. No cross-contamination.
2. **Independent scaling** — You can have 200 documents for one persona and 20 for another.
3. **Clean updates** — Re-ingesting one persona doesn't touch the others.

### Storage

The reference implementation uses **ChromaDB** for simplicity. Each persona's store lives at `vector_stores/<persona-name>/`. The stores are .gitignored — you build them locally from your own source material.

Alternatives that work well:
- **LanceDB** — faster for large corpora, columnar format
- **FAISS** — if you want raw speed and don't need persistence metadata
- **Qdrant** — if you're running this as a service

## Chunking Strategy

Source material is chunked before embedding. The strategy matters more than the embedding model.

### Defaults

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Chunk size | 1000 tokens | Large enough to preserve argument structure, small enough for precise retrieval |
| Overlap | 200 tokens | Prevents losing context at chunk boundaries |
| Separator hierarchy | `\n\n` > `\n` > `. ` > ` ` | Respects document structure — paragraphs > lines > sentences > words |

### Source-Type-Specific Notes

- **Books**: Chapter boundaries make natural chunk points. Chunk within chapters, not across them.
- **Interviews/Transcripts**: Split on speaker turns first, then by size within a turn. Preserve the question that prompted each answer.
- **Letters (e.g., Buffett's shareholder letters)**: Each letter is a natural unit. Chunk within, never across letters.
- **Speeches**: Split on thematic sections. Preserve rhetorical flow within chunks.

## Embedding Model

Default: `text-embedding-3-small` (OpenAI) — 1536 dimensions, good price/performance.

Alternatives:
- `text-embedding-3-large` — better retrieval quality, 3072 dimensions, higher cost
- `voyage-3` (Voyage AI) — strong on long-form reasoning text
- Local models (e.g., `nomic-embed-text`) — if you want to avoid API calls

The embedding model must be consistent across ingest and query time. If you change models, re-ingest everything.

## Retrieval Flow

For each persona query:

1. **Embed the question** using the same model used at ingest time
2. **Retrieve top-k chunks** (default k=5) from that persona's vector store
3. **Assemble the prompt**:
   - System: persona definition + decision framework
   - Context: retrieved chunks, formatted with source attribution
   - User: the question/situation
4. **Call the configured LLM** with the assembled prompt
5. **Return** the structured response

### Retrieval Parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| top_k | 5 | Increase for complex questions, decrease for focused ones |
| score_threshold | 0.3 | Chunks below this similarity score are dropped |
| max_context_tokens | 4000 | Caps total retrieved context to prevent prompt bloat |

## Orchestration Layer

The `convene.py` script orchestrates a full council session:

1. **Parse** the user's question/situation
2. **Fan out** to all seven personas in parallel (async calls)
3. **Collect** all seven responses
4. **Run synthesis** — a separate prompt that takes all seven responses and produces:
   - **Consensus**: What do most/all agree on?
   - **Key Disagreements**: Where do they diverge, and why?
   - **Recommended Actions**: Concrete next steps, informed by the full spectrum
   - **Dissenting Voice**: The strongest contrarian argument

### Parallelism

Persona queries are independent and run concurrently. A full council convocation with 7 personas takes roughly the same wall-clock time as a single query (bound by the slowest response, not the sum).

## Session Artifacts

Each council session can optionally produce a durable artifact:

```
sessions/
└── 2026-04-09-should-i-leave-my-job.md
```

Session files contain the original question, all seven responses, and the synthesis. Over time, this becomes a journal of your hardest decisions — which is more valuable than the tool itself.

## Model Choice

The reference implementation defaults to Qwen3.8-27B through Ollama's Anthropic-compatible API, with Anthropic available as an explicit fallback. The persona prompts and decision frameworks are model-agnostic and work with any LLM that supports system prompts and handles long context well.

Key considerations:
- **Context window**: The system prompt (persona + framework + retrieved chunks) can be 5-8k tokens. The model needs headroom for reasoning.
- **Instruction following**: The persona voice and decision framework require a model that stays in character.
- **Parallel calls**: Convening all seven requires 7 concurrent API calls + 1 synthesis call. Plan your rate limits accordingly.
