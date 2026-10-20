# Conclave

**A personal AI mastermind council: seven archetypes, each with its own
retrieval-backed mind, built from the source material of how that person thinks.**

> **Status: Reference (template).** Scaffolded April 2026; last meaningful update
> 2026-08-16 (local-model provider support and tests). Usable as a template;
> not under active development.

## Why a council

A single model converges on the median answer. Hard decisions sit in the
tension between competing truths: growth vs stability, speed vs thoroughness,
right vs survivable. Conclave asks seven perspectives that see differently,
then synthesizes where they agree and where they split.

**Tension is the point.** If all seven agree, the question was probably too easy.

| Seat | Archetype | Lens |
| --- | --- | --- |
| Arnold Schwarzenegger | The Relentless Builder | Discipline, vision, no Plan B |
| Steve Jobs | The Taste-Maker | Product intuition, simplicity |
| Warren Buffett | The Compounder | Long-term value, margin of safety |
| Nelson Mandela | The Moral Strategist | Justice, patience, reconciliation |
| Demis Hassabis | The Systems Thinker | First principles, intelligence as leverage |
| Sun Tzu | The Terrain Reader | Positioning, timing, asymmetric advantage |
| Jeff Bezos | The Scale Architect | Customer obsession, one-way vs two-way doors |

## How it works

Each seat has a persona, a decision framework, a public bibliography, and a
local-only corpus that is chunked and embedded into a per-persona Chroma store.

`convene.py`:

1. takes your situation as input,
2. retrieves context from each persona's store,
3. runs each persona's framework against the problem,
4. collects seven responses,
5. synthesizes a **Council Verdict**: consensus, key disagreements, actions.

See [ARCHITECTURE.md](ARCHITECTURE.md).

## Layout

```txt
council/<persona>/persona.md             archetype, voice, lens
council/<persona>/decision-framework.md  how this persona reasons
council/<persona>/sources.md             bibliography (public)
council/<persona>/corpus/                source material (local only, gitignored)
prompts/convene.md, single-voice.md, synthesis.md
scripts/ingest.py     chunk + embed a persona's corpus
scripts/query.py      ask one persona
scripts/convene.py    run the full council
scripts/llm.py        provider selection (Ollama or Anthropic)
tests/test_llm.py     provider adapter tests (no network)
examples/127-days.md  a worked council session
sessions/             timestamped session output
BUILD_YOUR_OWN.md     guide to building your own council
```

## Run

```sh
git clone https://github.com/benikigai/conclave.git
cd conclave
pip install -r requirements.txt

# Local model via Ollama (default provider)
export CONCLAVE_OLLAMA_URL=http://localhost:11434
# optional: export CONCLAVE_MODEL=<ollama model tag>

# Add source material under council/<persona>/corpus/, then:
python scripts/ingest.py --persona warren-buffett
python scripts/query.py --persona sun-tzu --question "I have 127 days to build something meaningful. How do I spend them?"
python scripts/convene.py --question "Should I leave my job to start a company?"

# Cloud fallback
export CONCLAVE_PROVIDER=anthropic
export ANTHROPIC_API_KEY=...   # from your secret manager
python scripts/convene.py --question "..."

python -m unittest discover -s tests
```

## Config and secrets

| Variable | Purpose |
| --- | --- |
| `CONCLAVE_PROVIDER` | `ollama` (default) or `anthropic` |
| `CONCLAVE_OLLAMA_URL` | Ollama base URL |
| `CONCLAVE_MODEL` | Override the provider's default model |
| `ANTHROPIC_API_KEY` | Only for the Anthropic provider |

`.env` files, corpora, and vector stores are gitignored.

## Build your own

The method is the product, not the data. See [BUILD_YOUR_OWN.md](BUILD_YOUR_OWN.md).
Choosing archetypes, sourcing their material, and writing their decision
frameworks is itself the exercise.

## Maintenance notes

- `scripts/llm.py` currently defaults `CONCLAVE_OLLAMA_URL` to a private
  network address. Change the default to `http://localhost:11434` (the code
  default, not just the docs).
- `requirements.txt` lists `anthropic` unconditionally; it is only needed for the
  cloud provider.
- Never commit corpus files; cite sources ethically.

## License

MIT. See [LICENSE](LICENSE).
