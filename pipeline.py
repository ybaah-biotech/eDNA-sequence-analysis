#!/usr/bin/env python3
"""
eDNA Sequence Analysis Pipeline
================================
Takes a FASTA file of environmental DNA sequences, queries NCBI BLAST,
parses the XML results, and outputs a species identification table and
biodiversity summary as CSV files.

Usage
-----
    python pipeline.py --fasta data/sample_sequences.fasta --email you@example.com

    # Use a stricter e-value and report top hit only:
    python pipeline.py --fasta data/sample_sequences.fasta --email you@example.com \\
        --evalue 1e-20 --top-hit-only

    # Query the 16S ribosomal database (e.g. for bacteria):
    python pipeline.py --fasta data/sample_sequences.fasta --email you@example.com \\
        --db 16S_ribosomal_RNA

NCBI Policy
-----------
NCBI requires a valid email address for all Entrez/BLAST API calls.
Results are cached as XML under data/results/xml/ so re-running the
pipeline does not repeat completed queries.
"""

import argparse
import logging
import sys
from pathlib import Path

from src.blast_query import run_blast_queries
from src.parser import parse_all_results
from src.summarise import build_hit_table, calculate_diversity, export_results
from src.utils import ensure_dir, load_fasta, setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="eDNA pipeline: FASTA -> NCBI BLAST -> species table + biodiversity summary",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--fasta", required=True,
        help="Path to input FASTA file",
    )
    parser.add_argument(
        "--email", required=True,
        help="Email address for NCBI Entrez API (required by NCBI policy)",
    )
    parser.add_argument(
        "--output", default="data/results",
        help="Directory for output CSV files",
    )
    parser.add_argument(
        "--db", default="nt",
        help="NCBI BLAST database (nt | 16S_ribosomal_RNA | ITS_RefSeq_Fungi ...)",
    )
    parser.add_argument(
        "--program", default="blastn",
        help="BLAST program (blastn | blastx | tblastn ...)",
    )
    parser.add_argument(
        "--evalue", type=float, default=1e-10,
        help="E-value significance threshold",
    )
    parser.add_argument(
        "--max-hits", type=int, default=5,
        help="Maximum BLAST hits to report per query sequence",
    )
    parser.add_argument(
        "--top-hit-only", action="store_true",
        help="Retain only the single best hit per query in the output table",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging(args.log_level)
    log = logging.getLogger(__name__)

    output_dir = Path(args.output)
    xml_dir = output_dir / "xml"
    ensure_dir(output_dir)
    ensure_dir(xml_dir)

    # ── 1. Load sequences ────────────────────────────────────────────────────
    log.info(f"Loading sequences from: {args.fasta}")
    sequences = load_fasta(args.fasta)
    log.info(f"Loaded {len(sequences)} sequence(s)")

    # ── 2. BLAST queries (cached) ────────────────────────────────────────────
    log.info("Running BLAST queries (cached XML files will be reused) ...")
    run_blast_queries(
        sequences=sequences,
        xml_dir=xml_dir,
        email=args.email,
        db=args.db,
        program=args.program,
        evalue=args.evalue,
    )

    # ── 3. Parse XML results ─────────────────────────────────────────────────
    log.info("Parsing BLAST XML results ...")
    hits = parse_all_results(
        xml_dir=xml_dir,
        max_hits=args.max_hits,
        evalue_threshold=args.evalue,
    )

    if not hits:
        log.warning(
            "No hits survived the e-value filter. "
            "Try relaxing --evalue (e.g. 1e-5) or check your sequences."
        )
        sys.exit(0)

    # ── 4. Build species table ───────────────────────────────────────────────
    log.info("Building species identification table ...")
    hit_table = build_hit_table(hits, top_hit_only=args.top_hit_only)

    # ── 5. Biodiversity metrics ──────────────────────────────────────────────
    log.info("Calculating biodiversity metrics ...")
    diversity = calculate_diversity(hit_table)

    # ── 6. Export ────────────────────────────────────────────────────────────
    export_results(hit_table, diversity, output_dir)

    # ── Summary banner ───────────────────────────────────────────────────────
    log.info("=" * 55)
    log.info("  Pipeline complete")
    log.info(f"  Sequences queried : {len(sequences)}")
    log.info(f"  Hits retained     : {len(hit_table)}")
    log.info(f"  Species richness  : {diversity['species_richness']}")
    log.info(f"  Shannon H        : {diversity['shannon_index']:.4f}")
    log.info(f"  Pielou J         : {diversity['pielou_evenness']:.4f}")
    log.info(f"  Outputs           : {output_dir}/")
    log.info("=" * 55)


if __name__ == "__main__":
    main()
