"""Build species hit table, compute biodiversity metrics, and export results."""

import logging
import math
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.parser import BlastHit

log = logging.getLogger(__name__)

# Identity thresholds for species-level confidence, following standard
# barcoding convention (e.g. ITS2 / 16S / 18S):
#   ≥97 % → species-level assignment reliable
#   ≥90 % → genus-level reliable, species uncertain
#   < 90 % → alignment too divergent for reliable taxonomic placement
_CONF_HIGH = 97.0
_CONF_MED  = 90.0


def resolve_taxonomy(df: pd.DataFrame, lca_identity_gap: float = 2.0) -> pd.DataFrame:
    """
    Add a resolved_species column using Lowest Common Ancestor (LCA) logic
    across multiple BLAST hits per query, combined with identity-based
    taxonomic level downgrading.

    Rules applied per query
    -----------------------
    ≥97 % identity on rank-1 hit
        Accept the species name directly — the match is strong enough for
        species-level placement.

    90–96 % identity (medium confidence)
        Examine all hits within lca_identity_gap % of the top score.
        If they all agree on genus → return 'Genus sp.'
        A single species name is not trusted at this identity level
        because it may represent a different species in the same genus.

    <90 % identity (low confidence)
        Examine all hits for the query.
        If all agree on genus → return 'Genus sp.'
        If genera disagree → return 'unclassified'.
        The alignment is too divergent to trust even the genus from a
        single hit alone.

    Parameters
    ----------
    df              : DataFrame from build_hit_table (before top_hit_only filter)
    lca_identity_gap: hits within this many % of the top score are included
                      in the LCA window for medium-confidence queries
    """
    df = df.copy()
    resolved_rows: List[pd.DataFrame] = []

    for query_id, group in df.groupby("query_id", sort=False):
        group = group.sort_values("hit_rank").copy()
        top = group.iloc[0]
        top_identity: float = top["identity_pct"]
        top_species: str   = top["species"]

        if top_identity >= _CONF_HIGH and top_species != "unclassified":
            # Strong match — trust the species name from the top hit
            resolved = top_species

        elif top_identity >= _CONF_MED:
            # Medium confidence — check genus consensus within the identity window
            window = group[group["identity_pct"] >= top_identity - lca_identity_gap]
            classified_species = [
                s for s in window["species"].tolist() if s != "unclassified"
            ]
            genera = {s.split()[0] for s in classified_species if s.split()}

            if len(genera) == 1:
                resolved = f"{next(iter(genera))} sp."
            elif top_species != "unclassified" and top_species.split():
                # No genus consensus — downgrade rank-1 to genus level
                resolved = f"{top_species.split()[0]} sp."
            else:
                resolved = "unclassified"

        else:
            # Low confidence — require genus consensus across all hits
            classified_species = [
                s for s in group["species"].tolist() if s != "unclassified"
            ]
            genera = {s.split()[0] for s in classified_species if s.split()}

            if len(genera) == 1:
                resolved = f"{next(iter(genera))} sp."
            else:
                resolved = "unclassified"

        group["resolved_species"] = resolved
        resolved_rows.append(group)

    if resolved_rows:
        return (
            pd.concat(resolved_rows)
            .sort_values(["query_id", "hit_rank"])
            .reset_index(drop=True)
        )

    # Edge case: empty DataFrame
    return df.assign(resolved_species=pd.Series(dtype=str))


def build_hit_table(hits: List[BlastHit], top_hit_only: bool = False) -> pd.DataFrame:
    """
    Convert BlastHit records to a tidy DataFrame.

    Columns: query_id, query_length, hit_rank, accession, species,
             description, identity_pct, evalue, bit_score,
             alignment_length, query_coverage_pct, confidence_flag,
             resolved_species.

    resolved_species is the biologically honest classification after LCA
    and identity-based downgrading. Use this column for diversity analyses.
    species is the raw name extracted from the BLAST title and is preserved
    for reference and audit.
    """
    if not hits:
        log.warning("No hits to build table from — check e-value threshold or BLAST results.")
        return pd.DataFrame()

    df = pd.DataFrame([vars(h) for h in hits])

    # Confidence flag based on identity percentage
    df["confidence_flag"] = df["identity_pct"].apply(
        lambda x: "high" if x >= _CONF_HIGH else ("medium" if x >= _CONF_MED else "low")
    )

    # Apply LCA + identity downgrading across all hits before any filtering
    df = resolve_taxonomy(df)

    if top_hit_only:
        df = df[df["hit_rank"] == 1].copy()

    return df.sort_values(["query_id", "hit_rank"]).reset_index(drop=True)


def calculate_diversity(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute alpha-diversity metrics from BLAST top hits.

    Uses rank-1 hits and the resolved_species column (falling back to species
    if resolved_species is not present). Sequences resolved to 'unclassified'
    are excluded from diversity metrics but counted separately so sample
    coverage remains transparent.

    Metrics returned
    ----------------
    species_richness        : number of distinct classified taxa
    shannon_index           : Shannon–Wiener H' = -Σ p_i · ln(p_i)
    pielou_evenness         : J' = H' / ln(S); 1.0 = perfectly even community
    total_queries_with_hit  : classified queries used in diversity calculation
    unclassified_queries    : queries that could not be assigned to any taxon
    species_counts          : {taxon: count} for classified top-hit identifications
    """
    empty: Dict[str, Any] = {
        "species_richness": 0,
        "shannon_index": 0.0,
        "pielou_evenness": 0.0,
        "total_queries_with_hit": 0,
        "unclassified_queries": 0,
        "species_counts": {},
    }
    if df.empty:
        return empty

    # Prefer resolved_species (post-LCA) over raw species
    species_col = "resolved_species" if "resolved_species" in df.columns else "species"

    top_hits = df[df["hit_rank"] == 1]

    # Separate unclassified — real sequences but no meaningful taxonomic signal
    classified = top_hits[top_hits[species_col] != "unclassified"]
    n_unclassified = len(top_hits) - len(classified)

    if classified.empty:
        log.warning("All top hits are unclassified — diversity metrics cannot be computed.")
        empty["unclassified_queries"] = n_unclassified
        return empty

    species_counts: Dict[str, int] = classified[species_col].value_counts().to_dict()
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
        "unclassified_queries": n_unclassified,
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
        {"metric": "unclassified_queries",   "value": diversity["unclassified_queries"]},
    ]
    for species, count in diversity["species_counts"].items():
        key = f"count_{species.replace(' ', '_')}"
        summary_rows.append({"metric": key, "value": count})

    summary_df = pd.DataFrame(summary_rows)
    summary_path = output_dir / "biodiversity_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    log.info(f"Biodiversity summary -> {summary_path}")
