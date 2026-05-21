"""Parse BLAST XML result files into structured BlastHit records."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

from Bio.Blast import NCBIXML

log = logging.getLogger(__name__)

# Database source prefixes that appear in BLAST titles and are not organism names.
_ACCESSION_PREFIXES = frozenset({
    "gb", "emb", "dbj", "ref", "sp", "pir", "prf", "pdb",
    "tpg", "tpe", "tpd",
})

# Taxonomic qualifiers that appear between genus and species epithet.
# Returning these as the epithet produces nonsense names like "Alternaria cf"
# or "Betula var". They are skipped so the real epithet is found instead.
# "x" handles hybrid notation written as lowercase x (formal = ×).
_SKIP_QUALIFIERS = frozenset({
    "cf", "aff", "var", "subsp", "ssp", "f", "fo", "nov", "sp", "x",
})

# Common BLAST title descriptor words that follow the species name.
# Encountering one of these while scanning for an epithet means the
# species epithet was absent — stop and return genus-level only.
# Without this, words like "clone" or "isolate" are mistaken for epithets.
_STOP_WORDS = frozenset({
    "clone", "isolate", "strain", "voucher", "specimen", "culture",
    "sequence", "partial", "complete", "region", "gene", "rrna",
    "rdna", "spacer", "ribosomal", "transcribed", "barcode",
    "marker", "locus", "fragment", "type", "sample", "hybrid",
})

# Tokens that, when found as a candidate genus, indicate an environmental or
# unclassified sequence. These must not be returned as species names.
_NON_SPECIFIC_TERMS = frozenset({
    "uncultured", "unidentified", "environmental", "metagenome",
    "unknown", "synthetic", "artificial",
})

# Bracket-enclosed phrases that are not useful species names.
_NON_SPECIFIC_BRACKETS = frozenset({
    "environmental sample", "metagenome", "eukaryote",
    "unidentified", "unknown organism",
})


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

    Handles common formats:
      'gb|AJ312462.1| Betula pendula isolate BET1 ...'
      'Alternaria cf. alternata strain CBS ...'
      'mRNA partial sequence [Quercus robur]'
      'Populus × canadensis clone ...'
      'uncultured Chlamydomonas sp. clone ENV45 [freshwater metagenome]'

    Uncultured rescue: if a title is prefixed with 'uncultured' but contains
    a recognisable genus name (e.g. 'uncultured Chlorella sp.'), the genus is
    extracted and returned as 'Genus sp.' rather than discarding the hit as
    'unclassified'. This preserves genus-level signal from environmental entries.

    BLAST titles concatenate multiple database records separated by '>'.
    Only the first record is used to prevent cross-contamination.
    """
    # Use only the first record — BLAST titles may join multiple hits with '>'
    first_record = title.split(">")[0]

    # Normalise: replace pipe delimiters and hybrid × marker with spaces
    clean_title = first_record.replace("|", " ").replace("×", " ")
    tokens = clean_title.split()

    for i, token in enumerate(tokens):
        clean = token.rstrip(",;.()")
        if not (
            len(clean) > 2
            and clean[0].isupper()
            and clean.isalpha()
            and clean.lower() not in _ACCESSION_PREFIXES
            and clean.lower() not in _NON_SPECIFIC_TERMS
        ):
            continue

        genus = clean
        j = i + 1
        while j < len(tokens):
            epithet_raw = tokens[j].rstrip(",;.()")
            epithet_lower = epithet_raw.lower()
            # Skip taxonomic qualifiers (cf., aff., var., etc.) and keep looking
            if epithet_lower in _SKIP_QUALIFIERS:
                j += 1
                continue
            # Descriptor word encountered — species epithet is absent
            if epithet_lower in _STOP_WORDS:
                break
            if epithet_raw and epithet_raw[0].islower() and epithet_raw.isalpha():
                return f"{genus} {epithet_raw}"
            break

        # Genus resolved but epithet absent — sp. is the correct notation
        return f"{genus} sp."

    # Fallback: organism name inside square brackets (e.g. "mRNA ... [Quercus robur]")
    if "[" in first_record and "]" in first_record:
        bracket = first_record[first_record.rfind("[") + 1 : first_record.rfind("]")]
        if bracket.lower() not in _NON_SPECIFIC_BRACKETS:
            return bracket

    return "unclassified"


def parse_blast_xml(
    xml_path: Path,
    max_hits: int = 5,
    evalue_threshold: float = 1e-10,
) -> List[BlastHit]:
    """
    Parse a single BLAST XML file.

    Returns one BlastHit per alignment (up to max_hits) that passes the
    evalue_threshold filter, using the highest-scoring HSP for each alignment.
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

            # Select best HSP by bit score — BLAST XML does not guarantee ordering
            hsp = max(alignment.hsps, key=lambda h: h.bits)

            if hsp.expect > evalue_threshold:
                continue

            # Guard against degenerate zero-length alignments
            if hsp.align_length == 0 or query_length == 0:
                log.warning(
                    f"{xml_path.name}: skipping zero-length alignment for {query_id}"
                )
                continue

            rank += 1
            identity_pct = round(hsp.identities / hsp.align_length * 100, 2)
            # Clamp to 100 — subject insertions can push align_length > query_length
            coverage_pct = min(round(hsp.align_length / query_length * 100, 2), 100.0)

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
