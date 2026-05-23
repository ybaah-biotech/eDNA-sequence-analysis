# LinkedIn Post 01 — Project Introduction

*Angle: Builder journey — biologist teaching himself bioinformatics*

---

Biology degrees teach you to pipette. They don't teach you to write a pipeline.

I spent years working with environmental DNA in the lab — extracting, amplifying, sequencing. But when I started trying to make sense of the data at scale, I hit a wall. Processing results from a single eDNA water survey meant hours of manual BLAST searches, copying hits into spreadsheets, and trying to remember which database version I'd used six months ago. There had to be a better way.

So I built one.

Over the past few months I've been writing a Python pipeline that automates species identification from environmental DNA samples. You give it a FASTA file of sequences from a water sample; it runs BLAST, parses the results, resolves taxonomy using Lowest Common Ancestor logic, and outputs a clean species table with confidence scores. With the local BLAST mode I added in Phase 1, 100 sequences that used to take hours over the web API now finish in about 8 minutes offline.

Where it stands now:
- 38 unit tests passing
- 10 phases planned — 2 complete, 1 in progress
- Runs entirely offline once a database is downloaded
- Generates a regulatory PDF report that an environmental consultant or EA officer can actually read

I'm an MSc Biotechnology graduate (NTU, High Commendation) building commercial tools for eDNA work. This series documents the build phase by phase — the decisions, the mistakes, and what I learn along the way.

Follow along if you work in ecology, environmental consulting, or bioinformatics — or if you're also figuring out the gap between a biology degree and the computational world.

#eDNA #Bioinformatics #Python #EnvironmentalDNA #OpenSource
