"""
src/plots.py — Chart rendering for the eDNA pipeline.

Produces PNG figures embedded in the regulatory PDF report. Uses matplotlib's
non-interactive ``Agg`` backend so it runs headless (CI, servers, containers)
without a display.

Currently provides the rarefaction curve (Phase 6). Future phases (beta
diversity / PCoA, Phase 7) will add their plots here so all chart rendering
lives in one place.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")  # headless backend — must be set before pyplot import
import matplotlib.pyplot as plt  # noqa: E402

log = logging.getLogger(__name__)

__all__ = ["rarefaction_plot"]


def rarefaction_plot(
    curve: Sequence[Tuple[int, float]],
    output_path: Path,
    observed_richness: Optional[int] = None,
    chao1_value: Optional[float] = None,
    rarefy_depth: Optional[int] = None,
    title: str = "Rarefaction curve",
) -> Optional[Path]:
    """
    Render a rarefaction curve to a PNG and return its path.

    Parameters
    ----------
    curve:
        ``[(depth, expected_species), ...]`` from
        :func:`src.rarefaction.rarefaction_curve`.
    output_path:
        Destination PNG path.
    observed_richness:
        If given, drawn as a dashed horizontal reference line (the richness
        actually observed at full depth).
    chao1_value:
        If given, drawn as a dotted horizontal line (estimated true richness).
    rarefy_depth:
        If given, drawn as a vertical line marking the chosen rarefaction depth.
    title:
        Plot title.

    Returns the PNG path, or ``None`` if there is nothing to plot or rendering
    fails (the caller falls back to the numeric table — a plot failure must
    never abort report generation).
    """
    if not curve:
        return None

    try:
        xs: List[int] = [d for d, _ in curve]
        ys: List[float] = [s for _, s in curve]

        fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=150)
        ax.plot(xs, ys, color="#1B4F72", linewidth=2.0, marker="o",
                markersize=3, label="Expected species")

        if observed_richness is not None:
            ax.axhline(observed_richness, color="#1E8449", linestyle="--",
                       linewidth=1.2, label=f"Observed richness = {observed_richness}")
        if chao1_value is not None:
            ax.axhline(chao1_value, color="#D4AC0D", linestyle=":",
                       linewidth=1.4, label=f"Chao1 estimate = {chao1_value:.1f}")
        if rarefy_depth is not None:
            ax.axvline(rarefy_depth, color="#922B21", linestyle="-.",
                       linewidth=1.2, label=f"Rarefaction depth = {rarefy_depth}")

        ax.set_xlabel("Sequencing depth (reads sampled)")
        ax.set_ylabel("Species detected")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc="lower right")
        fig.tight_layout()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path)
        plt.close(fig)
        log.info(f"Rarefaction plot -> {output_path}")
        return output_path
    except Exception as exc:  # noqa: BLE001
        log.warning(f"Could not render rarefaction plot: {exc}")
        plt.close("all")
        return None
