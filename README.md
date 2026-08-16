# Conclave

**A personal AI mastermind council — seven archetypes, each with its own mind, trained on the source material of how that person actually thinks.**

---

## Why a Council Instead of Just Asking One Model

Here's the thing about asking a single AI for advice: you get one voice. It's articulate, it's helpful, and it converges on the median answer fast. But the median answer is rarely the right one for hard decisions.

Hard decisions live in the tension between competing truths. Growth vs. stability. Speed vs. thoroughness. What's right vs. what's survivable. No single perspective can hold all of that at once.

So I built a council.

Seven archetypes — not chosen because they're famous, but because each one *sees differently*. Arnold sees through the lens of relentless physical and mental discipline. Buffett sees compounding and erosion. Mandela sees systems of power and the long moral arc. Sun Tzu sees terrain and timing. Jobs sees the gap between what exists and what should exist. Hassabis sees intelligence itself as a lever. Bezos sees scale and irreversible vs. reversible doors.

When I bring a real problem to the council, I don't get agreement. I get seven genuinely different responses, shaped by different source material, different reasoning patterns, different definitions of what "winning" means. The synthesis that comes out the other side is sharper than anything I'd get from a single prompt.

**Tension is the point.** If all seven agree, you probably asked a boring question.

## The Council

| Seat | Archetype | Lens |
|------|-----------|------|
| Arnold Schwarzenegger | The Relentless Builder | Discipline, vision, immigrant hunger, the refusal to have a Plan B |
| Steve Jobs | The Taste-Maker | Product intuition, simplicity as sophistication, reality distortion |
| Warren Buffett | The Compounder | Long-term value, margin of safety, what erodes vs. what compounds |
| Nelson Mandela | The Moral Strategist | Justice, patience, reconciliation, leading through suffering |
| Demis Hassabis | The Systems Thinker | First principles, intelligence amplification, interdisciplinary synthesis |
| Sun Tzu | The Terrain Reader | Positioning, timing, winning without fighting, asymmetric advantage |
| Jeff Bezos | The Scale Architect | Customer obsession, reversible vs. irreversible, Day 1 thinking |

## How It Works

Each council member has:
- A **persona** defining their archetype, strengths, weaknesses, and voice
- A **decision framework** — the step-by-step way they evaluate problems
- A **source bibliography** — the books, speeches, letters, and interviews that trained their perspective
- A **corpus** (local only, never committed) — the actual source material, chunked and embedded into a per-persona vector store

When you convene the council, an orchestrator:
1. Takes your situation as input
2. Retrieves relevant context from each persona's vector store
3. Runs each persona's decision framework against your problem with their retrieved context
4. Collects all seven responses
5. Synthesizes a **Council Verdict** — consensus points, key disagreements, and recommended actions

See [ARCHITECTURE.md](ARCHITECTURE.md) for the technical details.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/benikigai/conclave.git
cd conclave

# Install dependencies
pip install -r requirements.txt

# The checked-in default uses Qwen3.8-27B on the Studio B Ollama endpoint.
# Override the URL for another Ollama host.
export CONCLAVE_OLLAMA_URL=http://localhost:11434

# Add your source material to council/<persona>/corpus/
# Then ingest it
python scripts/ingest.py --persona warren-buffett

# Ask a single council member
python scripts/query.py --persona sun-tzu --question "I have 127 days to build something meaningful. How do I spend them?"

# Convene the full council
python scripts/convene.py --question "Should I leave my job to start a company?"

# Anthropic remains available as an explicit cloud fallback.
export CONCLAVE_PROVIDER=anthropic
export ANTHROPIC_API_KEY=...
python scripts/convene.py --question "Should I leave my job to start a company?"
```

Run the provider adapter regression tests without making model or cloud calls:

```bash
python -m unittest discover -s tests
```

## Build Your Own

The method is the product, not the data. This repo gives you the scaffolding to build your own council of advisors — with whatever archetypes matter to *your* decisions.

See [BUILD_YOUR_OWN.md](BUILD_YOUR_OWN.md) for the full guide.

## Repository Structure

```
conclave/
├── README.md
├── ARCHITECTURE.md           # RAG architecture and orchestration design
├── BUILD_YOUR_OWN.md         # Step-by-step guide to build your own council
├── council/
│   ├── arnold-schwarzenegger/
│   ├── steve-jobs/
│   ├── warren-buffett/
│   ├── nelson-mandela/
│   ├── demis-hassabis/
│   ├── sun-tzu/
│   └── jeff-bezos/
│       ├── persona.md            # Archetype, voice, lens
│       ├── decision-framework.md # How this persona reasons
│       ├── sources.md            # Bibliography (public)
│       └── corpus/               # Source material (local only, .gitignored)
├── prompts/
│   ├── convene.md            # Full council orchestration prompt
│   ├── single-voice.md       # Single persona consultation prompt
│   └── synthesis.md          # Council verdict synthesis prompt
├── examples/
│   └── 127-days.md           # A real example of the council in action
├── sessions/                 # Timestamped council session artifacts
└── scripts/
    ├── ingest.py             # Chunk and embed source material
    ├── query.py              # Query a single persona
    └── convene.py            # Orchestrate the full council
```

## Philosophy

This isn't a chatbot wrapper. It's a thinking tool.

The best decisions I've made came from holding multiple conflicting perspectives simultaneously until a synthesis emerged that none of them would have reached alone. The council automates the hardest part of that — genuinely inhabiting a perspective that isn't yours.

If you build your own, you'll notice something: the process of choosing your archetypes, sourcing their material, and writing their decision frameworks teaches you more about how you think than any amount of journaling. The council is a mirror with seven faces.

## License

MIT. See [LICENSE](LICENSE).

The method and code are open. The source material in your corpus is your responsibility — cite ethically, never commit copyrighted files.
