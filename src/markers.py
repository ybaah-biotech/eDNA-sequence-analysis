"""
src/markers.py — Multi-marker support for the eDNA pipeline (Phase 5).

A single eDNA survey often amplifies several gene markers from the same water
sample (e.g. 16S for bacteria, COI for invertebrates, 12S for fish). Each
marker must be searched against its own reference database, and diversity must
be reported per marker — you never mix bacterial 16S and animal COI into one
community metric.

This module provides the marker-aware layer:

  * ``detect_marker``            — read the marker from a query-ID prefix
  * ``add_marker_column``        — tag a hit table with its marker per row
  * ``split_sequences_by_marker``— group input sequences for per-marker BLAST
  * ``calculate_diversity_by_marker`` — per-marker alpha diversity

Marker convention
-----------------
Sequences are tagged by a prefix on the FASTA query ID, delimited by the first
underscore::

    16S_pondA_001     -> 16S
    COI_pondA_002     -> COI
    12S_fish_07       -> 12S
    ITS2_sample3      -> ITS2
    seq_001           -> unknown   (no recognised marker prefix)

Detection is case-insensitive: ``coi_x`` resolves to ``COI``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import pandas as pd
from Bio.SeqRecord import SeqRecord

from src.summarise import calculate_diversity

log = logging.getLogger(__name__)

__all__ = [
    "SUPPORTED_MARKERS",
    "UNKNOWN_MARKER",
    "detect_marker",
    "add_marker_column",
    "split_sequences_by_marker",
    "calculate_diversity_by_marker",
    "marker_summary_frame",
]

# Canonical marker vocabulary — kept in step with src/databases.py routing.
SUPPORTED_MARKERS: frozenset[str] = frozenset(
    {"16S", "18S", "12S", "COI", "ITS", "ITS1", "ITS2"}
)

UNKNOWN_MARKER = "unknown"

# Case-insensitive lookup: normalised token -> canonical marker name.
_CANONICAL: Dict[str, str] = {m.upper(): m for m in SUPPORTED_MARKERS}


def detect_marker(query_id: str) -> str:
    """
    Return the gene marker encoded in *query_id*, or ``"unknown"``.

    The marker is the substring before the first underscore, matched
    case-insensitively against :data:`SUPPORTED_MARKERS`.

    Examples
    --------
    >>> detect_marker("16S_pondA_001")
    '16S'
    >>> detect_marker("coi_seq3")
    'COI'
    >>> detect_marker("seq_001")
    'unknown'
    >>> detect_marker("16S")          # no underscore -> no marker prefix
    'unknown'
    """
    if not query_id or "_" not in query_id:
        return UNKNOWN_MARKER
    prefix = query_id.split("_", 1)[0].upper()
    return _CANONICAL.get(prefix, UNKNOWN_MARKER)


def add_marker_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a copy of *df* with a ``marker`` column derived from ``query_id``.

    Safe on an empty DataFrame (adds an empty ``marker`` column of dtype str).
    """
    df = df.copy()
    if df.empty:
        df["marker"] = pd.Series(dtype=str)
        return df
    df["marker"] = df["query_id"].apply(detect_marker)
    return df


def split_sequences_by_marker(
    sequences: Dict[str, SeqRecord],
) -> Dict[str, Dict[str, SeqRecord]]:
    """
    Group ``{query_id: SeqRecord}`` into ``{marker: {query_id: SeqRecord}}``.

    Each marker group is routed to its own BLAST database by the pipeline.
    Sequences whose ID carries no recognised marker prefix are collected under
    the ``"unknown"`` key so they are never silently dropped.
    """
    grouped: Dict[str, Dict[str, SeqRecord]] = {}
    for query_id, record in sequences.items():
        marker = detect_marker(query_id)
        grouped.setdefault(marker, {})[query_id] = record

    if grouped:
        summary = ", ".join(
            f"{m}: {len(seqs)}" for m, seqs in sorted(grouped.items())
        )
        log.info(f"Sequences split by marker — {summary}")
    return grouped


def calculate_diversity_by_marker(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Compute alpha diversity separately for each marker in *df*.

    Returns ``{marker: diversity_dict}`` where each value matches the schema
    of :func:`src.summarise.calculate_diversity`. The hit table must already
    carry a ``marker`` column (see :func:`add_marker_column`); if it does not,
    the column is added automatically.

    Diversity is never pooled across markers — bacterial 16S richness and
    animal COI richness describe different communities and are reported apart.
    """
    if df.empty:
        return {}
    if "marker" not in df.columns:
        df = add_marker_column(df)

    per_marker: Dict[str, Dict[str, Any]] = {}
    for marker, group in df.groupby("marker", sort=True):
        per_marker[str(marker)] = calculate_diversity(group)
    return per_marker


def marker_summary_frame(
    marker_diversity: Dict[str, Dict[str, Any]],
) -> pd.DataFrame:
    """
    Flatten ``{marker: diversity_dict}`` into a tidy summary DataFrame.

    One row per marker with columns: marker, total_queries_with_hit,
    species_richness, shannon_index_H, pielou_evenness_J, unclassified_queries.
    Suitable for writing to ``marker_summary.csv`` and for the PDF report.
    """
    rows = []
    for marker, d in sorted(marker_diversity.items()):
        rows.append({
            "marker": marker,
            "total_queries_with_hit": d.get("total_queries_with_hit", 0),
            "species_richness": d.get("species_richness", 0),
            "shannon_index_H": d.get("shannon_index", 0.0),
            "pielou_evenness_J": d.get("pielou_evenness", 0.0),
            "unclassified_queries": d.get("unclassified_queries", 0),
        })
    return pd.DataFrame(rows)
