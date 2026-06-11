# eDNA Sequence Analysis Pipeline

**Automated species identification from environmental DNA — built for environmental consultancies, regulators, and field ecologists.**

---

![Tests](https://img.shields.io/badge/tests-108%20passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Phases](https://img.shields.io/badge/phases-5%20of%2010%20complete-orange)
![CI](https://github.com/ybaah-biotech/eDNA-sequence-analysis/actions/workflows/tests.yml/badge.svg)

---

Environmental DNA (eDNA) surveys capture traces of biological material from water samples and use DNA sequencing to identify which species are present. Processing the resulting sequence data manually is slow, error-prone, and hard to reproduce. This pipeline automates the entire workflow — from a raw FASTA sequence file to a species identification table, biodiversity summary, protected species alerts, and a client-ready regulatory PDF report — with no internet connection required.

---

## What it does

- **Local BLAST+ offline analysis** ✅ — parallel species identification against curated local databases; no rate limits, no internet dependency, version-locked results
- **Regulatory PDF reports** ✅ — 4-section PDF with cover page, executive summary metric tiles, colour-coded species table, and methodology with database version embedded
- **Protected species detection** ✅ — automatic cross-reference against 20 UK aquatic and riparian protected species (Habitats Regulations 2017, WCA Schedule 5/6, NERC Act S41); CONFIRMED/POSSIBLE alert banners in the PDF
- **Curated database registry** ✅ — built-in registry of SILVA, BOLD, MIDORI2, ITS_RefSeq_Fungi, PR2; `--marker` flag auto-selects the correct database for your gene marker
- **Multi-marker support** ✅ — route COI, ITS, 16S, 18S, 12S markers in one FASTA to their own databases by ID prefix; per-marker diversity reported separately
- **Rarefaction** 🔄 — normalise species counts for unequal sequencing depth *(Phase 6)*
- **Beta diversity** 🔄 — community comparison across sites with PCoA ordination *(Phase 7)*
- **Cloud API** 🔄 — REST endpoint for integration with LIMS and third-party tools *(Phase 8)*
- **ASV/DADA2** 🔄 — amplicon sequence variant denoising for higher-resolution ID *(Phase 9)*
- **Nanopore streaming** 🔄 — real-time field identification from MinION devices *(Phase 10)*

---

## Quick start

### Offline demo (no BLAST install needed)

```bash
git clone https://github.com/ybaah-biotech/eDNA-sequence-analysis.git
cd eDNA-sequence-analysis
pip install -r requirements.txt
python mock_run.py
```

### Local BLAST+ (recommended for production)

```bash
# Step 1 — download a curated database (run once)
python scripts/setup_db.py --db 16S_ribosomal_RNA --dest /data/blast/

# Step 2 — run the pipeline
python pipeline.py \
    --fasta data/sample_sequences.fasta \
    --local --db-path /data/blast/16S_ribosomal_RNA \
    --threads 4 \
    --report --site "Rutland Water" --analyst "Yaw Baah"

# Use --marker to auto-select the recommended database for your gene marker
python pipeline.py \
    --fasta data/sample_sequences.fasta \
    --local --db-path /data/blast/bold \
    --marker COI --threads 4 --report
```

### Multi-marker run (Phase 5)

Tag each FASTA sequence with a marker prefix on its ID (`16S_001`, `COI_002`, `12S_fish`), then route each marker to its own database in a single run:

```bash
python pipeline.py \
    --fasta data/multi_marker.fasta \
    --local --multi-marker \
    --db-map 16S=/data/blast/silva,COI=/data/blast/bold,12S=/data/blast/midori2 \
    --threads 4 --report
```

Diversity is reported **per marker** (never pooled) in `marker_summary.csv` and a dedicated PDF section. Sequences whose marker has no `--db-map` entry are skipped with a warning.

### Web BLAST (NCBI — requires internet)

```bash
python pipeline.py \
    --fasta data/sample_sequences.fasta \
    --email your@email.com \
    --report --site "Site A" --analyst "Yaw Baah"
```

**All CLI flags:**

```
  --fasta          Path to input FASTA file                       [required]
  --local          Use local BLAST+ instead of NCBI web API       [flag]
  --db-path        Path to local database (required with --local)
  --threads        Parallel workers for local BLAST               [default: 1]
  --marker         Gene marker: 16S | 18S | COI | 12S | ITS | ITS1 | ITS2
                   Auto-selects recommended curated database and logs it
  --multi-marker   Route markers in one FASTA to different databases [flag]
  --db-map         MARKER=PATH pairs for --multi-marker, comma-separated
                   e.g. 16S=/data/blast/silva,COI=/data/blast/bold
  --email          Email for NCBI Entrez (required without --local)
  --output         Output directory                    [default: data/results]
  --db             NCBI web database name                        [default: nt]
  --evalue         E-value threshold                         [default: 1e-10]
  --max-hits       Max hits per query                            [default: 5]
  --top-hit-only   Retain only the best hit per query            [flag]
  --report         Generate a regulatory PDF report              [flag]
  --site           Site name for the PDF cover page
  --sample-date    Sample collection date (YYYY-MM-DD)
  --analyst        Analyst name for the PDF cover page
```

---

## Supported databases

| Database | Marker | Target organisms | Size |
|----------|--------|-----------------|------|
| SILVA 138.2 SSU | 16S / 18S | Bacteria, archaea, eukaryotes | ~10 GB |
| BOLD | COI | Animals — invertebrates, fish, birds | ~3 GB |
| MIDORI2 | 12S, COI | Vertebrates — fish, amphibians, GCN | ~2 GB |
| ITS_RefSeq_Fungi | ITS1 / ITS2 | Fungi | ~1 GB |
| PR2 | 18S | Protists, algae, phytoplankton | ~500 MB |
| NCBI nt | All | General purpose | ~300 GB |

Use `--marker COI` (or 16S, 12S, ITS, 18S) and the pipeline recommends the correct database automatically.

---

## Output files

| File | Description |
|------|-------------|
| `blast_hit_table.csv` | All hits with resolved species (LCA), confidence flag, identity %, e-value, protected_flag (+ `marker` in multi-marker runs) |
| `biodiversity_summary.csv` | Shannon H', Pielou J', species richness, per-taxon counts |
| `marker_summary.csv` | Per-marker diversity (multi-marker runs only) |
| `eDNA_Report.pdf` | Regulatory PDF — generated with `--report` flag |
| `db_version.json` | Database path, version string, timestamp — written per run for reproducibility |

### Confidence flags

| Flag | Identity | Meaning |
|------|----------|---------|
| `HIGH` | ≥ 97% | Species-level assignment reliable |
| `MEDIUM` | 90–96% | Genus-level reliable; reported as *Genus sp.* |
| `LOW` | < 90% | Alignment too divergent; row highlighted red in PDF |

---

## Protected species detection

The pipeline cross-references every BLAST result against 20 UK aquatic and riparian protected species drawn from four legislative frameworks:

- **EPS** — European Protected Species (Habitats Regulations 2017)
- **WCA Schedule 5** — Wildlife & Countryside Act 1981
- **WCA Schedule 6** — Prohibited methods of taking/killing
- **Section 41** — NERC Act 2006 (Species of Principal Importance)

Includes: *Triturus cristatus* (GCN), *Lutra lutra* (otter), *Austropotamobius pallipes* (white-clawed crayfish), *Margaritifera margaritifera* (freshwater pearl mussel), *Salmo salar* (Atlantic salmon), *Anguilla anguilla* (European eel), and 14 others.

When alerts fire, the PDF report opens with a **red banner (CONFIRMED)** or **amber banner (POSSIBLE)** before all other content, with a mandatory ecologist review disclaimer.

---

## Phase roadmap

| Phase | Name | Status |
|-------|------|--------|
| 1 | Local BLAST+ — offline, threaded, version-stamped | ✅ Complete |
| 2 | Regulatory PDF reports — 4-section client PDF | ✅ Complete |
| 3 | Protected species detection — 20 UK species, CONFIRMED/POSSIBLE alerts | ✅ Complete |
| 4 | Curated database registry — 7 databases, marker→DB routing | ✅ Complete |
| 5 | Multi-marker — route COI, ITS, 16S, 18S, 12S to their own databases in one run | ✅ Complete |
| 6 | Rarefaction — curves, subsampling, rarefied diversity | 🔄 Next |
| 7 | Beta diversity — Bray-Curtis, PCoA ordination, PERMANOVA | 📋 Planned |
| 8 | Cloud API — Flask/FastAPI, pay-per-run endpoint | 📋 Planned |
| 9 | ASV/DADA2 — denoising, higher-resolution ID | 📋 Planned |
| 10 | Nanopore streaming — real-time field analysis | 📋 Planned |

---

## Project structure

```
eDNA-sequence-analysis/
├── pipeline.py                    # CLI entry point
├── mock_run.py                    # Offline demo — no BLAST needed
│
├── src/
│   ├── blast_query.py             # Web BLAST via NCBI Entrez
│   ├── local_blast.py             # Local BLAST+ via subprocess (Phase 1)
│   ├── parser.py                  # BLAST XML → BlastHit dataclass
│   ├── summarise.py               # LCA resolution, diversity metrics, CSV export
│   ├── report.py                  # Regulatory PDF generator (Phase 2)
│   ├── protected.py               # Protected species detection (Phase 3)
│   ├── databases.py               # Curated database registry (Phase 4)
│   ├── markers.py                 # Multi-marker routing & per-marker diversity (Phase 5)
│   └── utils.py                   # FASTA loading, logging, helpers
│
├── scripts/
│   └── setup_db.py                # Download and verify local BLAST databases
│
├── tests/
│   ├── test_parser.py             # 38 tests — parsing, LCA, diversity metrics
│   ├── test_protected.py          # 12 tests — protected species detection
│   ├── test_databases.py          # 28 tests — database registry and marker routing
│   └── test_markers.py           # 30 tests — marker detection, per-marker diversity
│
├── notebooks/
│   ├── 01_BLAST_and_Species_Parsing.ipynb
│   └── 02_Local_BLAST_and_Databases.ipynb
│
├── data/
│   ├── sample_sequences.fasta     # Five representative UK eDNA sequences
│   └── results/                   # Pipeline outputs (auto-created)
│
├── .devcontainer/                 # GitHub Codespaces — Python 3.12 + BLAST+
├── .github/workflows/tests.yml   # CI — runs full test suite on push
└── requirements.txt
```

---

## Running tests

```bash
python -m pytest tests/ -v
```

108 tests — all run offline, no network required. Covers: species name parsing, XML parsing and e-value filtering, LCA taxonomy resolution, confidence flag assignment, diversity metrics, protected species detection, database registry routing, and multi-marker detection and per-marker diversity.

---

## Author

**Yaw Baah** — MSc Biotechnology (Nottingham Trent University, High Commendation) · BSc Biology (University of Nottingham)

Building commercial-grade bioinformatics tools for UK environmental consulting.

[github.com/ybaah-biotech](https://github.com/ybaah-biotech)
