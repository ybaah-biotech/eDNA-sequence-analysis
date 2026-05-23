# LinkedIn Post 03 — Phase 2: Regulatory PDF Reports

*Angle: Bridging science and communication — CSVs aren't reports*

---

A CSV file is not a report. It's the raw material for one.

Most bioinformatics tools stop at the data file. You get a table of species names and identity percentages, and then it's up to you to turn that into something a client or regulator can read and act on. For a one-off analysis, fine. For a commercial eDNA service that needs to be traceable, auditable, and consistent, that gap is a real problem.

Phase 2 of my pipeline closes it.

`src/report.py` generates a four-section PDF directly from the pipeline outputs:

1. **Cover page** — site name, sample date, analyst, report date
2. **Executive summary** — five key metric tiles (species richness, Shannon H', Pielou J', sequences analysed, unclassified count) plus a plain-English interpretation of the community structure
3. **Species identification table** — one row per sequence, with the LCA-resolved species name, identity %, e-value, accession, and a colour-coded confidence flag
4. **Methodology** — database version embedded, LCA thresholds explained, full sample metadata

The confidence flag behaviour is the part I'm most pleased with. Every row is automatically flagged HIGH, MEDIUM, or LOW based on identity threshold. LOW rows render with a red background — no analyst has to remember to go back and flag uncertain results before sending to a client. It's built into the output.

The report is designed around Environment Agency and Natural England eDNA guidance, so the structure and language should be familiar to anyone who reviews these surveys.

The hardest part wasn't the code. It was working out what a regulator actually needs to see — and what they don't.

Code: github.com/ybaah-biotech/eDNA-sequence-analysis

#eDNA #EnvironmentalConsulting #Bioinformatics #Python #EnvironmentAgency
