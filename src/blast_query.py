"""NCBI BLAST querying with result caching and polite rate-limiting."""

import logging
import time
from pathlib import Path
from typing import Dict

from Bio import Entrez
from Bio.Blast import NCBIWWW
from Bio.SeqRecord import SeqRecord

log = logging.getLogger(__name__)

# NCBI enforces ≤3 requests/sec with an API key; ≤1/sec without.
# 3 s is conservative and avoids any risk of being blocked.
_NCBI_REQUEST_INTERVAL = 3.0


def run_blast_queries(
    sequences: Dict[str, SeqRecord],
    xml_dir: Path,
    email: str,
    db: str = "nt",
    program: str = "blastn",
    evalue: float = 1e-10,
    hitlist_size: int = 20,
) -> None:
    """
    Submit NCBI BLAST queries for each sequence and cache results as XML.

    Skips any query whose XML file already exists and is non-empty, so
    re-running the pipeline never incurs redundant network calls.

    Parameters
    ----------
    sequences:    {query_id: SeqRecord} dict from load_fasta()
    xml_dir:      directory where per-query XML files are written
    email:        registered email (required by NCBI Entrez policy)
    db:           BLAST database (default: 'nt')
    program:      BLAST program (default: 'blastn')
    evalue:       e-value cutoff passed to NCBI
    hitlist_size: max alignments returned per query
    """
    Entrez.email = email

    total = len(sequences)
    for idx, (query_id, record) in enumerate(sequences.items(), start=1):
        xml_path = xml_dir / f"{query_id}.xml"

        if xml_path.exists() and xml_path.stat().st_size > 0:
            log.info(f"[{idx}/{total}] {query_id} — cached result found, skipping BLAST call")
            continue

        log.info(
            f"[{idx}/{total}] {query_id} — querying NCBI BLAST "
            f"(program={program}, db={db}). This may take 30-120 s ..."
        )

        try:
            result_handle = NCBIWWW.qblast(
                program=program,
                database=db,
                sequence=record.format("fasta"),
                hitlist_size=hitlist_size,
                expect=evalue,
            )
            xml_content = result_handle.read()
            result_handle.close()
        except Exception as exc:
            log.error(f"[{query_id}] BLAST query failed: {exc}")
            raise

        xml_path.write_text(xml_content, encoding="utf-8")
        log.info(f"[{query_id}] Saved {len(xml_content):,} bytes -> {xml_path.name}")

        if idx < total:
            time.sleep(_NCBI_REQUEST_INTERVAL)
