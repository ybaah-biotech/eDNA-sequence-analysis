"""
tests/test_plots.py — Smoke tests for src/plots.py (Phase 6).

Plot rendering is I/O, not logic, so these tests confirm a PNG file is created
(or that empty input is handled gracefully) rather than inspecting pixels.
"""

from src.plots import rarefaction_plot
from src.rarefaction import rarefaction_curve


class TestRarefactionPlot:
    def test_creates_png_file(self, tmp_path):
        counts = {"a": 20, "b": 15, "c": 10, "d": 5}
        curve = rarefaction_curve(counts, n_points=10)
        out = rarefaction_plot(
            curve,
            tmp_path / "rare.png",
            observed_richness=4,
            chao1_value=5.5,
            rarefy_depth=25,
        )
        assert out is not None
        assert out.exists()
        assert out.stat().st_size > 0

    def test_empty_curve_returns_none(self, tmp_path):
        assert rarefaction_plot([], tmp_path / "empty.png") is None

    def test_minimal_args_ok(self, tmp_path):
        curve = rarefaction_curve({"a": 10, "b": 10}, n_points=5)
        out = rarefaction_plot(curve, tmp_path / "min.png")
        assert out is not None and out.exists()
