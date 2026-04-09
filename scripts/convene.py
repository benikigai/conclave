#!/usr/bin/env python3
"""
Convene the full Council of Seven.

Queries all seven personas in parallel, then runs the synthesis prompt
to produce a Council Verdict.

Usage:
    python scripts/convene.py --question "Should I leave my job to start a company?"
    python scripts/convene.py -q "How should I spend the next 90 days?" --save
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import anthropic
import click
from rich.console import Console
from rich.markdown import Markdown

# Import from sibling module
sys.path.insert(0, str(Path(__file__).resolve().parent))
from query import get_persona_names, load_persona, retrieve_context, build_system_prompt

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = PROJECT_ROOT / "sessions"
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_TOP_K = 5

console = Console()


# ---------------------------------------------------------------------------
# Async persona queries
# ---------------------------------------------------------------------------

async def query_persona_async(
    client: anthropic.AsyncAnthropic,
    persona: str,
    question: str,
    top_k: int,
    model: str,
) -> tuple[str, str]:
    """Query a single persona asynchronously. Returns (persona_name, response_text)."""
    persona_content = load_persona(persona)
    retrieved_chunks = retrieve_context(persona, question, top_k=top_k)
    system_prompt = build_system_prompt(persona_content, retrieved_chunks)

    response = await client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": question}],
    )

    return persona, response.content[0].text


async def query_all_personas(
    question: str,
    top_k: int = DEFAULT_TOP_K,
    model: str = DEFAULT_MODEL,
) -> dict[str, str]:
    """Query all personas in parallel."""
    client = anthropic.AsyncAnthropic()
    personas = get_persona_names()

    tasks = [
        query_persona_async(client, p, question, top_k, model) for p in personas
    ]

    results = await asyncio.gather(*tasks)
    return dict(results)


# ---------------------------------------------------------------------------
# Synthesis
# ---------------------------------------------------------------------------

def synthesize(
    question: str,
    responses: dict[str, str],
    model: str = DEFAULT_MODEL,
) -> str:
    """Run the synthesis prompt over all persona responses."""
    system_prompt = (
        "You are the Council Synthesizer. Your role is not to add a new perspective "
        "— it is to find the signal in the seven perspectives you've been given.\n\n"
        "Rules:\n"
        "- Do not average the perspectives. Averaging destroys the signal.\n"
        "- Do not introduce new opinions. You are a synthesizer, not an eighth advisor.\n"
        "- Weight perspectives by relevance, not by confidence of tone.\n"
        "- Name names. Say 'Buffett and Mandela both see...' not 'several advisors noted...'\n"
        "- If the council is genuinely split, say so.\n\n"
        "Structure your response as:\n"
        "### Consensus\n"
        "### Key Disagreements\n"
        "### Recommended Actions\n"
        "### Strongest Dissent\n"
        "### The Question Behind the Question\n"
    )

    user_content = f"QUESTION: {question}\n\n"
    for persona, response in responses.items():
        display_name = persona.replace("-", " ").title()
        user_content += f"---\n\n{display_name.upper()}:\n{response}\n\n"
    user_content += "---\n\nSynthesize these into a Council Verdict."

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )

    return response.content[0].text


# ---------------------------------------------------------------------------
# Session saving
# ---------------------------------------------------------------------------

def save_session(
    question: str,
    responses: dict[str, str],
    synthesis: str,
) -> Path:
    """Save a council session as a timestamped markdown file."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate filename from date and question
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = question[:50].lower()
    slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
    slug = slug.strip().replace(" ", "-")
    filename = f"{date_str}-{slug}.md"
    filepath = SESSIONS_DIR / filename

    lines = []
    lines.append(f"# Council Session: {date_str}\n")
    lines.append(f"## Question\n\n{question}\n")
    lines.append("---\n")

    for persona, response in responses.items():
        display_name = persona.replace("-", " ").title()
        lines.append(f"\n## {display_name}\n\n{response}\n")
        lines.append("---\n")

    lines.append(f"\n## Council Synthesis\n\n{synthesis}\n")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.command()
@click.option(
    "--question",
    "-q",
    type=str,
    required=True,
    help="Your question or situation for the council.",
)
@click.option(
    "--top-k",
    type=int,
    default=DEFAULT_TOP_K,
    show_default=True,
    help="Number of chunks to retrieve per persona.",
)
@click.option(
    "--model",
    type=str,
    default=DEFAULT_MODEL,
    show_default=True,
    help="Claude model to use.",
)
@click.option(
    "--save",
    is_flag=True,
    help="Save the session to sessions/ as a timestamped markdown file.",
)
def main(question: str, top_k: int, model: str, save: bool):
    """Convene the full Council of Seven."""
    personas = get_persona_names()
    console.print(f"\n[bold]Convening the Council of Seven...[/bold]")
    console.print(f"  Querying: {', '.join(p.replace('-', ' ').title() for p in personas)}\n")

    # Query all personas in parallel
    responses = asyncio.run(query_all_personas(question, top_k=top_k, model=model))

    # Display individual responses
    for persona, response in responses.items():
        display_name = persona.replace("-", " ").title()
        console.print(Markdown(f"## {display_name}\n\n{response}\n\n---"))

    # Run synthesis
    console.print("\n[bold]Synthesizing Council Verdict...[/bold]\n")
    synthesis = synthesize(question, responses, model=model)
    console.print(Markdown(f"## Council Synthesis\n\n{synthesis}"))

    # Save session if requested
    if save:
        filepath = save_session(question, responses, synthesis)
        console.print(f"\n[dim]Session saved to {filepath}[/dim]")


if __name__ == "__main__":
    main()
