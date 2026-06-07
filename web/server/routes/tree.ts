import fs from "node:fs";
import path from "node:path";
import type { Request, Response } from "express";
import type { WikiRegistry } from "../config.js";
import { extractTitle } from "../links.js";
import { wikiOr400 } from "./helpers.js";

export interface TreeNode {
  name: string;
  path: string; // relative to wikiRoot
  kind: "file" | "dir";
  children?: TreeNode[];
}

/**
 * Build a navigation tree from the wiki/ directory.
 * The tree is recursive, sorted alphabetically, and only includes .md files.
 */
export function buildTree(wikiRoot: string): TreeNode {
  const wikiDir = path.join(wikiRoot, "wiki");
  if (!fs.existsSync(wikiDir)) {
    return { name: "wiki", path: "wiki", kind: "dir", children: [] };
  }
  return walk(wikiRoot, wikiDir, "wiki");
}

function walk(wikiRoot: string, dir: string, rel: string): TreeNode {
  const entries = fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((e) => !e.name.startsWith("."))
    .sort((a, b) => {
      if (a.isDirectory() !== b.isDirectory()) return a.isDirectory() ? -1 : 1;
      return a.name.localeCompare(b.name);
    });

  const children: TreeNode[] = [];
  for (const e of entries) {
    const full = path.join(dir, e.name);
    const nodeRel = path.posix.join(rel, e.name);
    if (e.isDirectory()) {
      children.push(walk(wikiRoot, full, nodeRel));
    } else if (e.name.endsWith(".md")) {
      const text = fs.readFileSync(full, "utf-8");
      const stem = e.name.replace(/\.md$/, "");
      const title = extractTitle(text) ?? stem;
      children.push({ name: title, path: nodeRel, kind: "file" });
    }
  }

  return { name: path.basename(dir), path: rel, kind: "dir", children };
}

export function handleTree(registry: WikiRegistry) {
  return (req: Request, res: Response) => {
    const wiki = wikiOr400(registry, req, res);
    if (!wiki) return;
    res.json(buildTree(wiki.path));
  };
}
