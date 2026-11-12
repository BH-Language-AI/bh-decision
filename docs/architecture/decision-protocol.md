# Decision protokol v1 (zajednički / common)

Interni zahtjev: `{state:{task, language?, available_tools?, context?}, questions:{id:{type, instructions?, options?}}}`.
Tipovi: `categorical` (2–64 opcije) → SystemOne `choice`; `boolean` → `noul`;
`score` (2–16 nivoa) → `score`. ID 1–100 znakova `[A-Za-z0-9_.-]`, 1–64 pitanja,
`task` ≤ 8000 znakova, bez `images/videos`.

Interni odgovor: `{decision_id, provider, model, model_version?, decisions:{id:{selected, probabilities, confidence?}}, confidence, latency_ms, fallback_used, requires_escalation, abstained[], usage?, timestamp}`.
`confidence` = minimum max-vjerojatnosti; `requires_escalation` kad je ispod
`escalation` praga ili ima apstinencija. Vjerojatnost ≠ kalibrirano povjerenje.
Apstinencija kad max prob < `abstain` praga. Bez chain-of-thought.

AnyJev mapiranje: `choice`→`choice` (≤26 opcija), `boolean`→`yes_no`, `score`→`score`
sa levels kao options (selected = argmax indeks). Odgovor nosi `route` (`one_forward`/`cot`)
i `level` u `usage`. Nepoznat oblik odgovora → `invalid_response`, nikad nagađanje.
