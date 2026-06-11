"""
tests/test_rarefaction.py — Unit tests for src/rarefaction.py (Phase 6).

Tests cover:
  - chao1() — singletons/doubletons, bias-corrected branch, no-rare case, empty
  - rarefaction_point() — endpoints, monotonicity, exact small-case value
  - rarefaction_curve() — shape, plateau, empty input
  - rarefy_counts() — depth conservation, determinism with seed, passthrough
  - rarefied_diversity() — schema, richness bounded by depth
"""

import math

import pytest

from src.rarefaction import (
    chao1,
    rarefaction_curve,
    rarefaction_point,
    rarefied_diversity,
    rarefy_counts,
)


# ---------------------------------------------------------------------------
# TestChao1
# ---------------------------------------------------------------------------

class TestChao1:
    def test_classic_formula_with_doubletons(self):
        # S_obs=3, F1=2 singletons, F2=1 doubleton -> 3 + 4/2 = 5
        counts = {"a": 1, "b": 1, "c": 2}
        assert chao1(counts) == 5.0

    def test_no_singletons_returns_observed(self):
        counts = {"a": 5, "b": 4, "c": 3}
        assert chao1(counts) == 3.0

    def test_bias_corrected_when_no_doubletons(self):
        # S_obs=3, F1=2, F2=0 -> 3 + (2*1)/(2*1) = 4
        counts = {"a": 1, "b": 1, "c": 5}
        assert chao1(counts) == 4.0

    def test_always_at_least_observed(self):
        counts = {"a": 1, "b": 1, "c": 1, "d": 10}
        assert chao1(counts) >= len(counts)

    def test_empty_returns_zero(self):
        assert chao1({}) == 0.0

    def test_ignores_zero_counts(self):
        counts = {"a": 5, "b": 0}
        assert chao1(counts) == 1.0


# ---------------------------------------------------------------------------
# TestRarefactionPoint
# ---------------------------------------------------------------------------

class TestRarefactionPoint:
    def test_depth_zero_is_zero(self):
        assert rarefaction_point({"a": 5, "b": 5}, 0) == 0.0

    def test_full_depth_returns_observed_richness(self):
        counts = {"a": 5, "b": 3, "c": 2}
        assert rarefaction_point(counts, sum(counts.values())) == 3.0

    def test_beyond_full_depth_caps_at_richness(self):
        counts = {"a": 5, "b": 3}
        assert rarefaction_point(counts, 1000) == 2.0

    def test_depth_one_expected_between_one_and_richness(self):
        counts = {"a": 5, "b": 5}
        # A single read always yields exactly one species
        assert rarefaction_point(counts, 1) == 1.0

    def test_exact_small_case(self):
        # 2 species, 2 reads each, subsample of 2:
        # P(both same sp) for each species = C(2,2)/C(4,2) = 1/6
        # E(S) = 2 - 2*(1/6) = 1.6667
        counts = {"a": 2, "b": 2}
        assert rarefaction_point(counts, 2) == pytest.approx(1.6667, abs=1e-4)

    def test_monotonic_increasing(self):
        counts = {"a": 10, "b": 8, "c": 6, "d": 4, "e": 2}
        vals = [rarefaction_point(counts, d) for d in (1, 5, 10, 20, 30)]
        assert all(vals[i] <= vals[i + 1] + 1e-9 for i in range(len(vals) - 1))

    def test_empty_counts_zero(self):
        assert rarefaction_point({}, 5) == 0.0


# ---------------------------------------------------------------------------
# TestRarefactionCurve
# ---------------------------------------------------------------------------

class TestRarefactionCurve:
    def test_returns_list_of_pairs(self):
        curve = rarefaction_curve({"a": 10, "b": 10}, n_points=5)
        assert all(isinstance(p, tuple) and len(p) == 2 for p in curve)

    def test_ends_at_total_depth(self):
        counts = {"a": 10, "b": 10}
        curve = rarefaction_curve(counts, n_points=5)
        assert curve[-1][0] == sum(counts.values())

    def test_final_point_equals_observed_richness(self):
        counts = {"a": 10, "b": 5, "c": 5}
        curve = rarefaction_curve(counts, n_points=5)
        assert curve[-1][1] == 3.0

    def test_curve_is_non_decreasing(self):
        counts = {"a": 20, "b": 15, "c": 10, "d": 5}
        curve = rarefaction_curve(counts, n_points=10)
        ys = [y for _, y in curve]
        assert all(ys[i] <= ys[i + 1] + 1e-9 for i in range(len(ys) - 1))

    def test_empty_returns_empty(self):
        assert rarefaction_curve({}) == []


# ---------------------------------------------------------------------------
# TestRarefyCounts
# ---------------------------------------------------------------------------

class TestRarefyCounts:
    def test_subsample_conserves_depth(self):
        counts = {"a": 50, "b": 30, "c": 20}
        out = rarefy_counts(counts, 40, seed=1)
        assert sum(out.values()) == 40

    def test_deterministic_with_seed(self):
        counts = {"a": 50, "b": 30, "c": 20}
        a = rarefy_counts(counts, 40, seed=42)
        b = rarefy_counts(counts, 40, seed=42)
        assert a == b

    def test_different_seeds_can_differ(self):
        counts = {f"sp{i}": 10 for i in range(20)}
        a = rarefy_counts(counts, 50, seed=1)
        b = rarefy_counts(counts, 50, seed=2)
        # Not guaranteed different, but overwhelmingly likely for this setup
        assert a != b

    def test_depth_at_or_above_total_passthrough(self):
        counts = {"a": 5, "b": 3}
        assert rarefy_counts(counts, 100) == counts

    def test_depth_zero_empty(self):
        assert rarefy_counts({"a": 5}, 0) == {}

    def test_no_count_exceeds_original(self):
        counts = {"a": 50, "b": 30, "c": 20}
        out = rarefy_counts(counts, 60, seed=7)
        for taxon, c in out.items():
            assert c <= counts[taxon]


# ---------------------------------------------------------------------------
# TestRarefiedDiversity
# ---------------------------------------------------------------------------

class TestRarefiedDiversity:
    def test_schema_keys_present(self):
        result = rarefied_diversity({"a": 50, "b": 30, "c": 20}, 40, seed=1)
        for key in (
            "species_richness", "shannon_index", "pielou_evenness",
            "total_queries_with_hit", "species_counts",
            "rarefaction_depth", "expected_richness",
        ):
            assert key in result

    def test_total_equals_depth(self):
        result = rarefied_diversity({"a": 50, "b": 30, "c": 20}, 40, seed=1)
        assert result["total_queries_with_hit"] == 40

    def test_richness_not_above_observed(self):
        counts = {"a": 50, "b": 30, "c": 20}
        result = rarefied_diversity(counts, 40, seed=1)
        assert result["species_richness"] <= len(counts)

    def test_reproducible_with_seed(self):
        counts = {"a": 50, "b": 30, "c": 20}
        a = rarefied_diversity(counts, 40, seed=5)
        b = rarefied_diversity(counts, 40, seed=5)
        assert a == b

    def test_single_species_evenness_one(self):
        result = rarefied_diversity({"a": 100}, 50, seed=1)
        assert result["species_richness"] == 1
        assert result["pielou_evenness"] == 1.0
