# Build Your Own Council

This guide walks you through creating your own AI mastermind council from scratch. You don't need to use the same archetypes — the power is in choosing advisors whose perspectives create productive tension with each other and with your own defaults.

## Step 1: Choose Your Archetypes

Start with a question: **What perspectives am I missing when I make decisions alone?**

Good council members aren't just people you admire. They're people who would *disagree with each other* in useful ways. You want:

- At least one **operator** (someone who builds and ships things)
- At least one **strategist** (someone who thinks in systems and positioning)
- At least one **moral voice** (someone who asks whether you *should*, not just whether you *can*)
- At least one **contrarian** (someone whose default reaction is to question the premise)
- At least one person from a **domain you're weak in**

### The Litmus Test

For each candidate, ask: "If I described my current biggest problem to this person, would their first question surprise me?" If yes, they belong on the council. If you can already predict what they'd say, they're not adding a new lens.

### Sizing

Seven is not magic. Start with three if that's what you can source well. A council of three deeply-researched perspectives beats seven shallow ones. You can always add seats later.

## Step 2: Source Material (Ethically)

For each council member, you need primary source material — the things they actually said, wrote, or were quoted saying in context. Not summaries. Not "in the style of." The actual thinking.

### Where to Find It

| Source Type | Where to Look | Notes |
|-------------|---------------|-------|
| Books (authored) | Library, purchase | Best single source for most figures |
| Biographies | Library, purchase | Good for decision context, but filter for the subject's own words |
| Interviews | YouTube transcripts, podcast transcripts | Rich, unscripted thinking |
| Speeches | University archives, YouTube | Good for values and priorities |
| Letters | Published collections, annual reports | Buffett's shareholder letters are the gold standard |
| Articles | Personal blogs, published essays | Direct access to thinking process |

### Ethics

- **Never commit copyrighted material to a public repo.** Your `corpus/` folders are .gitignored for this reason.
- **Cite everything in `sources.md`.** The bibliography is public. The files are private.
- **Prefer primary sources over secondary.** A biography's interpretation is not the same as the subject's own words.
- **Living people**: Be thoughtful. You're building a reasoning model, not a deepfake. The persona should serve your decision-making, not impersonate someone.

## Step 3: Build the Persona File

For each council member, create `persona.md` with these sections:

```markdown
# [Name]

## Archetype
One line. What role do they play on your council?

## Strength
What kind of problem are they best at? When should you listen to them most?

## Weakness
What are they blind to? When should you discount their advice?

## Lens
In one sentence: how do they see the world? What's the filter everything passes through?

## Voice Notes
How do they talk? Short sentences or long? Metaphors or directness? Formal or casual?
Include specific verbal patterns, favorite phrases, rhetorical habits.

## Sample Phrases
5-10 things they'd actually say, drawn from source material.
These anchor the LLM's voice calibration.
```

The **Weakness** section is the most important. If your persona has no blind spots, it's not a real perspective — it's a flattering caricature.

## Step 4: Write the Decision Framework

This is the step-by-step reasoning pattern the persona uses when evaluating a problem. It's the most labor-intensive part and the most valuable.

Study your source material for patterns. How does this person approach a new problem? What do they ask first? What do they check? Where do they start, and where do they end?

Example structure:

```markdown
# [Name] — Decision Framework

## Step 1: [First thing they do]
Description of this step. What question do they ask? What are they looking for?

## Step 2: [Second thing they do]
...

## Step 3: [Third thing they do]
...

## Final Check
The question they ask themselves before committing to an answer.
```

Tips:
- **Be specific.** "Think carefully" is useless. "Ask what the second-order consequences are in 10 years" is a real step.
- **Draw from real decisions.** Find examples of them reasoning through a choice and reverse-engineer the pattern.
- **Include failure modes.** If you know when this framework fails, note it. The LLM can use that self-awareness.

## Step 5: Curate and Cite Sources

Create `sources.md` with a structured bibliography. Organize by source type. Include enough detail that someone else could find and verify each source.

You don't need hundreds of sources. The Pareto principle applies:
- 2-3 books will give you 80% of the thinking
- 5-10 interviews will give you the voice
- The rest is refinement

## Step 6: Chunk and Embed

Once your source material is in `council/<persona>/corpus/`, run the ingest script:

```bash
# Ingest one persona
python scripts/ingest.py --persona your-persona-name

# Ingest all personas
python scripts/ingest.py --all
```

### Before You Ingest

1. **Clean your source files.** Remove headers, footers, page numbers, table of contents — anything that's navigation, not content.
2. **Use plain text or markdown.** The chunker handles `.txt` and `.md` files. Convert PDFs first.
3. **Name files descriptively.** `buffett-shareholder-letter-2005.txt` > `doc_17.txt`. The filename becomes metadata.

### Verify Your Embeddings

After ingesting, test retrieval:

```bash
python scripts/query.py --persona your-persona-name --question "What matters most when making a big decision?"
```

If the retrieved chunks feel off-topic, your chunking might be too small (losing context) or too large (diluting relevance). Adjust in `scripts/ingest.py`.

## Step 7: Test a Single Voice

Before convening the full council, test individual personas:

```bash
python scripts/query.py --persona sun-tzu --question "My competitor just raised $50M. What should I do?"
```

Ask yourself:
- Does the response sound like this person, or like generic AI advice?
- Does it reference concepts from the source material?
- Does it follow the decision framework's steps?

If not, iterate on the persona file and decision framework. The quality of these two files matters more than the quantity of source material.

## Step 8: Convene

Run your first full council session:

```bash
python scripts/convene.py --question "Your actual hard question here"
```

Read every response. Then read the synthesis. Ask:
- Did any persona surprise you?
- Where did they disagree, and was the disagreement illuminating?
- Did the synthesis capture the real tensions, or did it paper over them?

The best council questions are ones where you genuinely don't know the answer and where reasonable people would disagree.

## Step 9: Iterate

Your council is a living system. As you use it:

- **Refine personas** when responses feel off-voice
- **Update decision frameworks** when you discover reasoning patterns you missed
- **Add source material** as you find new interviews, letters, speeches
- **Add or remove seats** as your decision needs evolve
- **Save session artifacts** to `sessions/` — your decision journal accumulates over time

The council gets better the more you use it, because *you* get better at asking questions it can illuminate.
