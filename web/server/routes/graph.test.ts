import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { buildGraph } from "./graph.js";

test("uses frontmatter titles as graph node labels", () => {
  const wikiRoot = fs.mkdtempSync(path.join(os.tmpdir(), "llm-wiki-graph-"));
  fs.mkdirSync(path.join(wikiRoot, "wiki/concepts/Brand System"), { recursive: true });
  fs.mkdirSync(path.join(wikiRoot, "wiki/entities"), { recursive: true });

  fs.writeFileSync(
    path.join(wikiRoot, "wiki/index.md"),
    "---\ntitle: Index — Demo\n---\n# Index — Demo\n",
  );
  fs.writeFileSync(
    path.join(wikiRoot, "wiki/concepts/Growth Loop.md"),
    "---\ntitle: Growth Flywheel\n---\n# Growth Flywheel\n",
  );
  fs.writeFileSync(
    path.join(wikiRoot, "wiki/concepts/Brand System/overview.md"),
    "---\ntitle: Brand Strategy\n---\n# Brand Strategy\n",
  );
  fs.writeFileSync(
    path.join(wikiRoot, "wiki/entities/Andrej Karpathy.md"),
    "---\ntitle: Andrej Karpathy\n---\n# Researcher\n",
  );

  const graph = buildGraph(wikiRoot);
  const labelsByPath = new Map(graph.nodes.map((node) => [node.path, node.label]));

  assert.equal(graph.nodes.length, 4);
  assert.equal(labelsByPath.get("wiki/index.md"), "Index — Demo");
  assert.equal(labelsByPath.get("wiki/concepts/Growth Loop.md"), "Growth Flywheel");
  assert.equal(labelsByPath.get("wiki/concepts/Brand System/overview.md"), "Brand Strategy");
  assert.equal(labelsByPath.get("wiki/entities/Andrej Karpathy.md"), "Andrej Karpathy");
});
