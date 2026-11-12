// Opcionalni live test — preskače se bez OPENCODE_API_KEY. Nikad se ne izvršava u CI.
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { DecisionCore } from "../../packages/decision-core/src/core.ts";
import { ProviderRegistry } from "../../packages/decision-core/src/providers.ts";
import { loadConfig, registryOptsFromEnv } from "../../packages/decision-core/src/config.ts";

const KEY = process.env.OPENCODE_API_KEY;

describe("live jev (samo uz korisnički ključ)", { skip: !KEY }, () => {
  it("jev-1.13-free vraća strukturiran odgovor", async () => {
    const cfg = loadConfig({ primary: "jev", fallback: [] });
    const core = new DecisionCore(new ProviderRegistry(registryOptsFromEnv(cfg, process.env)), cfg);
    const r = await core.decide({
      state: { task: "Korisnik pita gdje produžiti ličnu kartu.", language: "bs-ijekavica" },
      questions: { intent: { id: "intent", type: "categorical",
        options: { admin: "Administrativni postupak.", tech: "Tehnički problem." } } },
    }, "live-smoke");
    assert.equal(r.provider, "jev");
    assert.equal(r.model, "jev-1.13-free");
    assert.ok(r.confidence >= 0 && r.confidence <= 1);
  });
});
