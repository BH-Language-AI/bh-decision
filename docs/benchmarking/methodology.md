# Metodologija benchmarka / Benchmark methodology

1. Paket: `decision_benchmark` MCP alat čita `datasets/samples/*.jsonl`
   (human-reference `decision`), svaki primjer → jedna `categorical` odluka.
2. Metrike: accuracy vs referenca, apstinencije, latencija (p50/max), provider,
   fallbackovi, dostupnost. Ništa se ne tvrdi bez brojeva iz pokretanja.
3. Mock smoke (ovdje): deterministički provider, mjeri samo harness, ne provider.
4. Live poredba A/B/C/D: isti scenariji + isti `session_id` prefiks, jednom bez DI
   (direktan glavni LLM), jednom sa svakim providerom; porede se trajanje zadatka,
   glavni-LLM tokeni, broj alata, pogrešni izbori. Potrebni ključevi/infra + odobrenje.
5. Izvještaji idu u `benchmarks/reports/`, nikad fabricirani.
