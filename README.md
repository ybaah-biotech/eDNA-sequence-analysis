# eDNA Sequence Analysis Pipeline

**Automated species identification from environmental DNA — built for environmental consultancies, regulators, and field ecologists.**

---

`Tests: 38 passing` &nbsp;·&nbsp; `Phases: 2 of 10 complete` &nbsp;·&nbsp; `Python: 3.12`

---

Environmental DNA (eDNA) surveys capture traces of biological material from water or air samples and use DNA sequencing to identify which species are present. Processing the resulting sequence data manually is slow, error-prone, and hard to reproduce. This pipeline automates the entire workflow: from a raw DNA sequence file to a species identification table, biodiversity summary, and a client-ready PDF report — in under two minutes on a standard laptop, with no internet connection required.

---

## What it does

- **Local BLAST+ offline analysis** (Phase 1 complete) — run species identification against a local copy of the NCBI nucleotide database; no rate limits, no internet dependency, version-locked results
- **Regulatory PDF reports** (Phase 2 complete) — generate a 4-section PDF with cover page, executive summary with key metrics, colour-coded species table, and methodology section with database version embedded
- **Protected species detection** (Phase 3 in progress) — cross-reference results against UK Biodiversity Action Plan (BAP) and Wildlife and Countryside Act (WCA) species lists
- **Curated databases** (Phase 4 planned) — custom reference sets for specific habitat types
- **Multi-marker support** (Phase 5 planned) — COI, ITS, 16S, 18S markers in a single run
- **Rarefaction** (Phase 6 planned) — normalise results for unequal sequencing depth
- **Beta diversity** (Phase 7 planned) — compare species communities across sites
- **Cloud API** (Phase 8 planned) — REST endpoint for integration with LIMS and third-party tools
- **ASV/DADA2** (Phase 9 planned) — amplicon sequence variant denoising for higher resolution
- **Nanopore streaming** (Phase 10 planned) — real-time species identification in the field

---

## Quick start

### Web BLAST (NCBI — requires internet and email)

```bash
git clone https://github.com/ybaah-biotech/eDNA-sequence-analysis.git
cd eDNA-sequence-analysis
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Basic run
python pipeline.py \
    --fasta data/sample_sequences.fasta \
    --email your@email.com

# With PDF report
python pipeline.py \
    --fasta data/sample_sequences.fasta \
    --email your@email.com \
    --report --site "Cannock Chase Pond A" --analyst "Yaw Baah"
```

> NCBI policy requires a valid email for all Entrez API calls.
> Results are cached under `data/results/xml/` — re-running the pipeline skips completed queries.

### Local BLAST+ (offline — recommended for production use)

```bash
# Step 1: download a local database (run once)
python scripts/setup_db.py --db 16S_ribosomal_RNA --dest /data/blast/

# Step 2: run the pipeline offline
python pipeline.py \
    --fasta data/sample_sequences.fasta \
    --local --db-path /data/blast/16S_ribosomal_RNA \
    --threads 4

# With PDF report, site name, and analyst
python pipeline.py \
    --fasta data/sample_sequences.fasta \
    --local --db-path /data/blast/nt \
    --threads 4 \
    --report --site "Rutland Water North Shore" --analyst "Yaw Baah"
```

**All CLI flags:**

```
  --fasta          Path to input FASTA file                       [required]
  --local          Use local BLAST+ instead of NCBI web API       [flag]
  --db-path        Path to local database (required with --local)
  --threads        Parallel workers for local BLAST               [default: 1]
  --email          Email for NCBI Entrez (required without --local)
  --output         Output directory                    [default: data/results]
  --db             NCBI web database name                        [default: nt]
  --program        BLAST program                           [default: blastn]
  --evalue         E-value threshold                         [default: 1e-10]
  --max-hits       Max hits per query                            [default: 5]
  --top-hit-only   Retain only the best hit per query            [flag]
  --report         Generate a regulatory PDF report              [flag]
  --site           Site name for the PDF cover page
  --sample-date    Sample collection date (YYYY-MM-DD)
  --analyst        Analyst name for the PDF cover page
  --log-level      DEBUG | INFO | WARNING | ERROR        [default: INFO]
```

---

## Project structure

