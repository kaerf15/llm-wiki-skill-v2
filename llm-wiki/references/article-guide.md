# Wiki Article Writing Guide

Guidelines for writing high-quality wiki articles. Read before compiling a new concept or entity page.

## Length targets

| Page type | Target length | Notes |
|-----------|--------------|-------|
| Concept page | 400–1200 words | Dense, no padding. **Hard ceiling: 1200.** |
| Topic hub page (`<Topic>.md`) | 150–400 words | Definition + map of sub-pages |
| Aspect page under a topic folder | 400–1200 words | Covers one aspect |
| Entity page | 200–500 words | Factual, link-heavy |
| Summary page | 150–400 words | Takeaways, not a rewrite |

## Divide and conquer — when to split

If a concept page **would** exceed ~1200 words, split it:

1. Write the hub at `wiki/concepts/<Topic>.md` (`title:` = concept name).
2. If aspects are needed, create `wiki/concepts/<Topic>/<aspect>.md` (one folder level only).
3. Link aspects from the hub:
   ```markdown
   - [aspect-1](wiki/concepts/<Topic>/aspect-1.md) — one-line summary
   - [aspect-2](wiki/concepts/<Topic>/aspect-2.md) — one-line summary
   ```
4. Update `wiki/index.md` with indented bullets.
5. **Never** add `index.md` under subfolders — only `wiki/index.md` exists.

Signs a page needs splitting: word count >1000, many `##` sections, or wanting to link to a subsection — that subsection probably deserves its own page.

## Concept page structure

Use standard Markdown links in **Relationship to other concepts** and **Sources**:

```markdown
## Relationship to other concepts

- [Related Concept A](wiki/concepts/Related%20Concept%20A.md) — how they relate

## Sources

- [source-slug-1](wiki/summaries/source-slug-1.md) — (date) one-line description
```

See `schema-guide.md` for frontmatter fields.

## Link rules

1. **Link first mention** of every entity or concept.
2. **Link maximum twice per article** for the same target.
3. **Use wiki-root-relative paths**: `[Title](wiki/concepts/Title.md)`.
4. **Topic hub**: `[Topic](wiki/concepts/Foo.md)`.
5. **After writing a new page**, grep existing articles for the title and add incoming links (or rely on web viewer backlinks to find gaps).

## Diagrams — always mermaid

ASCII art is banned. Use mermaid for flows, sequences, hierarchies, states.

## Formulas — always KaTeX

Inline `$...$` or block `$$...$$`. The web viewer renders math server-side with KaTeX.

## Handling contradictions

State both claims, cite sources with links, add to Open Questions. Do not silently pick one.

## Incorporating audit feedback

Locate anchor → apply smallest fix → bump `updated:` → write resolution → move to `audit/resolved/` → log.
