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
| `src/databases.py` | Curated database registry, marker→DB routing (Phase 4) |
| `src/markers.py` | Marker detection, multi-marker routing, per-marker diversity (Phase 5) |
| `src/utils.py` | FASTA loading, logging, directory helpers |
| `mock_run.py` | Offline demonstration — generates synthetic BLAST XML |
| `scripts/setup_db.py` | Download and format reference databases |
| `tests/test_parser.py` | Unit tests — species parsing, LCA, diversity metrics |
| `tests/test_protected.py` | Unit tests — protected species detection and alerts |
| `tests/test_databases.py` | Unit tests — database registry and marker routing |
| `tests/test_markers.py` | Unit tests — marker detection and per-marker diversity |

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

**Phase 1 complete**: local BLAST+ (`src/local_blast.py`) — threading, caching, DB version stamping.
**Phase 2 complete**: regulatory PDF report (`src/report.py`) — 4-section client PDF with confidence colour coding.
**Phase 3 complete**: protected species detection (`src/protected.py`) — 20 UK species, CONFIRMED/POSSIBLE alerts, PDF red/amber banners.
**Phase 4 complete**: curated database registry (`src/databases.py`) — 7 databases, marker→DB routing, `--marker` pipeline flag.
**Phase 5 complete**: multi-marker (`src/markers.py`) — marker detection from FASTA-ID prefix, `--multi-marker`/`--db-map` routing, per-marker diversity, `marker_summary.csv`, PDF marker section.
**Phase 6 next**: rarefaction — curves, subsampling to equal depth, rarefied diversity metrics, Chao1 estimator.

Marker convention: sequences are tagged by a prefix before the first underscore on the FASTA query ID (`16S_001`, `COI_002`, `12S_fish`). `detect_marker` is case-insensitive and returns `"unknown"` when no recognised prefix is present.
