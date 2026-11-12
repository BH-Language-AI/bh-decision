// Faza 2: normalizacija + validacija. Mock odgovori u stvarnom SystemOne obliku.
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { toSystemOne, fromSystemOne, validateRequest } from "../../packages/decision-core/src/systemone.ts";
import { DecisionError } from "../../packages/decision-core/src/types.ts";

const REQ = {
  state: { task: "Koju alatku koristiti?", language: "bs-ijekavica", available_tools: ["read", "bash"] },
  questions: {
    task_type: { id: "task_type", type: "categorical" as const, options: { research: "Istraživanje.", coding: "Pisanje koda." } },
    needs_tool: { id: "needs_tool", type: "boolean" as const, instructions: "Treba li alat?" },
    complexity: { id: "complexity", type: "score" as const, options: ["low", "medium", "high"] },
  },
};

describe("toSystemOne", () => {
  it("mapira categorical->choice, boolean->noul, score->score", () => {
    const sys = toSystemOne(REQ, "jev-1.13-free");
    assert.equal(sys.model, "jev-1.13-free");
    assert.equal(sys.questions.task_type.type, "choice");
    assert.equal(sys.questions.needs_tool.type, "noul");
    assert.equal(sys.questions.complexity.type, "score");
  });
  it("ne šalje images/videos i odbija prazan task", () => {
    const sys = toSystemOne(REQ, "m");
    assert.ok(!("images" in sys) && !("videos" in sys));
    assert.throws(() => validateRequest({ state: { task: " " }, questions: {} }), (e: unknown) => (e as DecisionError).code === "invalid_request");
  });
  it("odbija nepoznat tip i previše pitanja", () => {
    assert.throws(() => toSystemOne({ state: { task: "t" }, questions: { x: { id: "x", type: "categorical" as never } } }, "m"));
    const many: Record<string, never> = {};
    for (let i = 0; i < 65; i++) many[`q${i}`] = { id: `q${i}`, type: "boolean" } as never;
    assert.throws(() => toSystemOne({ state: { task: "t" }, questions: many }, "m"));
  });
});

describe("fromSystemOne", () => {
  const RESP = {
    model: "jev-1.13-free",
    answers: {
      task_type: { choice: "coding", probabilities: { research: 0.15, coding: 0.85 }, confidence: 0.85 },
      needs_tool: { noul: 0.9 },
      complexity: { score: 1, probabilities: { low: 0.1, medium: 0.8, high: 0.1 }, legend: ["low", "medium", "high"] },
    },
  };
  it("normalizira Jev odgovor (slučaj 1: parsing)", () => {
    const { decisions, abstained } = fromSystemOne(REQ, RESP, 0.4);
    assert.equal(decisions.task_type.selected, "coding");
    assert.equal(decisions.needs_tool.selected, true);
    assert.equal(decisions.complexity.selected, 1);
    assert.deepEqual(abstained, []);
  });
  it("isti builder vrijedi za Clef (slučaj 2)", () => {
    const sys = toSystemOne(REQ, "Cloudflare/clef-flash");
    assert.equal(sys.model, "Cloudflare/clef-flash");
    assert.equal(sys.questions.task_type.type, "choice");
  });
  it("odbija zbroj != 1 (slučaj 10) i nepoznat choice", () => {
    assert.throws(() => fromSystemOne(REQ, { answers: { ...RESP.answers, task_type: { choice: "coding", probabilities: { research: 0.5, coding: 0.9 } } } }, 0.4),
      (e: unknown) => (e as DecisionError).code === "invalid_response");
    assert.throws(() => fromSystemOne(REQ, { answers: { ...RESP.answers, task_type: { choice: "nope", probabilities: { research: 0.5, coding: 0.5 } } } }, 0.4));
  });
  it("apstinira kad je max prob ispod praga (slučaj 11)", () => {
    const low = { answers: { ...RESP.answers, needs_tool: { noul: 0.45 } } };
    const { abstained, decisions } = fromSystemOne(REQ, low, 0.6);
    assert.deepEqual(abstained, ["needs_tool"]);
    assert.equal(decisions.needs_tool.selected, false);
  });
  it("odbija odgovor bez answers (slučaj 9)", () => {
    assert.throws(() => fromSystemOne(REQ, {}, 0.4), (e: unknown) => (e as DecisionError).code === "invalid_response");
  });
});
