#!/usr/bin/env python3
"""
scripts/setup_db.py — Download and prepare a local BLAST database.

This script automates Phase 1 database setup so you never have to read
the NCBI documentation.  It wraps the BLAST+ ``update_blastdb.pl`` utility
(bundled with NCBI BLAST+) and provides a simple CLI.

Supported databases
-------------------
  nt               Nucleotide collection (GenBank/EMBL/DDBJ) — general purpose
  16S_ribosomal_RNA  Ribosomal RNA database (bacteria / archaea)
  ITS_RefSeq_Fungi   ITS sequences (fungi / plants) — good for mycology eDNA
  silva138_ssu     SILVA 138 SSU (small-subunit rRNA) — eukaryote-friendly
                   NOTE: SILVA must be downloaded manually from
                   https://www.arb-silva.de/download/arb-files/

Usage examples
--------------
    # Download NCBI nt database to /data/blast/ (large — ~300 GB compressed)
    python scripts/setup_db.py --db nt --dest /data/blast/

    # 16S only (much smaller — ~1 GB):
    python scripts/setup_db.py --db 16S_ribosomal_RNA --dest /data/blast/

    # Check what is already installed:
    python scripts/setup_db.py --list --dest /data/blast/

Prerequisites
-------------
  BLAST+ installed:
    Ubuntu: sudo apt-get install ncbi-blast+
    macOS:  brew install blast
    Codespaces / devcontainer: already installed
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# NCBI-hosted databases available via update_blastdb.pl
AVAILABLE_DBS = {
    "nt":                  "Nucleotide collection (all GenBank/EMBL/DDBJ) ~300 GB",
    "16S_ribosomal_RNA":   "16S ribosomal RNA sequences (~1 GB, bacteria/archaea)",
    "ITS_RefSeq_Fungi":    "ITS RefSeq fungi sequences (~300 MB)",
    "18S_fungal_sequences":"18S fungal sequences",
    "28S_fungal_sequences":"28S fungal sequences",
    "ITS_eukaryote_sequences": "ITS sequences for eukaryotes (~800 MB)",
}


def _require_binary(name: str) -> Path:
    path = shutil.which(name)
    if path is None:
        log.error(
            f"'{name}' not found on PATH.\n"
            "Install BLAST+:\n"
            "  Ubuntu: sudo apt-get install ncbi-blast+\n"
            "  macOS:  brew install blast\n"
            "  Codespaces: open project in devcontainer (already installed)"
        )
        sys.exit(1)
    return Path(path)


def list_installed(dest: Path) -> None:
    blastdbcmd = _require_binary("blastdbcmd")
    log.info(f"Scanning {dest} for installed BLAST databases ...")
    found = False
    for db_file in sorted(dest.glob("*.nsq")) + sorted(dest.glob("*.nal")):
        db_path = dest / db_file.stem
        try:
            result = subprocess.run(
                [str(blastdbcmd), "-db", str(db_path), "-info"],
                capture_output=True, text=True, timeout=10,
            )
            title_line = next(
                (ln.strip() for ln in result.stdout.splitlines() if "Database:" in ln),
                str(db_path)
            )
            log.info(f"  FOUND  {title_line}")
            found = True
        except Exception:  # noqa: BLE001
            pass
    if not found:
        log.info(f"  No BLAST databases found in {dest}.")
        log.info("  Run: python scripts/setup_db.py --db 16S_ribosomal_RNA --dest <path>")


def download_ncbi_db(db: str, dest: Path, decompress: bool = True) -> None:
    """Use update_blastdb.pl to download and decompress an NCBI BLAST database."""
    update_script = shutil.which("update_blastdb.pl")
    if update_script is None:
        # Fallback: try running as a perl script
        perl = shutil.which("perl")
        if perl is None:
            log.error(
                "update_blastdb.pl not found.  "
                "It is bundled with BLAST+ — make sure BLAST+ is installed "
                "and that its bin/ directory is on PATH."
            )
            sys.exit(1)

    dest.mkdir(parents=True, exist_ok=True)

    cmd = [
        "update_blastdb.pl",
        "--decompress" if decompress else "--no-decompress",
        "--blastdb_version", "5",
        db,
    ]

    log.info(f"Downloading '{db}' database to {dest} ...")
    log.info("  This can take from minutes (small dbs) to hours (nt).")
    log.info(f"  Command: {' '.join(cmd)}")

    try:
        proc = subprocess.run(
            cmd, cwd=str(dest),
            capture_output=False,   # stream output so user sees progress
            timeout=7200,           # 2-hour max
        )
    except subprocess.TimeoutExpired:
        log.error("Download timed out after 2 hours.  Try again or use a faster connection.")
        sys.exit(1)
    except FileNotFoundError:
        log.error(
            "update_blastdb.pl not found.  "
            "It is bundled with NCBI BLAST+ — ensure blast/bin/ is on PATH."
        )
        sys.exit(1)

    if proc.returncode != 0:
        log.error(f"update_blastdb.pl exited with code {proc.returncode}.")
        sys.exit(1)

    log.info(f"Database '{db}' downloaded to {dest}.")

    # Write a provenance file
    prov = {
        "database": db,
        "destination": str(dest),
        "db_path": str(dest / db),
        "downloaded_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }
    prov_file = dest / f"{db}_setup.json"
    prov_file.write_text(json.dumps(prov, indent=2), encoding="utf-8")
    log.info(f"Provenance written -> {prov_file}")
    log.info("")
    log.info("Ready to use:")
    log.info(f"  python pipeline.py --fasta data/sample_sequences.fasta \\")
    log.info(f"      --local --db-path {dest / db} --threads 4")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and prepare a local BLAST+ database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(
            f"  {name:<30} {desc}" for name, desc in AVAILABLE_DBS.items()
        ),
    )
    parser.add_argument(
        "--db", choices=list(AVAILABLE_DBS.keys()),
        help="BLAST database to download",
    )
    parser.add_argument(
        "--dest", default="/data/blast",
        help="Directory to store the database files",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List databases already installed in --dest",
    )
    parser.add_argument(
        "--no-decompress", action="store_true",
        help="Keep .tar.gz files without decompressing (saves time, uses less disk)",
    )
    args = parser.parse_args()

    dest = Path(args.dest)

    if args.list:
        list_installed(dest)
        return

    if not args.db:
        parser.print_help()
        log.error("\nSpecify --db <name> or --list")
        sys.exit(1)

    download_ncbi_db(args.db, dest, decompress=not args.no_decompress)


if __name__ == "__main__":
    main()
