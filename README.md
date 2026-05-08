# eDNA Sequence Analysis Pipeline

A command-line pipeline for environmental DNA (eDNA) species identification via NCBI BLAST. Takes raw FASTA sequences from airborne eDNA sampling, queries the NCBI nucleotide database, and produces a clean species identification table and alpha-diversity summary.

---

## Background

Environmental DNA metabarcoding is an increasingly powerful tool for passive biodiversity monitoring. Airborne eDNA — captured via Burkard spore traps, passive samplers, or filter membranes — encodes signals from pollen, fungal spores, insect fragments, and other biological particles. This pipeline implements the core bioinformatics workflow:

1. **Sequence ingestion** — load a FASTA file of eDNA amplicon reads
2. **Taxonomic identification** — query NCBI BLAST against the `nt` nucleotide database (or a specialised database such as `ITS_RefSeq_Fungi`)
3. **Result parsing** — extract identity %, e-value, coverage, and accession per hit
4. **Biodiversity summary** — compute species richness, Shannon–Wiener diversity index (H′), and Pielou's evenness (J′)

The pipeline is designed around ITS (Internal Transcribed Spacer) markers for fungi, ITS2 for plants, and the trnL intron for vascular plant pollen — all standard eDNA barcoding loci.

---

## Project Structure

```
eDNA-sequence-analysis/
├── pipeline.py                  # CLI entry point
├── src/
│   ├── blast_query.py           # NCBI BLAST querying with XML caching
│   ├── parser.py                # BLAST XML parsing → structured records
│   ├── summarise.py             # Species table + diversity metrics
│   └── utils.py                 # FASTA loading, logging, directory helpers
├── data/
│   ├── sample_sequences.fasta   # Five representative airborne eDNA sequences
│   └── results/                 # Pipeline outputs (auto-created)
│       ├── xml/                 # Cached BLAST XML (one file per query)
│       ├── blast_hit_table.csv  # Full species hit table
│       └── biodiversity_summary.csv
├── tests/
│   └── test_parser.py           # Unit tests (no network required)
├── requirements.txt
└── .gitignore
```

---

## Installation

```bash
git clone https://github.com/ybaah-biotech/eDNA-sequence-analysis.git
cd eDNA-sequence-analysis

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

**Dependencies:** `biopython ≥ 1.83`, `pandas ≥ 2.0`

---

## Usage

### Basic run (uses sample data)

```bash
python pipeline.py \
    --fasta data/sample_sequences.fasta \
    --email your@email.com
```

> NCBI policy requires a valid email address for all Entrez API calls.  
> Results are cached under `data/results/xml/` — re-running the pipeline skips completed queries.

### Full options

```
python pipeline.py --help

  --fasta        Path to input FASTA file                      [required]
  --email        Email for NCBI Entrez API                     [required]
  --output       Output directory                   [default: data/results]
  --db           BLAST database                            [default: nt]
                 Alternatives: ITS_RefSeq_Fungi, 16S_ribosomal_RNA
  --program      BLAST program                        [default: blastn]
  --evalue       E-value threshold                      [default: 1e-10]
  --max-hits     Max hits reported per query                [default: 5]
  --top-hit-only Only retain best hit per query             [flag]
  --log-level    DEBUG | INFO | WARNING | ERROR         [default: INFO]
```

### Examples

```bash
# Fungal eDNA against the curated ITS fungi database
python pipeline.py \
    --fasta data/sample_sequences.fasta \
    --email your@email.com \
    --db ITS_RefSeq_Fungi \
    --evalue 1e-20 \
    --top-hit-only

# Strict threshold, top hit per query, verbose logging
python pipeline.py \
    --fasta my_samples.fasta \
    --email your@email.com \
    --evalue 1e-30 \
    --max-hits 3 \
    --top-hit-only \
    --log-level DEBUG
```

---

## Output

### `blast_hit_table.csv`

One row per BLAST hit (up to `--max-hits` per query sequence):

| query_id  | hit_rank | accession | species             | identity_pct | evalue   | bit_score | query_coverage_pct |
|-----------|----------|-----------|---------------------|-------------|----------|-----------|--------------------|
| QUERY_001 | 1        | AJ312462  | Betula pendula      | 98.60       | 1.2e-104 | 380.6     | 100.00             |
| QUERY_002 | 1        | KJ869093  | Alternaria alternata| 97.84       | 0.0      | 895.2     | 99.41              |
| …         | …        | …         | …                   | …           | …        | …         | …                  |

### `biodiversity_summary.csv`

| metric                        | value  |
|-------------------------------|--------|
| species_richness              | 5      |
| shannon_index_H               | 1.6094 |
| pielou_evenness_J             | 1.0000 |
| total_queries_with_hit        | 5      |
| count_Betula_pendula          | 1      |
| count_Alternaria_alternata    | 1      |
| …                             | …      |

**Shannon–Wiener index (H′):** H′ = −Σ pᵢ ln(pᵢ), where pᵢ is the proportion of queries assigned to species i. Higher values indicate greater diversity.  
**Pielou's evenness (J′):** J′ = H′ / ln(S), where S = species richness. J′ = 1.0 indicates perfectly equal abundance of all species.

---

## Sample Data

`data/sample_sequences.fasta` contains five sequences representative of organisms commonly detected in UK urban airborne eDNA studies:

| Query ID  | Organism                       | Marker         | Ecological role              |
|-----------|--------------------------------|----------------|------------------------------|
| QUERY_001 | *Betula pendula* (Silver Birch)| ITS2           | Major allergenic pollen source|
| QUERY_002 | *Alternaria alternata*         | ITS1-5.8S-ITS2 | Ubiquitous saprotrophic fungus|
| QUERY_003 | *Pinus sylvestris* (Scots Pine)| trnL intron    | Wind-dispersed conifer pollen |
| QUERY_004 | *Cladosporium cladosporioides* | ITS1-5.8S-ITS2 | Dominant airborne fungal spore|
| QUERY_005 | *Quercus robur* (English Oak)  | ITS2           | Deciduous pollen, urban parks |

These are representative synthetic sequences modelled on publicly available GenBank data for these taxa. For production use, substitute your own FASTA file from sequencing output.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

Tests run offline using a synthetic BLAST XML fixture — no network or NCBI account required.

---

## NCBI Usage Policy

This pipeline uses the NCBI BLAST web API via Biopython's `NCBIWWW.qblast`. Per [NCBI Entrez guidelines](https://www.ncbi.nlm.nih.gov/books/NBK25497/):

- Provide a valid email address (`--email`)
- Do not submit more than 3 requests per second
- For high-throughput workloads (>100 sequences), use a **local BLAST+ installation** with a downloaded database (`makeblastdb` + `blastn` command-line)

Result XML files are cached locally; only new sequences trigger API calls on re-runs.

---

## Extending the Pipeline

| Use case | Change |
|---|---|
| Local BLAST+ (large datasets) | Replace `NCBIWWW.qblast` in `blast_query.py` with `subprocess` call to `blastn` |
| Metabarcoding (multiple samples) | Loop over per-sample FASTA files; aggregate hit tables |
| Taxonomic visualisation | Load `blast_hit_table.csv` into R or a Jupyter notebook; use `ggplot2` / `matplotlib` |
| QIIME2 integration | Export species assignments as a feature table; feed into diversity analyses |

---

## Author

**Yaw Baah** · MSc Biotechnology (NTU, High Commendation) · BSc Biology (UoN)  
[github.com/ybaah-biotech](https://github.com/ybaah-biotech)
