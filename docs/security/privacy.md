# Privatnost i sigurnost / Privacy and security

- Tajne: samo env (`OPENCODE_API_KEY`, `CLOUDFLARE_*`); `.env.example` bez vrijednosti;
  `.gitignore` pokriva `.env`; test `bez tajni u kodu` skenira isporučeni kod.
- Jev Free: hosted, zatvorene težine, bez dokumentirane zero-retention politike za free
  tier → šalje se samo minimalni state (`task` + jezik + alati); repo i historija NIKAD
  (`send_repository_content: false`, default).
- Clef lokalno: podaci ne napuštaju server — strateški default za osjetljivo.
- Logovi: `log_prompts: false`; `redactSecrets()` za ključeve/tokene; bez punih promptova.
- Trošak: `allow_paid: false` + denylist na dva sloja; plaćeni endpointi (`jev-1.13`,
  Workers AI `@cf/cloudflare/clef-flash`) se nikad ne pozivaju automatski.
- Plugin: ne autorizira brisanje/rm/eskalaciju privilegija/kredencijale/deploy/objave/
  novac; OpenCode dozvole ostaju jedini autoritet (testirano mock ctx-om).
- Bez automatskog downloada modela i bez automatskog izvršavanja preporučenih komandi.
