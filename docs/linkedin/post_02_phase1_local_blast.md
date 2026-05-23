# LinkedIn Post 02 — Phase 1: Local BLAST+

*Angle: Solved a real problem — the rate-limiting bottleneck of web BLAST*

---

The NCBI web BLAST API caps you at 3 requests per second. Each sequence takes 30 to 120 seconds to come back. Run 100 sequences and you're waiting 3 hours — if nothing times out.

That's not a workflow. That's babysitting.

Phase 1 of my eDNA pipeline replaces the web API with a local BLAST+ installation running on your own machine. Same science, same database, no rate limits. With `--threads 4` on an SSD, those same 100 sequences run in about 8 minutes.

The core of it is `src/local_blast.py` — a subprocess wrapper that fires BLAST jobs in parallel using Python's `ThreadPoolExecutor`. Each query writes its own XML file, so nothing blocks and caching still works. If you stop halfway through and restart, it picks up from where it left off.

The part I didn't expect to care about: database version stamping.

NCBI updates its nucleotide database daily. A sequence that maps to *Betula pendula* today might resolve to a different accession or a revised species name in six months, because taxonomists update records continuously. If you can't say exactly which version of the database you used, your results are technically not reproducible — and for environmental compliance work, that matters.

Every local run now writes a `db_version.json` file alongside the results. It records the database path, the version string from `blastdbcmd`, and the timestamp. The PDF report embeds this in the methodology section automatically.

The learning: I didn't expect version control for biological databases to be a scientific credibility issue — but it is.

Code: github.com/ybaah-biotech/eDNA-sequence-analysis

#eDNA #BLAST #Bioinformatics #Python #ReproducibleScience
