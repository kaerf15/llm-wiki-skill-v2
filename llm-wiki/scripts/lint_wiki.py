#!/usr/bin/env python3
"""
lint_wiki.py — Health check for an LLM Wiki.

Usage:
    python3 lint_wiki.py <wiki-root>

Example:
    python3 lint_wiki.py ~/wikis/ai-research

Checks:
  1. Dead links — [text](path.md) where the target doesn't exist
  2. Orphan pages — wiki pages with no inbound links
  3. Missing index entries — wiki pages not listed in wiki/index.md
  4. Nested index.md — only wiki/index.md is allowed
  5. Frequently-linked missing pages — linked 3+ times but no page
  6. log/ shape — every file matches YYYYMMDD.md and has the right H1
  7. audit/ shape — every audit/*.md parses as a valid AuditEntry
  8. Audit targets — every open audit's `target` file must exist

Exit codes:
  0 — no issues found
  1 — issues found (printed to stdout)
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote


MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
LOG_FILENAME_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})\.md$")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

AUDIT_REQUIRED_FIELDS = {
    "id", "target", "target_lines", "anchor_before", "anchor_text",
    "anchor_after", "severity", "author", "source", "created", "status",
}
VALID_SEVERITIES = {"info", "suggest", "warn", "error"}
VALID_STATUSES = {"open", "resolved"}
VALID_SOURCES = {"web-viewer", "manual"}


def load_pages(wiki_dir: Path) -> dict[str, Path]:
    """Map normalized wiki-relative paths and stems to file paths."""
    pages: dict[str, Path] = {}
    for p in wiki_dir.rglob("*.md"):
        rel = p.relative_to(wiki_dir).as_posix()
        pages[rel] = p
        pages[rel.removesuffix(".md")] = p
        pages[p.stem] = p
    return pages


def is_external_href(href: str) -> bool:
    return bool(re.match(r"^(https?:|mailto:|#)", href, re.I))


def resolve_link_href(root_path: Path, from_rel: str, href: str) -> str | None:
    """Return normalized path relative to wiki root, or None if not a wiki link."""
    href = unquote(href.strip())
    if not href or is_external_href(href):
        return None

    path_part = href.split("#", 1)[0]
    if not path_part:
        return None

    candidate = path_part.replace("\\", "/")
    if not candidate.endswith(".md"):
        candidate += ".md"

    from_path = root_path / from_rel
    if candidate.startswith("wiki/") or candidate.startswith("raw/"):
        full = root_path / candidate
    else:
        full = (from_path.parent / candidate).resolve()

    try:
        rel = full.relative_to(root_path.resolve()).as_posix()
    except ValueError:
        return None

    if rel.startswith(".."):
        return None
    return rel


def extract_md_links(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in MD_LINK_RE.finditer(text)]


def parse_frontmatter(text: str) -> dict | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    body = m.group(1)
    result: dict = {}
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        val = rest.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                result[key] = []
            else:
                parts = [p.strip() for p in inner.split(",")]
                parsed: list = []
                for p in parts:
                    if p.isdigit() or (p.startswith("-") and p[1:].isdigit()):
                        parsed.append(int(p))
                    else:
                        parsed.append(p.strip('"').strip("'"))
                result[key] = parsed
        elif val.startswith('"') and val.endswith('"'):
            result[key] = val[1:-1].replace("\\n", "\n").replace('\\"', '"')
        elif val.startswith("'") and val.endswith("'"):
            result[key] = val[1:-1]
        else:
            result[key] = val
        i += 1
    return result


def lint(root: str) -> int:
    root_path = Path(root)
    wiki_path = root_path / "wiki"
    log_path = root_path / "log"
    audit_path = root_path / "audit"

    if not wiki_path.exists():
        print(f"ERROR: wiki/ directory not found at {wiki_path}", file=sys.stderr)
        return 1

    pages = load_pages(wiki_path)
    all_wiki_files = list(wiki_path.rglob("*.md"))
    index_path = wiki_path / "index.md"

    issues = 0
    inbound: dict[str, list[str]] = defaultdict(list)

    # ── Pass 1: dead links ──────────────────────────────────────────────
    dead_links: list[tuple[str, str, str]] = []
    for md_file in root_path.rglob("*.md"):
        if "audit" in md_file.parts and md_file.parent.name in {"audit", "resolved"}:
            continue
        rel_from_root = md_file.relative_to(root_path).as_posix()
        text = md_file.read_text(encoding="utf-8")
        for _text, href in extract_md_links(text):
            resolved = resolve_link_href(root_path, rel_from_root, href)
            if not resolved:
                continue
            if not resolved.startswith("wiki/"):
                continue
            full = root_path / resolved
            wiki_rel = resolved.removeprefix("wiki/")
            if full.exists() and full.is_file():
                inbound[wiki_rel.removesuffix(".md")].append(rel_from_root)
                inbound[Path(wiki_rel).stem].append(rel_from_root)
            elif wiki_rel in pages or Path(wiki_rel).stem in pages:
                target = pages.get(wiki_rel) or pages.get(Path(wiki_rel).stem)
                if target:
                    inbound[target.stem].append(rel_from_root)
            else:
                dead_links.append((rel_from_root, _text or href, href))

    if dead_links:
        print(f"\n🔴 Dead links ({len(dead_links)}):")
        for source, label, href in dead_links:
            print(f"   {source} → [{label}]({href})")
        issues += len(dead_links)
    else:
        print("✅ No dead links")

    # ── Pass 2: orphan pages ────────────────────────────────────────────
    skip_orphan = {"index"}
    orphans = [
        p for p in all_wiki_files
        if p.stem not in inbound
        and p.stem not in skip_orphan
        and p != index_path
    ]
    if orphans:
        print(f"\n🟡 Orphan pages ({len(orphans)}) — no inbound links:")
        for p in orphans:
            print(f"   {p.relative_to(root_path)}")
        issues += len(orphans)
    else:
        print("✅ No orphan pages")

    # ── Pass 3: missing index entries ───────────────────────────────────
    if index_path.exists():
        index_text = index_path.read_text(encoding="utf-8")
        not_in_index = []
        for p in all_wiki_files:
            if p == index_path:
                continue
            rel = p.relative_to(wiki_path).as_posix()
            stem = p.stem
            if rel not in index_text and rel.removesuffix(".md") not in index_text and stem not in index_text:
                not_in_index.append(p)
        if not_in_index:
            print(f"\n🟡 Pages missing from index.md ({len(not_in_index)}):")
            for p in not_in_index:
                print(f"   {p.relative_to(root_path)}")
            issues += len(not_in_index)
        else:
            print("✅ All pages in index.md")
    else:
        print("⚠️  wiki/index.md not found — skipping index check")

    # ── Pass 4: nested index.md (only wiki/index.md allowed) ────────────
    nested_indexes = [p for p in all_wiki_files if p.name == "index.md" and p != index_path]
    if nested_indexes:
        print(f"\n🔴 Nested index.md files ({len(nested_indexes)}) — only wiki/index.md is allowed:")
        for p in nested_indexes:
            print(f"   {p.relative_to(root_path)}")
        issues += len(nested_indexes)
    else:
        print("✅ No nested index.md files")

    # ── Pass 5: frequently linked but missing ─────────────────────────────
    link_counts: dict[str, int] = defaultdict(int)
    for md_file in root_path.rglob("*.md"):
        rel_from_root = md_file.relative_to(root_path).as_posix()
        text = md_file.read_text(encoding="utf-8")
        for _text, href in extract_md_links(text):
            resolved = resolve_link_href(root_path, rel_from_root, href)
            if resolved and resolved.startswith("wiki/"):
                link_counts[resolved] += 1

    missing_pages = [
        (link, count) for link, count in link_counts.items()
        if count >= 3 and not (root_path / link).exists()
    ]
    if missing_pages:
        print(f"\n🟡 Frequently linked but no page ({len(missing_pages)}):")
        for link, count in sorted(missing_pages, key=lambda x: -x[1]):
            print(f"   [{link}]({link}) — mentioned {count}x")
        issues += len(missing_pages)
    else:
        print("✅ No frequently-linked missing pages")

    # ── Pass 6: log/ shape ───────────────────────────────────────────────
    if log_path.exists() and log_path.is_dir():
        log_issues: list[str] = []
        for p in sorted(log_path.iterdir()):
            if p.is_dir() or p.name == ".gitkeep":
                continue
            m = LOG_FILENAME_RE.match(p.name)
            if not m:
                log_issues.append(f"   {p.relative_to(root_path)} — filename doesn't match YYYYMMDD.md")
                continue
            y, mo, d = m.groups()
            iso = f"{y}-{mo}-{d}"
            first_line = p.read_text(encoding="utf-8").splitlines()[:1]
            if not first_line or first_line[0].strip() != f"# {iso}":
                log_issues.append(f"   {p.relative_to(root_path)} — expected H1 '# {iso}'")
        if log_issues:
            print(f"\n🟡 log/ shape issues ({len(log_issues)}):")
            for s in log_issues:
                print(s)
            issues += len(log_issues)
        else:
            print("✅ log/ shape OK")
    else:
        print("⚠️  log/ directory not found — skipping log shape check")

    # ── Pass 7: audit/ shape ─────────────────────────────────────────────
    audit_targets_to_check: list[tuple[str, str]] = []
    if audit_path.exists() and audit_path.is_dir():
        audit_files = [p for p in audit_path.rglob("*.md") if p.name != ".gitkeep"]
        audit_issues: list[str] = []
        for p in audit_files:
            text = p.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            rel = p.relative_to(root_path)
            if fm is None:
                audit_issues.append(f"   {rel} — missing YAML frontmatter")
                continue
            missing = AUDIT_REQUIRED_FIELDS - set(fm.keys())
            if missing:
                audit_issues.append(
                    f"   {rel} — missing fields: {', '.join(sorted(missing))}"
                )
                continue
            if fm["severity"] not in VALID_SEVERITIES:
                audit_issues.append(
                    f"   {rel} — invalid severity '{fm['severity']}'"
                )
            if fm["source"] not in VALID_SOURCES:
                audit_issues.append(f"   {rel} — invalid source '{fm['source']}'")
            expected_status = "resolved" if "resolved" in p.parts else "open"
            if fm["status"] != expected_status:
                audit_issues.append(
                    f"   {rel} — status '{fm['status']}' doesn't match directory"
                )
            if fm["status"] == "open":
                audit_targets_to_check.append((fm["id"], fm["target"]))

        if audit_issues:
            print(f"\n🔴 audit/ shape issues ({len(audit_issues)}):")
            for s in audit_issues:
                print(s)
            issues += len(audit_issues)
        else:
            print(f"✅ audit/ shape OK ({len(audit_files)} files)")
    else:
        print("⚠️  audit/ directory not found — skipping audit shape check")

    # ── Pass 8: audit targets exist ──────────────────────────────────────
    missing_targets: list[tuple[str, str]] = []
    for audit_id, target in audit_targets_to_check:
        target_path = root_path / target
        if not target_path.exists():
            alt = wiki_path / target
            if not alt.exists():
                missing_targets.append((audit_id, target))
    if missing_targets:
        print(f"\n🔴 Open audits with missing target files ({len(missing_targets)}):")
        for audit_id, target in missing_targets:
            print(f"   {audit_id} → {target}")
        issues += len(missing_targets)
    elif audit_targets_to_check:
        print("✅ All open-audit targets exist")

    print(f"\n{'─'*40}")
    if issues == 0:
        print("✅ Wiki is healthy — no issues found")
    else:
        print(f"⚠️  {issues} issue(s) found — review above and fix before next ingest")

    return 0 if issues == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(lint(sys.argv[1]))
