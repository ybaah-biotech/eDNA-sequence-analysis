# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

eDNA metabarcoding pipeline — takes a FASTA file of environmental DNA sequences, runs BLAST alignment (web or local), resolves taxonomy using LCA logic, flags UK protected species, and outputs a species table, biodiversity metrics, and a regulatory PDF report. Built for environmental consultancies and UK regulators (Environment Agency, Natural England).

**Owner:** Yaw Baah — MSc Biotechnology (NTU), BSc Biology (Nottingham)
**Repo:** https://github.com/ybaah-biotech/eDNA-sequence-analysis

---

## Common commands

```bash
# Run full test suite
python -m pytest tests/ -v

# Run single test file
python -m pytest tests/test_parser.py -v

# Run single test by name
python -m pytest tests/test_protected.py::TestCheckProtected::test_confirmed_exact_match -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Offline demo (no BLAST install or network needed)
python mock_run.py

# Pipeline — web BLAST
python pipeline.py --fasta data/sample_sequences.fasta --email you@example.com --report --site "Site A" --analyst "Yaw Baah"

# Pipeline — local BLAST+
python pipeline.py --fasta data/sample_sequences.fasta --local --db-path /data/blast/nt --threads 4 --report

# Pipeline — multi-marker (Phase 5): route markers to different databases by FASTA-ID prefix
python pipeline.py --fasta data/multi_marker.fasta --local --multi-marker \
  --db-map 16S=/data/blast/silva,COI=/data/blast/bold,12S=/data/blast/midori2 --report

# Download a local database (16S ~1GB, nt ~300GB)
python scripts/setup_db.py --db 16S_ribosomal_RNA --dest /data/blast/

# Generate a learning module PDF
python docs/modules/generate_module_01.py

# Check local BLAST database info
blastdbcmd -db /path/to/database -info
```

---

## Architecture

### Data flow

```
FASTA file
  → src/utils.py::load_fasta()              {query_id: SeqRecord}
  → src/blast_query.py OR local_blast.py    XML files cached in output/xml/
  → src/parser.py::parse_all_results()      List[BlastHit]
  → src/summarise.py::build_hit_table()     DataFrame (+ LCA via resolve_taxonomy)
  → src/protected.py::check_protected()     DataFrame (+ protected_flag column)
  → src/summarise.py::calculate_diversity() diversity dict
  → src/summarise.py::export_results()      blast_hit_table.csv, biodiversity_summary.csv
  → src/report.py::generate_report()        eDNA_Report.pdf
```

### Phase completion status

| Phase | Module | Status |
|-------|--------|--------|
| 1 | `src/local_blast.py` — offline BLAST via subprocess, threading, DB version stamping | ✅ Complete |
| 2 | `src/report.py` — 4-section regulatory PDF (cover, executive summary, species table, methodology) | ✅ Complete |
| 3 | `src/protected.py` — 20 UK protected species, CONFIRMED/POSSIBLE alerts, PDF alert section | ✅ Complete |
| 4 | `src/databases.py` — DATABASE_REGISTRY (7 DBs), marker→DB routing, `--marker` pipeline flag | ✅ Complete |
| 5 | `src/markers.py` — marker detection from query-ID prefix, `--multi-marker`/`--db-map` routing, per-marker diversity | ✅ Complete |
| 6 | Rarefaction | 📋 Planned |
| 7 | Beta diversity | 📋 Planned |
| 8 | Cloud API | 📋 Planned |
| 9 | ASV/DADA2 | 📋 Planned |
| 10 | Nanopore streaming | 📋 Planned |

---

## Key source files

### src/parser.py
- `BlastHit` dataclass — the core record type passed through the pipeline
- `_extract_species(title)` — parses species name from a raw BLAST hit title. Uses `_SKIP_QUALIFIERS` (cf/aff/var/subsp), `_STOP_WORDS` (clone/isolate/strain), `_NON_SPECIFIC_TERMS` (uncultured/metagenome). Returns `"Genus sp."` or `"unclassified"`.
- `parse_blast_xml(path)` — parses one XML file, selects best HSP via `max(hsps, key=lambda h: h.bits)`, clamps coverage to 100.0

### src/summarise.py
- `resolve_taxonomy(df)` — LCA logic: ≥97% → species, 90–96% → genus consensus in identity window, <90% → genus consensus across all hits. Adds `resolved_species` column. Always call before diversity metrics.
- `build_hit_table(hits)` — converts List[BlastHit] to DataFrame, adds `confidence_flag` (high/medium/low), calls resolve_taxonomy
- `calculate_diversity(df)` — uses `resolved_species` column, excludes `"unclassified"`, returns Shannon H', Pielou J', species richness, counts

