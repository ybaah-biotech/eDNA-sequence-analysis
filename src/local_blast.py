"""
Local BLAST+ execution via subprocess.

Replaces NCBI web BLAST (src/blast_query.py) for offline / high-throughput
work. Key advantages over the web API:
  - No rate limits or internet dependency
  - Version-locked database → reproducible results
  - Multi-threaded: --threads N runs N queries in parallel
  - Identical caching contract: existing non-empty XML files are reused

Typical usage
-------------
    from src.local_blast import run_local_blast
    run_local_blast(
        sequences=sequences,
        xml_dir=xml_dir,
        db_path="/data/blast/nt",   # path to local nt database
        evalue=1e-10,
        max_hits=20,
        threads=4,
        version_file=output_dir / "db_version.json",
    )
"""

import json
import logging
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from Bio.SeqRecord import SeqRecord

log = logging.getLogger(__name__)

# Safety timeout per query — local BLAST on large databases can be slow
_BLAST_TIMEOUT_SEC = 300  # 5 minutes


# ── Installation check ────────────────────────────────────────────────────────

def _check_blast_installed(program: str = "blastn") -> Path:
    """
    Return the absolute path to the BLAST binary.

    Raises RuntimeError with actionable installation instructions if the
    binary is not found on PATH.
    """
    binary = shutil.which(program)
    if binary is None:
        raise RuntimeError(
            f"'{program}' not found on PATH.\n\n"
            "  Install BLAST+:\n"
            "    Ubuntu / Debian : sudo apt-get install ncbi-blast+\n"
            "    macOS (Homebrew): brew install blast\n"
            "    Windows         : https://www.ncbi.nlm.nih.gov/books/NBK153387/\n"
            "    GitHub Codespaces / devcontainer: already installed — "
            "open the project in the devcontainer (Ctrl+Shift+P → "
            "'Reopen in Container')."
        )
    return Path(binary)


# ── Database version stamping ─────────────────────────────────────────────────

def get_db_version(db_path: str) -> str:
    """
    Query a local BLAST database for its title and creation date.

    Returns a human-readable string — e.g.
        "Database: Nucleotide collection (nt)  Date: Feb 14, 2025  1:04 PM"

    Falls back to "unknown (...reason...)" if blastdbcmd is missing or errors.
    """
    blastdbcmd = shutil.which("blastdbcmd")
    if blastdbcmd is None:
        return "unknown (blastdbcmd not on PATH)"
    try:
        result = subprocess.run(
            [blastdbcmd, "-db", db_path, "-info"],
            capture_output=True, text=True, timeout=15,
        )
        lines = result.stdout.splitlines()
        # Collect title + date lines — they contain the most useful info
        useful = [
            ln.strip() for ln in lines
            if any(kw in ln for kw in ("Database:", "Date:", "sequences:", "total"))
        ]
        return " | ".join(useful[:4]) if useful else (result.stdout.strip()[:200] or "unknown")
    except subprocess.TimeoutExpired:
        return "unknown (blastdbcmd timed out)"
    except Exception as exc:  # noqa: BLE001
        return f"unknown ({exc})"


