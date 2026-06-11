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
from src.databases import recommend_database
from src.local_blast import run_local_blast
from src.markers import (
    add_marker_column,
    calculate_diversity_by_marker,
    marker_summary_frame,
    split_sequences_by_marker,
)
from src.parser import parse_all_results
from src.protected import check_protected, get_alerts
from src.report import generate_report
from src.summarise import build_hit_table, calculate_diversity, export_results
from src.utils import ensure_dir, load_fasta, setup_logging


def parse_db_map(raw: str) -> dict:
    """Parse a '--db-map' string into a {marker: db_path} dict.

    Format: 'MARKER=PATH,MARKER=PATH'. Marker names are upper-cased so
    '16s=...' and '16S=...' are equivalent. Raises ValueError on malformed
    input so the CLI can report it cleanly.
    """
    mapping: dict = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if "=" not in pair:
            raise ValueError(
                f"Malformed --db-map entry '{pair}'. "
                "Expected MARKER=PATH (e.g. 16S=/data/blast/silva)."
            )
        marker, path = pair.split("=", 1)
        marker = marker.strip().upper()
        path = path.strip()
        if not marker or not path:
            raise ValueError(
                f"Malformed --db-map entry '{pair}'. "
                "Both a marker and a path are required."
            )
        mapping[marker] = path
    if not mapping:
        raise ValueError("--db-map was empty. Provide at least one MARKER=PATH pair.")
    return mapping


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

    # ── Multi-marker mode (Phase 5) ──────────────────────────────────────────
    multi = parser.add_argument_group(
        "Multi-marker mode (Phase 5)",
        "Route different gene markers in one FASTA to different databases. "
        "Sequences are tagged by a marker prefix on the FASTA ID "
        "(e.g. 16S_001, COI_002). Local mode only.",
    )
    multi.add_argument(
        "--multi-marker", action="store_true",
        help=(
            "Enable multi-marker routing. Requires --local and --db-map. "
            "Each marker group is BLASTed against its mapped database; "
            "diversity is reported per marker."
        ),
    )
    multi.add_argument(
        "--db-map", default=None, metavar="MAP",
        help=(
            "Comma-separated MARKER=PATH pairs for --multi-marker, e.g. "
            "'16S=/data/blast/silva,COI=/data/blast/bold,12S=/data/blast/midori2'. "
            "Markers present in the FASTA without a mapping are skipped with a warning."
        ),
    )

    # ── BLAST parameters ─────────────────────────────────────────────────────
    blast = parser.add_argument_group("BLAST parameters")
    blast.add_argument(
        "--db", default="nt",
        help="NCBI BLAST database for web mode (nt | 16S_ribosomal_RNA | ITS_RefSeq_Fungi ...)",
    )
    blast.add_argument(
        "--marker", default=None,
        metavar="GENE",
        help=(
            "Gene marker used in PCR (16S | 18S | COI | 12S | ITS | ITS1 | ITS2). "
            "When --local is set and --db-path is not provided, the pipeline "
            "auto-selects the recommended curated database for this marker "
            "and logs the recommendation. "
            "Example: --marker COI  →  uses BOLD."
        ),
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
        "--report", action="store_true",
        help="Generate a regulatory PDF report alongside the CSV outputs",
    )
    output.add_argument(
        "--site", default="Unknown site", metavar="NAME",
        help="Site name printed on the PDF report cover page",
    )
    output.add_argument(
        "--sample-date", default="", metavar="YYYY-MM-DD",
        help="Sample collection date for the PDF report (defaults to today)",
    )
    output.add_argument(
        "--analyst", default="Unknown", metavar="NAME",
        help="Analyst name printed on the PDF report cover page",
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
    db_map: dict = {}
    if args.multi_marker:
        if not args.local:
            log.error("--multi-marker requires --local.")
            sys.exit(1)
        if not args.db_map:
            log.error(
                "--multi-marker requires --db-map.  Example:\n"
                "  --db-map 16S=/data/blast/silva,COI=/data/blast/bold"
            )
            sys.exit(1)
        try:
            db_map = parse_db_map(args.db_map)
        except ValueError as exc:
            log.error(str(exc))
            sys.exit(1)
    elif args.local:
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

    # ── Marker → database auto-selection (Phase 4) ───────────────────────────
    if args.marker:
        try:
            recommended = recommend_database(args.marker)
            if args.local and not args.db_path:
                log.error(
                    f"--marker {args.marker} recommends database '{recommended.display_name}' "
                    f"(~{recommended.approx_size_gb:.0f} GB). "
                    f"Download it first:\n"
                    f"  python scripts/setup_db.py --db {recommended.name} --dest /data/blast/\n"
                    f"Then re-run with: --local --db-path /data/blast/{recommended.name}"
                )
                sys.exit(1)
            log.info(
                f"Marker: {args.marker.upper()}  →  "
                f"Recommended database: {recommended.display_name} "
                f"({recommended.organisms})"
            )
        except ValueError as exc:
            log.error(str(exc))
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
    if args.multi_marker:
        log.info("BLAST mode : LOCAL MULTI-MARKER")
        grouped = split_sequences_by_marker(sequences)
        db_versions: dict = {}
        routed_markers: list = []
        for marker, group in sorted(grouped.items()):
            db_path = db_map.get(marker)
            if db_path is None:
                log.warning(
                    "No --db-map entry for marker '%s' (%d sequence(s)) — skipping. "
                    "Add '%s=/path/to/db' to --db-map to include it.",
                    marker, len(group), marker,
                )
                continue
            log.info(
                "Marker %s : %d sequence(s)  →  %s", marker, len(group), db_path
            )
            ver_file = output_dir / f"db_version_{marker}.json"
            run_local_blast(
                sequences=group,
                xml_dir=xml_dir,
                db_path=db_path,
                program=args.program,
                evalue=args.evalue,
                max_hits=args.max_hits,
                threads=args.threads,
                version_file=ver_file,
            )
            routed_markers.append(marker)
            try:
                import json as _json
                db_versions[marker] = _json.loads(
                    ver_file.read_text(encoding="utf-8")
                ).get("db_version", "unknown")
            except Exception:  # noqa: BLE001
                db_versions[marker] = "unknown"

        if not routed_markers:
            log.error(
                "No sequences could be routed — none of the detected markers "
                "had a --db-map entry. Markers found: %s",
                ", ".join(sorted(grouped.keys())) or "none",
            )
            sys.exit(1)

        # Combined version stamp so the report methodology stays self-documenting
        combined = "; ".join(f"{m} → {db_versions[m]}" for m in routed_markers)
        (output_dir / "db_version.json").write_text(
            __import__("json").dumps(
                {
                    "db_version": f"Multi-marker: {combined}",
                    "markers": db_versions,
                    "program": args.program,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    elif args.local:
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

    # ── 4b. Protected species check ──────────────────────────────────────────
    log.info("Checking for protected species ...")
    hit_table = check_protected(hit_table)
    alerts    = get_alerts(hit_table)
    if alerts["has_alerts"]:
        for det in alerts.get("confirmed", []):
            log.warning(
                "PROTECTED SPECIES DETECTED: %s (%s) — %s",
                det.get("species", "unknown"),
                det.get("common_name", "unknown"),
                det.get("legislation", "unknown legislation"),
            )
    n_confirmed = len(alerts.get("confirmed", []))
    n_possible  = len(alerts.get("possible",  []))
    log.info(
        "Protected species check complete — %d confirmed, %d possible",
        n_confirmed, n_possible,
    )

    # ── 5. Biodiversity metrics ──────────────────────────────────────────────
    log.info("Calculating biodiversity metrics ...")
    diversity = calculate_diversity(hit_table)

    # ── 5b. Per-marker breakdown (multi-marker runs) ─────────────────────────
    marker_diversity: dict = {}
    if args.multi_marker:
        hit_table = add_marker_column(hit_table)
        marker_diversity = calculate_diversity_by_marker(hit_table)
        summary_df = marker_summary_frame(marker_diversity)
        summary_path = output_dir / "marker_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        log.info(f"Per-marker summary -> {summary_path}")
        for marker, d in sorted(marker_diversity.items()):
            log.info(
                "  %-7s richness=%d  H'=%.3f  J'=%.3f",
                marker, d["species_richness"], d["shannon_index"], d["pielou_evenness"],
            )

    # ── 6. Export CSVs ───────────────────────────────────────────────────────
    export_results(hit_table, diversity, output_dir)

    # ── 7. Optional PDF report ───────────────────────────────────────────────
    if args.report:
        log.info("Generating regulatory PDF report ...")
        report_path = generate_report(
            hit_table=hit_table,
            diversity=diversity,
            output_path=output_dir / "eDNA_Report.pdf",
            site_name=args.site,
            sample_date=args.sample_date,
            analyst=args.analyst,
            db_version_file=output_dir / "db_version.json",
            alerts=alerts,
            marker_diversity=marker_diversity or None,
        )
        log.info(f"  Report saved -> {report_path}")

    # ── Summary banner ───────────────────────────────────────────────────────
    if args.multi_marker:
        mode_label = f"local multi-marker ({len(marker_diversity)} marker(s))"
    elif args.local:
        mode_label = f"local ({args.db_path})"
    else:
        mode_label = f"web NCBI ({args.db})"
    log.info("=" * 58)
    log.info("  Pipeline complete")
    log.info(f"  BLAST mode        : {mode_label}")
    if args.marker:
        log.info(f"  Marker            : {args.marker.upper()}")
    log.info(f"  Sequences queried : {len(sequences)}")
    log.info(f"  Hits retained     : {len(hit_table)}")
    log.info(f"  Species richness  : {diversity['species_richness']}")
    log.info(f"  Shannon H'        : {diversity['shannon_index']:.4f}")
    log.info(f"  Pielou J'         : {diversity['pielou_evenness']:.4f}")
    log.info(f"  Protected alerts  : {n_confirmed} confirmed, {n_possible} possible")
    log.info(f"  Outputs           : {output_dir}/")
    log.info("=" * 58)


if __name__ == "__main__":
    main()
