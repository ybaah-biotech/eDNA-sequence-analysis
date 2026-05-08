"""Shared utilities: FASTA loading, logging setup, directory helpers."""

import logging
import sys
from pathlib import Path
from typing import Dict

from Bio import SeqIO
from Bio.SeqRecord import SeqRecord


def load_fasta(filepath: str) -> Dict[str, SeqRecord]:
    """Return {seq_id: SeqRecord} dict from a FASTA file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {filepath}")

    records: Dict[str, SeqRecord] = {}
    for record in SeqIO.parse(str(path), "fasta"):
        records[record.id] = record

    if not records:
        raise ValueError(f"No sequences found in {filepath}")
    return records


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def ensure_dir(path: Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)
