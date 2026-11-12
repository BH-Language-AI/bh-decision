# Evropski foundation modeli — FAZA 1

Status: istraživački nacrt. Ispravka uobičajene greške: EuroLLM nema veze s UT Austin — razvija ga EU konzorcij (Unbabel, IST Lisabon, Edinburgh, Aveni, Paris-Saclay, Amsterdam, Naver Labs, Sorbonne; finansiranje EU UTTER 101070631; trening MareNostrum 5).
Datum: 2026-11-12.

## 1. Tabela

| Model | Porijeklo | Stvarni param. | Licenca | Komerc/FT/distil | bs/hr/sr dokaz | Kontekst |
|---|---|---|---|---|---|---|
| EuroLLM-1.7B | EU konzorcij (gore) | 1.657B | Apache 2.0 | Da/Da/Da | hr DA (kartica); bs NE | 4k |
| EuroLLM-9B | isti | 9.154B | Apache 2.0 | Da/Da/Da | hr DA; bs NE (transfer preko hr) | 4k |
| Salamandra-2B | BSC, Španija | 2B (klasa) | Apache 2.0 | Da/Da/Da | NEPOTVRĐENO (35 jezika, fokus ES) | 8k |
| Salamandra-7B | isti | 7.768B | Apache 2.0 | Da/Da/Da | NEPOTVRĐENO | 8k |
| Apertus-8B | Swiss AI (EPFL/ETH/CSCS) | 8B | Apache 2.0 | Da/Da/Da | 1000+ jezika implicitno, kvalitet NEPOTVRĐEN | 65k |
| TildeOpen-30b | Tilde, Latvija (LUMI) | 30.7B | CC-BY-4.0 | Da uz atribuciju | bs DA, hr DA, sr DA, cnr DA — eksplicitno | 8k |
| Teuken-7B-commercial | Fraunhofer IAIS | 7B | Apache 2.0 (samo `-commercial`) | Da | hr vjerovatno, bs NE | — |
| Ministral 3 (3B/8B/14B) | Mistral AI, FR | 3/8/14B | Apache 2.0 (serija 2025; oprez: 2024. serija bila MNPL) | Da | bs/hr bez dokaza | 128k |
| Pharia-1-7B | Aleph Alpha | 7B | Open Aleph — SAMO nekomercijalno | NE → ISKLJUČEN | DE/EN | — |
| Occiglot-7B | DFKI community | 7B | Apache 2.0 | Da | EN DE FR ES IT; bs/hr/sr NE | — |
| CroissantLLM-1.3B | CentraleSupélec | 1.3B | otvorena (detalj NEPOTVRĐEN) | — | EN–FR, bez bs vrijednosti | — |
| EuroBERT-2.1B | EuroLLM konzorcij | 2.1B | Apache 2.0 | Da | enkoder — nije baza za generativni 2B | — |

Izvori: https://huggingface.co/utter-project/EuroLLM-9B, https://huggingface.co/utter-project/EuroLLM-1.7B, https://huggingface.co/BSC-LT/salamandra-7b, https://huggingface.co/swiss-ai/Apertus-8B-Instruct-2509, https://huggingface.co/TildeAI/TildeOpen-30b, https://huggingface.co/openGPT-X/Teuken-7B-instruct-commercial-v0.4, https://arxiv.org/abs/2409.16235, https://arxiv.org/abs/2502.08489, https://arxiv.org/abs/2509.14233, https://arxiv.org/abs/2603.08182, https://eurollm.io, https://apertus-ai.org

## 2. Detalji bitni za odluku

- EuroLLM-1.7B/9B: dense Transformer (GQA, RoPE, SwiGLU), 4T tokena. 1.7B-Instruct tuče Gemma-2B i parira Gemma-7B u MT (FLORES-200/WMT). Slabost: kontekst samo 4k.
- Salamandra: decoder-only od nule, 12.9T tokena, NeMo, MareNostrum 5. Jedini pravi evropski 2B dekoder. Benchmarki fokusirani na španske jezike + engleski (npr. copa_es 86).
- Apertus: 15T tokena, xIELU, samo otvoreni/compliant podaci, EU AI Act dokumentacija. Apertus-8B avg 65.8 ≈ Llama-3.1-8B na engleskim zadacima. Rezerva ako zatreba 65k kontekst.
- TildeOpen-30b: GPT-NeoX fork, 2T tokena. Jedini s eksplicitnim bosanskim. Belebele avg 84.7%, MultiBLiMP sr-hr 99.6%, nacionalni ispiti hr 71.9% / sr 66.9%. Base-only, bez instructa → nije baza, idealan učitelj za distilaciju i generator ijekavskih podataka.
- 4B tier: NE POSTOJI evropska 4B baza (praznina 2B→7B). Ne izmišljati veličinu.

## 3. Okvirni hardver (bf16 / Q4 / LoRA / full FT)

| Veličina | bf16 inferencija | Q4 | LoRA FT | Full FT |
|---|---|---|---|---|
| ~2B | ~4–5 GB | ~1.5 GB | 1×24 GB | 1×40–80 GB |
| ~8–9B | ~18–20 GB | ~5–6 GB | 1×24–48 GB | 1–2×80 GB |
| 30B | ~60–65 GB | ~18 GB | 1×80 GB | 4×80 GB+ |

## 4. Preporuka

- 9B → EuroLLM-9B (prvi izbor; Apache 2.0, potvrđen hr, MT dokazi). Rezerva Apertus-8B.
- 2B → EuroLLM-1.7B (prvi izbor; napomena: stvarnih 1.657B, dokumentovati odstupanje) + Salamandra-2B kao ablacija na ijekavskom probnom setu.
- 4B → nema evropske baze: ili preskočiti tier, ili vlastiti 4B distilacijom/pruningom iz EuroLLM-9B uz TildeOpen-30B kao učitelja.
- TildeOpen-30B → učitelj, ne baza.
- Isključiti: Pharia-1 (nekomercijalno), CroissantLLM (EN–FR), EuroBERT (enkoder), Occiglot (nema bs).
