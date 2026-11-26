#!/usr/bin/env python3
"""heldout-chart.png — readout vs generacija po verzijama (mjereno, ne fabricirano).

Izvori: docs/training/bh-decision-2-*.md + datasets/selfdistill/readout-*.jsonl
(v0.1 readout nije mjeren → 0, istom konvencijom kao stari graf).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

labels = ["stock\nTacit-4B", "v0.1\n(mix v2)", "v0.2-rc\n(mix v4)", "v0.3-rc\n(mix v7)",
          "v0.4-rc\n(mix v9)", "v10\n(mix v10, r16)", "v0.5-rc\n(mix v10, rec.A)"]
readout = [16, 0, 15, 15, 17, 15, 18]
gener = [7, 6, 3, 7, 6, 5, 5]

x = range(len(labels))
w = 0.35
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar([i - w / 2 for i in x], readout, w, label="readout /19", color="#1f77b4")
ax.bar([i + w / 2 for i in x], gener, w, label="generacija tolerantno /19", color="#ff7f0e")
ax.set_title("BH-Decision-2-4B — held-out (20 neviđenih, 19 bodovanih)")
ax.set_ylabel("held-out tačno / 19")
ax.set_xticks(list(x))
ax.set_xticklabels(labels)
ax.set_ylim(0, 20)
ax.legend()
fig.tight_layout()
fig.savefig("docs/heldout-chart.png", dpi=100)
print("chart-OK")
