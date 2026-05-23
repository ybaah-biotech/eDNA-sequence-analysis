# GitHub Copilot Instructions — eDNA Sequence Analysis Pipeline

## Project domain
Environmental DNA (eDNA) metabarcoding pipeline for species identification
from aquatic, soil, and airborne samples. Sequences are aligned against
reference databases using BLAST and classified using LCA taxonomy.

## Architecture — module responsibilities

| File | Responsibility |
|---|---|
| `pipeline.py` | CLI entry point — argument parsing, orchestration only |
| `src/blast_query.py` | Web BLAST queries via NCBI API (legacy) |
| `src/local_blast.py` | Local BLAST+ queries via subprocess (Phase 1) |
| `src/parser.py` | BLAST XML → BlastHit dataclass objects |
| `src/summarise.py` | BlastHit list → DataFrame, LCA, diversity metrics, CSV/PDF export |
| `src/report.py` | Regulatory PDF report generation (Phase 2) |
| `src/protected.py` | Protected species cross-reference (Phase 3) |
| `src/utils.py` | FASTA loading, logging, directory helpers |
| `mock_run.py` | Offline demonstration — generates synthetic BLAST XML |
| `scripts/setup_db.py` | Download and format reference databases |
| `tests/test_parser.py` | Unit tests — run with `pytest` |

## Biological context — key concepts

- **eDNA**: DNA shed into the environment (water, soil, air) by organisms
- **Metabarcoding**: sequencing mixed DNA from environmental samples to identify community composition
- **BLAST**: sequence alignment tool — finds similar sequences in a database
- **E-value**: statistical significance of a BLAST match (lower = more significant; threshold 1e-10)
- **% identity**: how similar the query and hit sequences are (≥97 % = species level for most markers)
- **LCA (Lowest Common Ancestor)**: when top BLAST hits disagree on species, assign the deepest taxonomic level they all agree on
- **Shannon H′**: diversity index — measures both richness and evenness
- **Pielou J′**: evenness index — 1.0 = all species equally abundant
- **resolved_species**: post-LCA classification used for diversity calculations (preferred over raw `species` column)

## Marker gene conventions

| Marker | Target group | % identity threshold |
|---|---|---|
| 16S rRNA | Bacteria, Archaea | ≥97 % |
| 18S rRNA | Eukaryotes (algae, protists) | ≥97 % |
| ITS / ITS2 | Fungi | ≥97 % |
| COI | Metazoans (invertebrates, fish) | ≥97 % |

## Coding conventions

- All source files use type hints throughout
- Docstrings follow NumPy style with Parameters/Returns sections
- Module-level constants use `SCREAMING_SNAKE_CASE` with frozenset for immutable sets
- Logging via `log = logging.getLogger(__name__)` — never print() in library code
- CSV outputs: `blast_hit_table.csv` and `biodiversity_summary.csv`
- Species names: `"Genus sp."` for unresolved, `"unclassified"` for unidentifiable

## What to avoid in suggestions

- Do not use `alignment.hsps[0]` — always select best HSP with `max(hsps, key=lambda h: h.bits)`
- Do not use `NCBIWWW.qblast` in new code — use `src/local_blast.py` instead
- Do not use raw `species` column for diversity metrics — use `resolved_species`
- Do not exceed 100 for `query_coverage_pct` — clamp with `min(..., 100.0)`
- Do not treat `"unclassified"` as a taxon in diversity calculations — filter it out
- Do not add `diversity` calculations before calling `resolve_taxonomy()` on the DataFrame

## Test patterns

```python
# BlastHit constructor (positional):
# query_id, query_length, hit_rank, accession, species, description,
# identity_pct, evalue, bit_score, alignment_length, query_coverage_pct
hit = BlastHit("Q1", 300, 1, "ACC1", "Betula pendula", "desc", 98.5, 1e-80, 400.0, 295, 98.0)
```

## Current phase

**Phase 1 complete**: local BLAST+ (`src/local_blast.py`) with threading, caching, DB version stamping.
**Phase 2 complete**: regulatory PDF report (`src/report.py`) — `generate_report()` takes hit_table + diversity dict and produces a 4-section client PDF.
**Phase 3 next**: protected species cross-reference (`src/protected.py`) — flag sequences matching UK BAP / WCA Schedule 5 species.
