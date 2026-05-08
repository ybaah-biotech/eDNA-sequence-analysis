"""Parse BLAST XML result files into structured BlastHit records."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

from Bio.Blast import NCBIXML

log = logging.getLogger(__name__)


@dataclass
class BlastHit:
    query_id: str
    query_length: int
    hit_rank: int
    accession: str
    species: str
    description: str
    identity_pct: float
    evalue: float
    bit_score: float
    alignment_length: int
    query_coverage_pct: float


def _extract_species(title: str) -> str:
    """
    Pull 'Genus species' from a BLAST hit title.

    Handles formats like:
      'gb|AJ312462.1| Betula pendula isolate BET1 ...'
      'Alternaria alternata strain CBS voucher ...'
      'mRNA partial sequence [Quercus robur]'
    """
    accession_prefixes = {"gb", "emb", "dbj", "ref", "sp", "pir", "prf", "pdb", "tpg", "tpe", "tpd"}
    tokens = title.replace("|", " ").split()
    for i, token in enumerate(tokens):
        clean = token.rstrip(",;.")
        # A genuine genus name is purely alphabetic (no digits, no dots),
        # starts with a capital, and is not a database prefix.
        if (
            len(clean) > 2
            and clean[0].isupper()
            and clean.isalpha()
            and clean.lower() not in accession_prefixes
        ):
            genus = clean
            if i + 1 < len(tokens):
                epithet = tokens[i + 1].rstrip(",;.")
                if epithet and epithet[0].islower() and epithet.isalpha():
                    return f"{genus} {epithet}"
            return genus

    # Fallback: organism name inside square brackets
    if "[" in title and "]" in title:
        return title[title.rfind("[") + 1 : title.rfind("]")]

    return title.split()[0]


def parse_blast_xml(
    xml_path: Path,
    max_hits: int = 5,
    evalue_threshold: float = 1e-10,
) -> List[BlastHit]:
    """
    Parse a single BLAST XML file.

    Returns one BlastHit per alignment (up to max_hits) that passes the
    evalue_threshold filter, using the top HSP for each alignment.
    """
    hits: List[BlastHit] = []
    blast_records: List = []

    with open(xml_path, encoding="utf-8") as fh:
        try:
            for record in NCBIXML.parse(fh):
                blast_records.append(record)
        except ValueError as exc:
            # Biopython's SAX-based parser signals end-of-stream via
            # ValueError("parsing finished") in some versions; this is
            # normal — any records collected before the signal are valid.
            if "parsing finished" not in str(exc):
                log.warning(f"Could not parse {xml_path.name}: {exc}")
                return hits
        except Exception as exc:
            log.warning(f"Could not parse {xml_path.name}: {exc}")
            return hits

    for record in blast_records:
        query_id = record.query.split()[0]
        query_length = record.query_length
        rank = 0

        for alignment in record.alignments:
            if rank >= max_hits:
                break

            hsp = alignment.hsps[0]  # best HSP for this subject sequence
            if hsp.expect > evalue_threshold:
                continue

            rank += 1
            identity_pct = round(hsp.identities / hsp.align_length * 100, 2)
            coverage_pct = round(hsp.align_length / query_length * 100, 2)

            hits.append(
                BlastHit(
                    query_id=query_id,
                    query_length=query_length,
                    hit_rank=rank,
                    accession=alignment.accession,
                    species=_extract_species(alignment.title),
                    description=alignment.title[:150],
                    identity_pct=identity_pct,
                    evalue=hsp.expect,
                    bit_score=round(hsp.bits, 1),
                    alignment_length=hsp.align_length,
                    query_coverage_pct=coverage_pct,
                )
            )

    return hits


def parse_all_results(
    xml_dir: Path,
    max_hits: int = 5,
    evalue_threshold: float = 1e-10,
) -> List[BlastHit]:
    """Parse every *.xml file in xml_dir and concatenate results."""
    xml_files = sorted(xml_dir.glob("*.xml"))
    if not xml_files:
        raise FileNotFoundError(f"No XML result files in {xml_dir}")

    all_hits: List[BlastHit] = []
    for xml_path in xml_files:
        hits = parse_blast_xml(xml_path, max_hits=max_hits, evalue_threshold=evalue_threshold)
        log.info(f"{xml_path.stem}: {len(hits)} hits (threshold e≤{evalue_threshold})")
        all_hits.extend(hits)

    return all_hits
