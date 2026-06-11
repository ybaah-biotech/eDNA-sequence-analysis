"""
src/rarefaction.py — Rarefaction and richness estimation (Phase 6).

eDNA samples are almost never sequenced to the same depth. A sample with more
reads finds more species simply because it had more chances to — not because
the water was richer. Comparing raw species counts across samples of different
depth is therefore biased. Rarefaction corrects this by asking a depth-fair
question: *how many species would we expect to see if every sample were
sequenced to the same number of reads?*

This module provides the analysis layer, operating on the ``species_counts``
mapping the pipeline already produces (``{taxon: read_count}``):

  * ``chao1``              — estimate true richness including unseen species
  * ``rarefaction_point``  — expected species at a given depth (analytical)
  * ``rarefaction_curve``  — expected species across a range of depths
  * ``rarefy_counts``      — stochastically subsample counts to a fixed depth
  * ``rarefied_diversity`` — Shannon/Pielou/richness on a rarefied sample

The curve and ``rarefaction_point`` use Hurlbert's analytical expectation,
which is exact and deterministic (no random seed needed). ``rarefy_counts``
draws a single random subsample and is used when you need an actual rarefied
count vector rather than an expectation.
"""

from __future__ import annotations

import logging
import math
import random
from typing import Any, Dict, List, Mapping, Tuple

log = logging.getLogger(__name__)

__all__ = [
    "chao1",
    "rarefaction_point",
    "rarefaction_curve",
    "rarefy_counts",
    "rarefied_diversity",
]


def chao1(species_counts: Mapping[str, int]) -> float:
    """
    Estimate true species richness (Chao1), including species present but
    not observed in the sample.

    Chao1 uses the number of rare species to estimate how many were missed:

        S_chao1 = S_obs + F1² / (2·F2)            (classic, when F2 > 0)
        S_chao1 = S_obs + F1·(F1−1) / (2·(F2+1))  (bias-corrected, when F2 = 0)

    where F1 = singletons (species seen once) and F2 = doubletons (seen twice).

    Returns ``S_obs`` unchanged when there are no singletons (nothing rare
    suggests undersampling). Always ``>= S_obs``.
    """
    counts = [c for c in species_counts.values() if c > 0]
    s_obs = len(counts)
    if s_obs == 0:
        return 0.0

    f1 = sum(1 for c in counts if c == 1)
    f2 = sum(1 for c in counts if c == 2)

    if f1 == 0:
        return float(s_obs)
    if f2 > 0:
        est = s_obs + (f1 * f1) / (2.0 * f2)
    else:
        # Bias-corrected form avoids division by zero when no doubletons exist
        est = s_obs + (f1 * (f1 - 1)) / (2.0 * (f2 + 1))
    return round(est, 4)


def rarefaction_point(species_counts: Mapping[str, int], depth: int) -> float:
    """
    Expected number of species in a random subsample of *depth* reads, using
    Hurlbert's analytical rarefaction:

        E(S_n) = Σ_i [ 1 − C(N − N_i, n) / C(N, n) ]

    where N is the total read count, N_i the count of species i, and n the
    subsample depth. Deterministic — no random draw involved.

    A depth of 0 yields 0.0; a depth at or beyond the total read count yields
    the full observed richness.
    """
    counts = [c for c in species_counts.values() if c > 0]
    total = sum(counts)
    if depth <= 0 or total == 0:
        return 0.0
    if depth >= total:
        return float(len(counts))

    # Probability a given species is ABSENT from the subsample, summed as
    # 1 − P(absent) to get its expected presence; sum over species.
    denom = math.comb(total, depth)
    expected = 0.0
    for n_i in counts:
        if total - n_i >= depth:
            p_absent = math.comb(total - n_i, depth) / denom
        else:
            p_absent = 0.0  # species cannot be wholly excluded at this depth
        expected += 1.0 - p_absent
    return round(expected, 4)


def rarefaction_curve(
    species_counts: Mapping[str, int],
    n_points: int = 20,
    max_depth: int | None = None,
) -> List[Tuple[int, float]]:
    """
    Build a rarefaction curve: ``[(depth, expected_species), ...]``.

    The curve runs from a small depth up to *max_depth* (default: the total
    read count) across roughly *n_points* evenly spaced depths. A curve that
    has plateaued indicates the sample was sequenced deeply enough; one still
    climbing indicates rare species remain undetected.
    """
    total = sum(c for c in species_counts.values() if c > 0)
    if total == 0:
        return []

    cap = total if max_depth is None else min(max_depth, total)
    n_points = max(1, n_points)
    step = max(1, cap // n_points)

    depths = list(range(step, cap + 1, step))
    if not depths or depths[-1] != cap:
        depths.append(cap)

    return [(d, rarefaction_point(species_counts, d)) for d in depths]


def rarefy_counts(
    species_counts: Mapping[str, int],
    depth: int,
    seed: int | None = None,
) -> Dict[str, int]:
    """
    Randomly subsample *species_counts* down to *depth* total reads, without
    replacement, returning a new ``{taxon: count}`` mapping (species that fall
    to zero are dropped).

    Unlike :func:`rarefaction_point` (an expectation), this returns one
    concrete realised draw — used when a rarefied count vector is needed for
    downstream diversity. Pass *seed* for reproducibility.

    If *depth* is at or above the total, the counts are returned unchanged.
    """
    counts = {k: v for k, v in species_counts.items() if v > 0}
    total = sum(counts.values())
    if depth <= 0:
        return {}
    if depth >= total:
        return dict(counts)

    # Build an urn of taxon labels, draw *depth* without replacement
    rng = random.Random(seed)
    urn: List[str] = []
    for taxon, c in counts.items():
        urn.extend([taxon] * c)
    drawn = rng.sample(urn, depth)

    rarefied: Dict[str, int] = {}
    for taxon in drawn:
        rarefied[taxon] = rarefied.get(taxon, 0) + 1
    return rarefied


def rarefied_diversity(
    species_counts: Mapping[str, int],
    depth: int,
    seed: int | None = None,
) -> Dict[str, Any]:
    """
    Subsample to *depth* and recompute alpha diversity on the rarefied counts.

    Returns a dict mirroring :func:`src.summarise.calculate_diversity` but
    derived from the rarefied sample, plus the realised ``rarefaction_depth``
    and analytical ``expected_richness`` at that depth:

        species_richness, shannon_index, pielou_evenness,
        total_queries_with_hit, species_counts,
        rarefaction_depth, expected_richness
    """
    rarefied = rarefy_counts(species_counts, depth, seed=seed)

    n_total = sum(rarefied.values())
    richness = len(rarefied)

    shannon = 0.0
    for c in rarefied.values():
        p = c / n_total if n_total else 0.0
        if p > 0:
            shannon -= p * math.log(p)
    evenness = (shannon / math.log(richness)) if richness > 1 else (1.0 if richness == 1 else 0.0)

    return {
        "species_richness": richness,
        "shannon_index": round(shannon, 4),
        "pielou_evenness": round(evenness, 4),
        "total_queries_with_hit": n_total,
        "species_counts": rarefied,
        "rarefaction_depth": min(depth, sum(species_counts.values())),
        "expected_richness": rarefaction_point(species_counts, depth),
    }
