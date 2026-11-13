// Integracija: raspored repozitorija, skill frontmatter, primjeri konfiguracije, bez tajni.
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFile, stat, readdir } from "node:fs/promises";
import { join } from "node:path";

const ROOT = "/home/sha/BH-Decision";

async function exists(p: string): Promise<boolean> {
  try { await stat(join(ROOT, p)); return true; } catch { return false; }
}

describe("project layout", () => {
  it("svi paketi, skill, config i docs postoje", async () => {
    for (const p of [
      "packages/decision-core/src/index.ts", "packages/decision-core/src/core.ts",
      "packages/decision-core/src/providers.ts", "packages/decision-core/src/systemone.ts",
      "packages/decision-core/src/config.ts",
      "packages/decision-mcp/src/index.ts", "packages/decision-mcp/src/tools.ts",
      "packages/opencode-plugin/src/index.ts",
      "skills/decision-intelligence/SKILL.md",
      "config/decision.example.yaml", "config/providers.example.yaml",
      "config/decision.basic.json", "config/decision.advanced.json",
      "docs/architecture/system-architecture.md", "docs/providers/jev.md",
      "docs/providers/clef-flash.md", "docs/decisions/provider-selection.md",
      "docs/installation/tiers.md",
      "scripts/anyjev_bridge.py", "scripts/anyjev_serve.sh",
      ".env.example", ".gitignore",
    ]) assert.ok(await exists(p), p);
  });
  it("tier presets su validan JSON s ocekivanim primaryjem", async () => {
    const basic = JSON.parse(await readFile(join(ROOT, "config/decision.basic.json"), "utf8"));
    const adv = JSON.parse(await readFile(join(ROOT, "config/decision.advanced.json"), "utf8"));
    assert.equal(basic.primary, "jev");
    assert.deepEqual(basic.fallback, []);
    assert.equal(adv.primary, "anyjev_local");
    assert.equal(adv.anyjev.model, "morriszjm/Tacit-4B");
    assert.equal(adv.anyjev.enabled, true);
  });
  it("skill ima valjan frontmatter", async () => {
    const md = await readFile(join(ROOT, "skills/decision-intelligence/SKILL.md"), "utf8");
    const m = md.match(/^---\nname: (\S+)\ndescription: (.+)\n---/);
    assert.ok(m, "frontmatter");
    assert.equal(m[1], "decision-intelligence");
    assert.ok(m[2].length > 20);
  });
  it("bez tajni u kodu i primjerima (slučaj 20)", async () => {
    const files: string[] = [];
    async function walk(d: string): Promise<void> {
      for (const e of await readdir(join(ROOT, d), { withFileTypes: true })) {
        if (e.name === "node_modules" || e.name.startsWith(".")) continue;
        const rel = `${d}/${e.name}`;
        if (e.isDirectory()) await walk(rel);
        else if (/\.(ts|json|yaml|md)$/.test(e.name)) files.push(rel);
      }
    }
    // Testovi sadrže sintetičke fixture i namjerno su izuzeti.
    await walk("packages"); await walk("skills"); await walk("config");
    const bad: string[] = [];
    for (const f of files) {
      const c = await readFile(join(ROOT, f), "utf8");
      if (/sk-(live|test)-[A-Za-z0-9]{8,}/.test(c) || /Bearer [A-Za-z0-9._-]{8,}/.test(c)) bad.push(f);
    }
    assert.deepEqual(bad, []);
  });
});
