# Lokalni Clef-Flash / Local Clef-Flash

> Bez downloada bez odobrenja. / No downloads without approval.

1. Model: `Cloudflare/clef-flash` (Apache-2.0), 9B BF16, treba ~18 GB RAM-a.
   Preuzimanje: `huggingface_hub snapshot_download("Cloudflare/clef-flash")`.
2. Runtime opcije: SGLang (`sglang:dev-clef`, služi `/v1/systemone`, treba GPU za
   smislenu latenciju), Transformers (`joint_schema_model.systemone`, `trust_remote_code`,
   radi na CPU ali sporo — izmjeriti prije odluke), vLLM / Docker Model Runner.
3. Ovaj server (12 CPU, 47 GB RAM, bez GPU): izvodljivo za pilot, očekivana CPU
   latencija reda sekundi–desetina sekundi — potvrditi mjerenjem (DI Faza 7).
4. Pokrenuti server na `127.0.0.1:30000`, u `decision.json` postaviti
   `primary/…clef_local…clefLocalUrl`. Health: `decision_status`.
5. Kvantizacije (63 community): chat-style, NISU SystemOne — ne koristiti kao zamjenu.