def stamp_db_version(db_path: str, program: str, version_file: Path) -> str:
    """
    Write a JSON file recording the database version and return the version string.

    The version file is stored alongside output CSVs so every results folder
    is self-documenting. Example content::

        {
          "db_path": "/data/blast/nt",
          "db_version": "Database: nt | Date: Feb 14, 2025",
          "program": "blastn",
          "stamped_at": "2026-05-22T09:00:00Z"
        }
    """
    db_ver = get_db_version(db_path)
    version_file.parent.mkdir(parents=True, exist_ok=True)
    version_file.write_text(
        json.dumps(
            {
                "db_path": str(db_path),
                "db_version": db_ver,
                "program": program,
                "stamped_at": datetime.utcnow().isoformat() + "Z",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    log.info(f"DB version stamp written -> {version_file}")
    return db_ver


# ── Single-query worker ───────────────────────────────────────────────────────

def _blast_single(
    query_id: str,
    record: SeqRecord,
    xml_path: Path,
    binary: Path,
    db_path: str,
    program: str,
    evalue: float,
    max_hits: int,
    idx: int,
    total: int,
) -> str:
    """
    Run a single BLAST query and write the XML result to *xml_path*.

    Returns *query_id* on success so futures can be mapped back to sequences.
    Raises RuntimeError on BLAST failure or timeout — the caller decides
    whether to abort the whole run or skip and continue.
    """
    if xml_path.exists() and xml_path.stat().st_size > 0:
        log.info(f"[{idx}/{total}] {query_id} — cached XML found, skipping")
        return query_id

    log.info(f"[{idx}/{total}] {query_id} — running local BLAST+ ...")

    # Pass the query as FASTA on stdin to avoid temp-file management
    fasta_input = f">{record.id}\n{str(record.seq)}\n"

    cmd = [
        str(binary),
        "-db",              db_path,
        "-query",           "-",         # read FASTA from stdin
        "-out",             str(xml_path),
        "-outfmt",          "5",         # BLAST XML
        "-evalue",          str(evalue),
        "-num_alignments",  str(max_hits),
        "-num_descriptions", str(max_hits),
    ]

    try:
        proc = subprocess.run(
            cmd,
            input=fasta_input,
            capture_output=True,
            text=True,
            timeout=_BLAST_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        xml_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"[{query_id}] BLAST timed out after {_BLAST_TIMEOUT_SEC} s. "
            "The database may be very large — try fewer sequences at a time "
            "or a smaller subset database (e.g. 16S_ribosomal_RNA)."
        )

    if proc.returncode != 0:
        xml_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"[{query_id}] {binary.name} exited with code {proc.returncode}.\n"
            f"stderr: {proc.stderr[:600]}\n"
            "Check that --db-path points to a valid, formatted BLAST database."
        )

    if not xml_path.exists() or xml_path.stat().st_size == 0:
        raise RuntimeError(
            f"[{query_id}] blastn ran but produced no XML output. "
            "Verify the database path and that it covers your sequence type."
        )

    log.info(
        f"[{idx}/{total}] {query_id} — "
        f"done ({xml_path.stat().st_size:,} bytes -> {xml_path.name})"
    )
    return query_id


# ── Public entry point ────────────────────────────────────────────────────────

def run_local_blast(
    sequences: Dict[str, SeqRecord],
    xml_dir: Path,
    db_path: str,
    program: str = "blastn",
    evalue: float = 1e-10,
    max_hits: int = 20,
    threads: int = 1,
    version_file: Optional[Path] = None,
) -> None:
    """
    Run local BLAST+ for every sequence and cache results as XML files.

    Mirrors the API of ``run_blast_queries()`` in blast_query.py so the
    pipeline can swap between web and local mode with a single flag.

    Parameters
    ----------
    sequences:
        ``{query_id: SeqRecord}`` dict from :func:`~src.utils.load_fasta`.
    xml_dir:
        Directory for per-query XML files.  Created if absent.
    db_path:
        Path to the local BLAST database **without** file extension
        (e.g. ``/data/blast/nt`` or ``/data/silva/SILVA_138_SSU``).
    program:
        BLAST binary to invoke (default ``blastn``).
    evalue:
        E-value threshold passed to BLAST.
    max_hits:
        Maximum alignments per query (``-num_alignments``).
    threads:
        Number of parallel workers.  Use 1 (default) for spinning hard
        drives; 4–8 is safe on SSDs and NVMe.
    version_file:
        Optional path for the JSON database-version stamp.  Written once
        before any queries so results folders are self-documenting.

    Raises
    ------
    RuntimeError
        If the BLAST binary is missing, a query fails, or the database
        cannot be found.
    """
    xml_dir.mkdir(parents=True, exist_ok=True)

    binary = _check_blast_installed(program)
    log.info(f"Local BLAST+ binary : {binary}")
    log.info(f"Database path       : {db_path}")

    # --- DB version stamp ------------------------------------------------
    if version_file is not None:
        db_ver = stamp_db_version(db_path, program, version_file)
    else:
        db_ver = get_db_version(db_path)
    log.info(f"Database version    : {db_ver}")

    # --- Run queries -------------------------------------------------------
    total = len(sequences)
    items = list(sequences.items())

    if threads <= 1:
        # Sequential — safe for all storage types
        for idx, (query_id, record) in enumerate(items, start=1):
            xml_path = xml_dir / f"{query_id}.xml"
            _blast_single(
                query_id, record, xml_path, binary,
                db_path, program, evalue, max_hits, idx, total,
            )
    else:
        # Parallel — thread-safe because each query writes its own file
        log.info(f"Running {threads} parallel BLAST workers ...")
        futures: dict = {}
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for idx, (query_id, record) in enumerate(items, start=1):
                xml_path = xml_dir / f"{query_id}.xml"
                fut = executor.submit(
                    _blast_single,
                    query_id, record, xml_path, binary,
                    db_path, program, evalue, max_hits, idx, total,
                )
                futures[fut] = query_id

            errors = []
            for fut in as_completed(futures):
                try:
                    fut.result()
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{futures[fut]}: {exc}")
                    log.error(f"Worker error — {futures[fut]}: {exc}")

        if errors:
            raise RuntimeError(
                f"{len(errors)} BLAST worker(s) failed:\n" + "\n".join(errors)
            )

    log.info(f"Local BLAST+ complete — {total} sequence(s) processed.")
