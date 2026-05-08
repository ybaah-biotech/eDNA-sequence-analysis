"""Build species hit table, compute biodiversity metrics, and export results."""

import logging
import math
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.parser import BlastHit

log = logging.getLogger(__name__)


def build_hit_table(hits: List[BlastHit], top_hit_only: bool = False) -> pd.DataFrame:
    """
    Convert BlastHit records to a tidy DataFrame.

    Columns: query_id, query_length, hit_rank, accession, species,
             description, identity_pct, evalue, bit_score,
             alignment_length, query_coverage_pct.
    """
    if not hits:
        log.warning("No hits to build table from — check e-value threshold or BLAST results.")
        return pd.DataFrame()

    df = pd.DataFrame([vars(h) for h in hits])

    if top_hit_only:
        df = df[df["hit_rank"] == 1].copy()

    return df.sort_values(["query_id", "hit_rank"]).reset_index(drop=True)


def calculate_diversity(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute alpha-diversity metrics from BLAST top hits.

    Uses rank-1 hits only (one identification per query sequence) to
    avoid inflating species counts when multiple hits point to the same taxon.

    Metrics returned
    ----------------
    species_richness        : number of distinct species identified
    shannon_index           : Shannon–Wiener H' = -Σ p_i · ln(p_i)
    pielou_evenness         : J' = H' / ln(S); 1.0 = perfectly even community
    total_queries_with_hit  : number of queries that yielded a passing hit
    species_counts          : {species: count} for top-hit identifications
    """
    if df.empty:
        return {
            "species_richness": 0,
            "shannon_index": 0.0,
            "pielou_evenness": 0.0,
            "total_queries_with_hit": 0,
            "species_counts": {},
        }

    top_hits = df[df["hit_rank"] == 1]
    species_counts: Dict[str, int] = top_hits["species"].value_counts().to_dict()
    n_total = sum(species_counts.values())
    richness = len(species_counts)

    shannon = 0.0
    if n_total > 0:
        for count in species_counts.values():
            p = count / n_total
            if p > 0:
                shannon -= p * math.log(p)

    evenness = (shannon / math.log(richness)) if richness > 1 else 1.0

    return {
        "species_richness": richness,
        "shannon_index": round(shannon, 4),
        "pielou_evenness": round(evenness, 4),
        "total_queries_with_hit": n_total,
        "species_counts": species_counts,
    }


def export_results(
    df: pd.DataFrame,
    diversity: Dict[str, Any],
    output_dir: Path,
) -> None:
    """Write blast_hit_table.csv and biodiversity_summary.csv to output_dir."""
    hit_table_path = output_dir / "blast_hit_table.csv"
    df.to_csv(hit_table_path, index=False)
    log.info(f"Hit table -> {hit_table_path} ({len(df)} rows)")

    summary_rows = [
        {"metric": "species_richness",       "value": diversity["species_richness"]},
        {"metric": "shannon_index_H",        "value": diversity["shannon_index"]},
        {"metric": "pielou_evenness_J",      "value": diversity["pielou_evenness"]},
        {"metric": "total_queries_with_hit", "value": diversity["total_queries_with_hit"]},
    ]
    for species, count in diversity["species_counts"].items():
        key = f"count_{species.replace(' ', '_')}"
        summary_rows.append({"metric": key, "value": count})

    summary_df = pd.DataFrame(summary_rows)
    summary_path = output_dir / "biodiversity_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    log.info(f"Biodiversity summary -> {summary_path}")
