#!/usr/bin/env python3
"""
eDNA Sequence Analysis Pipeline
================================
Takes a FASTA file of environmental DNA sequences, queries BLAST (web or
local), parses the XML results, and outputs a species identification table
and biodiversity summary as CSV files.

Usage — web BLAST (NCBI)
------------------------
    python pipeline.py --fasta data/sample_sequences.fasta --email you@example.com

    # Stricter e-value, top hit only:
    python pipeline.py --fasta data/sample_sequences.fasta --email you@example.com \\
        --evalue 1e-20 --top-hit-only

    # 16S ribosomal database (bacteria):
    python pipeline.py --fasta data/sample_sequences.fasta --email you@example.com \\
        --db 16S_ribosomal_RNA

Usage — local BLAST+ (Phase 1)
-------------------------------
    python pipeline.py --fasta data/sample_sequences.fasta \\
        --local --db-path /data/blast/nt --threads 4

    # Custom database (e.g. SILVA 138):
    python pipeline.py --fasta data/sample_sequences.fasta \\
        --local --db-path /data/silva/SILVA_138_SSU --threads 4

    # Set up a local database first:
    python scripts/setup_db.py --db nt --dest /data/blast/

NCBI Policy
-----------
Web BLAST requires a valid email address for all Entrez/BLAST API calls.
Results are cached as XML under <output>/xml/ so re-running the pipeline
never repeats completed queries.
"""

import argparse
import logging
import sys
from pathlib import Path

from src.blast_query import run_blast_queries
from src.local_blast import run_local_blast
from src.parser import parse_all_results
from src.summarise import build_hit_table, calculate_diversity, export_results
from src.utils import ensure_dir, load_fasta, setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "eDNA pipeline: FASTA → BLAST (web or local) → "
            "species table + biodiversity summary"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # ── Input / output ───────────────────────────────────────────────────────
    parser.add_argument(
        "--fasta", required=True,
        help="Path to input FASTA file",
    )
    parser.add_argument(
        "--output", default="data/results",
        help="Directory for output CSV files and XML cache",
    )

    # ── BLAST mode ───────────────────────────────────────────────────────────
    mode = parser.add_argument_group(
        "BLAST mode",
        "Choose web BLAST (default) or local BLAST+.  "
        "With --local you must supply --db-path; --email is not required.",
    )
    mode.add_argument(
        "--local", action="store_true",
        help=(
            "Use local BLAST+ binary instead of NCBI web BLAST. "
            "Requires BLAST+ installed and --db-path set."
        ),
    )
    mode.add_argument(
        "--db-path", default=None, metavar="PATH",
        help=(
            "Path to the local BLAST database (without extension), "
            "e.g. /data/blast/nt  or  /data/silva/SILVA_138_SSU. "
            "Required when --local is set."
        ),
    )
    mode.add_argument(
        "--threads", type=int, default=1, metavar="N",
        help=(
            "Number of parallel BLAST workers (local mode only). "
            "1 is safe on HDDs; 4-8 works well on SSDs."
        ),
    )
    mode.add_argument(
        "--email", default=None,
        help=(
            "Email address for NCBI Entrez API.  "
            "Required by NCBI policy when NOT using --local."
        ),
    )

    # ── BLAST parameters ─────────────────────────────────────────────────────
    blast = parser.add_argument_group("BLAST parameters")
    blast.add_argument(
        "--db", default="nt",
        help="NCBI BLAST database for web mode (nt | 16S_ribosomal_RNA | ITS_RefSeq_Fungi ...)",
    )
    blast.add_argument(
        "--program", default="blastn",
        help="BLAST program (blastn | blastx | tblastn ...)",
    )
    blast.add_argument(
        "--evalue", type=float, default=1e-10,
        help="E-value significance threshold",
    )
    blast.add_argument(
        "--max-hits", type=int, default=5,
        help="Maximum BLAST hits to report per query sequence",
    )

    # ── Output options ───────────────────────────────────────────────────────
    output = parser.add_argument_group("Output options")
    output.add_argument(
        "--top-hit-only", action="store_true",
        help="Retain only the single best hit per query in the output table",
    )
    output.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging(args.log_level)
    log = logging.getLogger(__name__)

    # ── Validate flag combinations ────────────────────────────────────────────
    if args.local:
        if not args.db_path:
            log.error(
                "--local requires --db-path.  "
                "Example: --db-path /data/blast/nt\n"
                "Run 'python scripts/setup_db.py --help' to download a database."
            )
            sys.exit(1)
    else:
        if not args.email:
            log.error(
                "--email is required for web BLAST (NCBI policy).  "
                "Use --local --db-path <path> to run without an email."
            )
            sys.exit(1)

    output_dir = Path(args.output)
    xml_dir = output_dir / "xml"
    ensure_dir(output_dir)
    ensure_dir(xml_dir)

    # ── 1. Load sequences ────────────────────────────────────────────────────
    log.info(f"Loading sequences from: {args.fasta}")
    sequences = load_fasta(args.fasta)
    log.info(f"Loaded {len(sequences)} sequence(s)")

    # ── 2. BLAST queries (cached) ────────────────────────────────────────────
    if args.local:
        log.info(
            f"BLAST mode : LOCAL  |  db={args.db_path}  |  threads={args.threads}"
        )
        run_local_blast(
            sequences=sequences,
            xml_dir=xml_dir,
            db_path=args.db_path,
            program=args.program,
            evalue=args.evalue,
            max_hits=args.max_hits,
            threads=args.threads,
            version_file=output_dir / "db_version.json",
        )
    else:
        log.info(f"BLAST mode : WEB (NCBI)  |  db={args.db}  |  program={args.program}")
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
    mode_label = (
        f"local ({args.db_path})" if args.local
        else f"web NCBI ({args.db})"
    )
    log.info("=" * 58)
    log.info("  Pipeline complete")
    log.info(f"  BLAST mode        : {mode_label}")
    log.info(f"  Sequences queried : {len(sequences)}")
    log.info(f"  Hits retained     : {len(hit_table)}")
    log.info(f"  Species richness  : {diversity['species_richness']}")
    log.info(f"  Shannon H'        : {diversity['shannon_index']:.4f}")
    log.info(f"  Pielou J'         : {diversity['pielou_evenness']:.4f}")
    log.info(f"  Outputs           : {output_dir}/")
    log.info("=" * 58)


if __name__ == "__main__":
    main()