```
eDNA-sequence-analysis/
├── pipeline.py                    # CLI entry point — orchestrates all phases
├── mock_run.py                    # Offline demo — no NCBI account required
│
├── src/
│   ├── blast_query.py             # Web BLAST via NCBI Entrez (Biopython)
│   ├── local_blast.py             # Local BLAST+ via subprocess — Phase 1
│   ├── parser.py                  # BLAST XML parsing → structured hit records
│   ├── summarise.py               # Species table, LCA resolution, diversity metrics
│   ├── report.py                  # Regulatory PDF generator (ReportLab) — Phase 2
│   └── utils.py                   # FASTA loading, logging, directory helpers
│
├── scripts/
│   └── setup_db.py                # Download and verify local BLAST databases
│
├── data/
│   ├── sample_sequences.fasta     # Five representative UK eDNA sequences
│   └── results/                   # Pipeline outputs (auto-created)
│       ├── xml/                   # Cached BLAST XML (one file per query)
│       ├── blast_hit_table.csv    # Full species hit table with confidence flags
│       ├── biodiversity_summary.csv
│       ├── db_version.json        # Database version stamp for reproducibility
│       └── eDNA_Report.pdf        # Regulatory PDF (with --report flag)
│
├── tests/
│   └── test_parser.py             # 38 unit tests — run offline, no network required
│
├── docs/
│   └── modules/
│       ├── Module_01_BLAST_and_Alignment.pdf
│       ├── generate_module_01.py
│       ├── generate_module_02.py  # Local BLAST+ and Reference Databases
│       └── generate_module_03.py  # Regulatory PDF Reports and Data Interpretation
│
├── .devcontainer/
│   ├── devcontainer.json          # GitHub Codespaces config (Python 3.12 + BLAST+)
│   └── setup.sh
│
├── .github/
│   ├── workflows/tests.yml        # CI — runs full test suite on push/PR
│   └── ISSUE_TEMPLATE/
│       ├── bug.yml
│       └── feature.yml
│
├── requirements.txt
└── .gitignore
```

---

## Phase roadmap

| Phase | Name | Status | Description |
|-------|------|--------|-------------|
| 1 | Local BLAST+ | Complete | Offline species identification via subprocess, multi-threaded, version-locked database |
| 2 | PDF Reports | Complete | Regulatory-grade PDF output: cover page, metrics, colour-coded species table, methodology |
| 3 | Protected Species | In progress | Cross-reference results against UK BAP and Wildlife and Countryside Act species lists |
| 4 | Curated Databases | Planned | Custom reference sets for freshwater, saltwater, and terrestrial habitat types |
| 5 | Multi-marker | Planned | Simultaneous analysis across COI, ITS, 16S, and 18S markers |
| 6 | Rarefaction | Planned | Normalise species counts for unequal sequencing depth between samples |
| 7 | Beta Diversity | Planned | Community-level comparison across multiple sites and time points |
| 8 | Cloud API | Planned | REST endpoint for integration with external LIMS and reporting tools |
| 9 | ASV/DADA2 | Planned | Amplicon sequence variant denoising for higher-resolution species discrimination |
| 10 | Nanopore Streaming | Planned | Real-time species identification from MinION field sequencing |

---

## Output files

| File | Description |
|------|-------------|
| `blast_hit_table.csv` | One row per BLAST hit: query ID, species, resolved species (LCA), confidence flag (HIGH/MEDIUM/LOW), identity %, e-value, bit score, coverage % |
| `biodiversity_summary.csv` | Species richness, Shannon H', Pielou J', total queries with hits, unclassified query count, per-species read counts |
| `eDNA_Report.pdf` | Regulatory PDF — generated with `--report` flag. Contains cover page, executive summary with metric tiles, species table, biodiversity section, and full methodology |
| `db_version.json` | Database version stamp: database path, version string, program, and timestamp — written once per run for reproducibility |

### Confidence flags

Species assignments in `blast_hit_table.csv` carry a `confidence_flag` column determined by BLAST identity %:

| Flag | Identity threshold | Meaning |
|------|--------------------|---------|
| `high` | ≥ 97 % | Species-level assignment reliable |
| `medium` | 90 – 96 % | Genus-level reliable; species name uncertain — reported as *Genus sp.* |
| `low` | < 90 % | Alignment too divergent; treat with caution — row highlighted red in PDF |

---

## Learning materials

`docs/modules/` contains PDF learning guides covering the bioinformatics concepts behind each pipeline phase:

- **Module 01** — BLAST and Sequence Alignment: how BLAST works, e-values, identity thresholds
- **Module 02** — Local BLAST+ and Reference Databases: offline setup, version stamping, reproducibility
- **Module 03** — Regulatory PDF Reports and Data Interpretation: what regulators need, confidence scoring, LCA logic

The generator scripts (`generate_module_0X.py`) are included so the PDFs can be rebuilt or extended.

---

## Running tests

```bash
python -m pytest tests/ -v
```

All 38 tests run offline using synthetic BLAST XML fixtures — no network connection or NCBI account required. The test suite covers: species name parsing (cf./aff. qualifiers, hybrids, uncultured sequences, stop words), XML parsing and e-value filtering, biodiversity metrics, LCA taxonomy resolution, and confidence flag assignment.

The GitHub Actions workflow (`.github/workflows/tests.yml`) runs the full suite automatically on every push to `main` or `dev`.

---

## Running the offline demo

To see the pipeline end-to-end without a BLAST installation or internet connection:

```bash
python mock_run.py
```

This generates synthetic BLAST XML for eight representative UK freshwater pond organisms (*Chlorella vulgaris*, *Microcystis aeruginosa*, *Chlamydomonas* sp., *Daphnia* spp., *Chironomus* spp., mixed diatoms, *Phragmites australis*) and exercises LCA resolution, uncultured sequence rescue, and confidence flagging.

---

## Author

**Yaw Baah** — MSc Biotechnology (Nottingham Trent University, High Commendation) · BSc Biology (University of Nottingham)

[github.com/ybaah-biotech](https://github.com/ybaah-biotech)
