---
name: llm-wiki
description: >-
  Build and maintain a Karpathy-style LLM knowledge base — a self-compiling
  Markdown wiki where an Agent ingests raw sources, compiles cross-linked
  concept/entity/summary pages, answers queries against the corpus, lints the
  graph for health, and audits in-context human feedback filed from the local
  web viewer. Use when (1) scaffolding a new knowledge base for any research
  topic, (2) ingesting articles/papers/PDFs/web pages into raw/, (3) compiling
  or restructuring wiki articles from existing raw material, (4) answering
  questions against the wiki and filing durable answers back, (5) running lint
  passes for dead links / orphan pages / coverage gaps / audit shape, (6)
  processing human feedback from the audit/ directory and applying corrections.
  Not for general note-taking or daily journals.
---

# LLM Wiki — Karpathy Knowledge Base Pattern

> **Experimental skill — iterating.**
> Authored by lym <973007435@qq.com> · [GitHub](https://github.com/kaerf15) · Inspired by [Karpathy's llm-wiki Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

## Core idea

Instead of RAG (re-retrieving raw docs on every query), the LLM **compiles** raw sources into a persistent, cross-linked wiki. Every ingest, query, lint, and audit pass makes the wiki richer. Knowledge compounds — and the human stays in the loop via a structured feedback channel instead of ad-hoc corrections that get lost.

- **You** own: sourcing raw material, asking good questions, steering direction, filing feedback on anything the AI got wrong.
- **LLM** owns: all writing, cross-referencing, filing, bookkeeping, and acting on your feedback.

The wiki is a living artifact with **five operations** — `compile`, `ingest`, `query`, `lint`, `audit`. Every session starts by reading `AGENTS.md` and `wiki/index.md`.

## Directory layout

```
<wiki-root>/
├── AGENTS.md          ← Schema: scope, conventions, current articles, gaps
├── CLAUDE.md          ← Compatibility pointer: @AGENTS.md
├── .agents/skills/llm-wiki/  ← This skill (installed by deploy)
├── log/               ← Per-day operation log (one file per day)
├── audit/             ← Human feedback inbox (one file per comment)
├── raw/               ← Immutable source documents (LLM reads, never writes)
├── wiki/              ← LLM-generated knowledge (LLM writes, you read)
└── outputs/queries/   ← Query answers (promote durable ones to wiki/)
```

`AGENTS.md` is the **schema file** — the single most important configuration. Read `references/schema-guide.md` for what to put in it. Read it at the start of every session. `CLAUDE.md` is generated as a one-line compatibility pointer (`@AGENTS.md`) for Claude Code users.

## Core principles

Four rules govern everything below. If a future instruction contradicts one, flag it to the user before acting.

### 1. Divide and conquer — flat structure

A single concept page should **never** try to cover a complex topic end-to-end. Target: **400–1200 words per page**. When a topic would blow past that:

- Prefer a **named hub file**: `wiki/concepts/<Topic>.md` with `title:` matching the concept name.
- Only if needed, add a **shallow** aspect folder: `wiki/concepts/<Topic>/<aspect>.md` (one extra level max).
- **Never** create `index.md` under subfolders — the **only** `index.md` is `wiki/index.md`.
- Keep paths shallow: `wiki/<category>/<file>.md` or `wiki/<category>/<topic>/<aspect>.md`. No deeper nesting.
- In `wiki/index.md`, list pages with indented bullets when a topic has aspect files.

On `compile`, flatten legacy layouts: rename `wiki/.../index.md` → `wiki/.../<Topic>.md` or `overview.md`, merge duplicates, and update links.

### 2. Mermaid for diagrams, KaTeX for formulas

- **Any flow, sequence, hierarchy, or state diagram** must be written in mermaid — never ASCII art.
- **Any formula** must be written in KaTeX: inline `$...$` or block `$$...$$`.

Both render in the web viewer (server-side KaTeX, client-side mermaid).

### 3. Raw file policy

Small text-based sources → copy into `raw/<subfolder>/`.

Document sources → convert with MarkItDown:

```bash
python3 -m pip install --user 'markitdown[all]'
python3 scripts/import_source.py <source-file> <wiki-root> --kind papers
```

Large binaries → create a pointer file at `raw/refs/<slug>.md` with `kind: ref` and `external_path`. Wiki pages cite it with a standard link: `[slug description](raw/refs/<slug>.md)`.

### 4. Audit is the human feedback surface

- Humans file feedback via the **web viewer** (select text → comment) or by writing `audit/*.md` manually.
- The AI **must** periodically run the `audit` op — never silently ignore open audits.
- When feedback is applied, move the file to `audit/resolved/` with a `# Resolution` section.

See `references/audit-guide.md` for the full format.

---

## Link format — standard Markdown

Use standard Markdown links with paths relative to the wiki root:

```markdown
[Transformers](wiki/concepts/Transformers.md)
[Brand Reconnaissance](wiki/concepts/Brand%20Reconnaissance.md)
[Andrej Karpathy](wiki/entities/Andrej%20Karpathy.md)
[source summary](wiki/summaries/karpathy-llm-wiki-gist.md)
[external ref](raw/refs/large-dataset.md)
```

Rules:
- Always use `wiki/...` paths for wiki pages (include `.md`). Do **not** link to subfolder `index.md`.
- Every page must have `title:` in frontmatter; the web graph and navigation use it as the display name.
- URL-encode spaces in paths (`%20`).
- Same-page sections: `[Section title](#section-heading)`.
- Link the first mention of every entity or concept; at most twice per article.

The web viewer renders display text only (hides paths), resolves dead links, shows **backlinks**, and provides a knowledge graph.

---

## The five operations

Every action on the wiki is one of these five. Each appends an entry to `log/YYYYMMDD.md`.

### 1. `compile`

(Re)structure wiki content from existing `raw/` material.

**Steps**: read schema + index → split oversized pages → flatten nested `index.md` → merge duplicates → rebuild `wiki/index.md` → log.

### 2. `ingest`

Add a new source. **One source typically touches 5–15 wiki pages.**

**Steps**: save to `raw/` → read source → create summary → create/update concept & entity pages → update `index.md` → log.

### 3. `query`

Answer a question **grounded in the wiki**.

**Steps**: scan `index.md` → read relevant pages → follow one level of outbound links → synthesize with inline citations like `[Concept Name](wiki/concepts/Concept.md)` → save to `outputs/queries/` → promote durable answers → log.

### 4. `lint`

```bash
python3 scripts/lint_wiki.py <wiki-root>
```

Reports: dead links, orphan pages, missing index entries, frequently-linked missing pages, log/audit shape issues.

### 5. `audit`

Process human feedback from `audit/`. See `references/audit-guide.md` and `SKILL.md` audit section in prior docs for resolution workflow.

---

## Tooling

| Tool | Purpose |
|------|---------|
| **`web/`** | Local preview — mermaid, KaTeX, backlinks, graph, feedback → `audit/` |
| `scripts/scaffold.py` | Bootstrap a new wiki directory tree |
| `scripts/lint_wiki.py` | Seven-pass health check |
| `scripts/audit_review.py` | Group open/resolved audits by target file |
| [qmd](https://github.com/tobi/qmd) | Optional local semantic search (>100 pages) |

## Starting a new wiki

```bash
python3 scripts/scaffold.py <wiki-root> "<Topic Title>"
```

Install skill to `<wiki-root>/.agents/skills/llm-wiki/` (see project README for deploy prompt).

## `wiki/index.md` format

```markdown
# Index — <Topic>

> One-sentence scope.

## 🔖 Navigation
- [Concepts](#concepts) · [Entities](#entities) · [Summaries](#summaries)

## Concepts
- [Foo](wiki/concepts/Foo.md) — one-line summary
- [Bar](wiki/concepts/Bar.md) — hub page
    - [aspect-1](wiki/concepts/Bar/aspect-1.md) — ...

## Entities
- [Andrej Karpathy](wiki/entities/Andrej%20Karpathy.md) — AI researcher

## Summaries (chronological)
- 2026-04-09 — [llm-wiki-gist](wiki/summaries/llm-wiki-gist.md) — Karpathy's Gist

## Open Questions
- Q1: ...
```

## References

- `references/schema-guide.md` — What to put in `AGENTS.md`
- `references/article-guide.md` — How to write wiki articles
- `references/log-guide.md` — The `log/` folder convention
- `references/audit-guide.md` — Audit file format and workflow
- `references/tooling-tips.md` — Web viewer, qmd, deployment