### src/markers.py (Phase 5)
- `detect_marker(query_id)` — reads marker from query-ID prefix before first `_` (`16S_001` → `16S`); case-insensitive; returns `"unknown"` if no recognised prefix. Vocabulary: 16S, 18S, 12S, COI, ITS, ITS1, ITS2.
- `add_marker_column(df)` — adds a `marker` column derived from `query_id`; safe on empty df; does not mutate input
- `split_sequences_by_marker(sequences)` — groups `{query_id: SeqRecord}` into `{marker: {query_id: SeqRecord}}` for per-marker BLAST routing; untagged sequences go to the `"unknown"` bucket (never dropped)
- `calculate_diversity_by_marker(df)` — `{marker: diversity_dict}`; reuses `calculate_diversity` on each marker subset; diversity is NEVER pooled across markers
- `marker_summary_frame(marker_diversity)` — flattens to a tidy one-row-per-marker DataFrame for `marker_summary.csv` and the PDF

### src/protected.py
- `PROTECTED_UK_SPECIES` — dict of 20 UK aquatic/riparian protected species (EPS, WCA Sch.5, S41, WCA Sch.6)
- `PROTECTED_GENERA` — auto-built at import from PROTECTED_UK_SPECIES
- `check_protected(df)` — adds `protected_flag` ("CONFIRMED"/"POSSIBLE"/None) to rank-1 rows only. CONFIRMED = exact species match. POSSIBLE = genus matches a genus containing protected species.
- `get_alerts(df)` — returns `{"has_alerts": bool, "confirmed": [...], "possible": [...], "highest_alert_level": ...}`

### src/local_blast.py
- `run_local_blast(sequences, xml_dir, db_path, ...)` — drop-in replacement for `run_blast_queries`. Caches XML per query_id. Uses `ThreadPoolExecutor` for parallel execution. Writes `db_version.json` via `stamp_db_version()`.
- `_check_blast_installed(program)` — raises `RuntimeError` with install instructions if binary not found

### src/report.py
- `generate_report(hit_table, diversity, output_path, ..., alerts=None)` — builds full PDF
- Section order: cover page → `_protected_species_section` (only if alerts) → executive summary → species table → biodiversity metrics → methodology
- Confidence colours: HIGH=green, MEDIUM=amber, LOW=red. LOW rows get red background in species table.

---

## Critical conventions

**Species naming:**
- `"Genus sp."` — resolved to genus only (LCA downgrade or no epithet found)
- `"unclassified"` — no meaningful taxonomic signal; excluded from all diversity calculations
- Never use raw `species` column for diversity — always use `resolved_species`

**BlastHit constructor (positional — used in tests):**
```python
BlastHit(query_id, query_length, hit_rank, accession, species, description,
         identity_pct, evalue, bit_score, alignment_length, query_coverage_pct)
```

**Identity thresholds (defined in summarise.py as `_CONF_HIGH=97.0`, `_CONF_MED=90.0`):**
- ≥97% → species level (HIGH confidence)
- 90–96% → genus level (MEDIUM confidence)
- <90% → low confidence (still reported, excluded from diversity, flagged red)

**Never do:**
- `alignment.hsps[0]` — always `max(hsps, key=lambda h: h.bits)`
- Use `NCBIWWW.qblast` in new code — use `src/local_blast.py`
- Exceed 100.0 for `query_coverage_pct` — clamp with `min(..., 100.0)`
- Count `"unclassified"` as a taxon in diversity
- Call `calculate_diversity()` before `resolve_taxonomy()`

---

## Testing

108 tests across four files. All must pass before any commit.

- `tests/test_parser.py` — 38 tests: species parsing (16), XML parsing (4), diversity metrics (8), stop words (4), LCA resolution (6)
- `tests/test_protected.py` — 12 tests: check_protected (6), get_alerts (4), PROTECTED_GENERA structure (2)
- `tests/test_databases.py` — 28 tests: registry structure (7), get_database_info (6), recommend_database (11), list_databases (4)
- `tests/test_markers.py` — 30 tests: detect_marker (13), add_marker_column (4), split_sequences_by_marker (4), calculate_diversity_by_marker (5), marker_summary_frame (4)

Test DataFrames for protected tests are built directly from `pd.DataFrame` dicts — no BlastHit constructor needed.

---

## Outputs

| File | Description |
|------|-------------|
| `blast_hit_table.csv` | All hits with resolved_species, confidence_flag, protected_flag (+ `marker` column in multi-marker runs) |
| `biodiversity_summary.csv` | Shannon H', Pielou J', species richness, per-taxon counts |
| `marker_summary.csv` | Per-marker diversity (multi-marker runs only) |
| `db_version.json` | Database title, version string, timestamp (local mode). Multi-marker: combined version + per-marker `db_version_{marker}.json` files |
| `eDNA_Report.pdf` | Regulatory PDF — generated with `--report` flag; gains a per-marker summary section in multi-marker runs |

---

## Learning materials

`notebooks/` — Jupyter notebooks (run in GitHub Codespaces):
- 01: BLAST & Species Parsing (21 cells, fully offline)
- 02: Local BLAST & Databases (16 cells, fully offline)

Learning module PDFs and LinkedIn post drafts are kept locally only
(not version controlled).

---

## CI / devcontainer

- GitHub Actions: `.github/workflows/tests.yml` — runs pytest on push to main/dev, uploads coverage to Codecov
- Devcontainer: `.devcontainer/` — Python 3.12, BLAST+ pre-installed via apt-get, runs test suite on create
- Issue templates: `.github/ISSUE_TEMPLATE/bug.yml` and `feature.yml`
