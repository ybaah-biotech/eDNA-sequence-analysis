"""
tests/test_markers.py — Unit tests for src/markers.py (Phase 5).

Tests cover:
  - detect_marker() — each supported marker, case insensitivity, no-prefix,
    unknown prefix, empty input
  - add_marker_column() — tagging, empty DataFrame
  - split_sequences_by_marker() — grouping, unknown bucket, counts
  - calculate_diversity_by_marker() — per-marker isolation, no pooling
"""

import pandas as pd
import pytest
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from src.markers import (
    SUPPORTED_MARKERS,
    UNKNOWN_MARKER,
    add_marker_column,
    calculate_diversity_by_marker,
    detect_marker,
    marker_summary_frame,
    split_sequences_by_marker,
)


def _rec(seq: str = "ACGT") -> SeqRecord:
    return SeqRecord(Seq(seq), id="x")


def _hit_row(query_id, species, rank=1, identity=99.0):
    """Build a minimal hit-table row matching the summarise schema."""
    return {
        "query_id": query_id,
        "hit_rank": rank,
        "species": species,
        "resolved_species": species,
        "identity_pct": identity,
    }


# ---------------------------------------------------------------------------
# TestDetectMarker
# ---------------------------------------------------------------------------

class TestDetectMarker:
    def test_16s_prefix(self):
        assert detect_marker("16S_pondA_001") == "16S"

    def test_18s_prefix(self):
        assert detect_marker("18S_sample_2") == "18S"

    def test_12s_prefix(self):
        assert detect_marker("12S_fish_07") == "12S"

    def test_coi_prefix(self):
        assert detect_marker("COI_inv_3") == "COI"

    def test_its_prefix(self):
        assert detect_marker("ITS_fungi_1") == "ITS"

    def test_its1_prefix(self):
        assert detect_marker("ITS1_x") == "ITS1"

    def test_its2_prefix(self):
        assert detect_marker("ITS2_y") == "ITS2"

    def test_case_insensitive_lowercase(self):
        assert detect_marker("coi_seq3") == "COI"

    def test_case_insensitive_mixed(self):
        assert detect_marker("Coi_seq3") == "COI"

    def test_no_underscore_returns_unknown(self):
        # A bare "16S" has no prefix delimiter — treated as no marker tag
        assert detect_marker("16S") == UNKNOWN_MARKER

    def test_unrecognised_prefix_returns_unknown(self):
        assert detect_marker("seq_001") == UNKNOWN_MARKER

    def test_empty_string_returns_unknown(self):
        assert detect_marker("") == UNKNOWN_MARKER

    def test_all_supported_markers_detected(self):
        for marker in SUPPORTED_MARKERS:
            qid = f"{marker}_test_1"
            assert detect_marker(qid) == marker


# ---------------------------------------------------------------------------
# TestAddMarkerColumn
# ---------------------------------------------------------------------------

class TestAddMarkerColumn:
    def test_adds_marker_column(self):
        df = pd.DataFrame([
            _hit_row("16S_a", "Escherichia coli"),
            _hit_row("COI_b", "Daphnia pulex"),
        ])
        out = add_marker_column(df)
        assert list(out["marker"]) == ["16S", "COI"]

    def test_does_not_mutate_input(self):
        df = pd.DataFrame([_hit_row("16S_a", "Escherichia coli")])
        add_marker_column(df)
        assert "marker" not in df.columns

    def test_empty_dataframe_gets_empty_marker_column(self):
        out = add_marker_column(pd.DataFrame())
        assert "marker" in out.columns
        assert len(out) == 0

    def test_unknown_prefix_tagged_unknown(self):
        df = pd.DataFrame([_hit_row("seq_1", "Escherichia coli")])
        out = add_marker_column(df)
        assert out["marker"].iloc[0] == UNKNOWN_MARKER


# ---------------------------------------------------------------------------
# TestSplitSequencesByMarker
# ---------------------------------------------------------------------------

class TestSplitSequencesByMarker:
    def test_groups_by_marker(self):
        seqs = {
            "16S_a": _rec(),
            "16S_b": _rec(),
            "COI_c": _rec(),
        }
        grouped = split_sequences_by_marker(seqs)
        assert set(grouped.keys()) == {"16S", "COI"}
        assert len(grouped["16S"]) == 2
        assert len(grouped["COI"]) == 1

    def test_unknown_bucket_collects_untagged(self):
        seqs = {"seq_1": _rec(), "COI_2": _rec()}
        grouped = split_sequences_by_marker(seqs)
        assert UNKNOWN_MARKER in grouped
        assert "seq_1" in grouped[UNKNOWN_MARKER]

    def test_no_sequences_dropped(self):
        seqs = {f"16S_{i}": _rec() for i in range(3)}
        seqs.update({f"COI_{i}": _rec() for i in range(2)})
        grouped = split_sequences_by_marker(seqs)
        total = sum(len(v) for v in grouped.values())
        assert total == len(seqs)

    def test_preserves_records(self):
        rec = _rec("ACGTACGT")
        grouped = split_sequences_by_marker({"12S_fish": rec})
        assert grouped["12S"]["12S_fish"] is rec


# ---------------------------------------------------------------------------
# TestCalculateDiversityByMarker
# ---------------------------------------------------------------------------

class TestCalculateDiversityByMarker:
    def test_returns_one_entry_per_marker(self):
        df = pd.DataFrame([
            _hit_row("16S_a", "Escherichia coli"),
            _hit_row("16S_b", "Bacillus subtilis"),
            _hit_row("COI_c", "Daphnia pulex"),
        ])
        result = calculate_diversity_by_marker(df)
        assert set(result.keys()) == {"16S", "COI"}

    def test_diversity_not_pooled_across_markers(self):
        # Two distinct bacteria under 16S, one animal under COI.
        df = pd.DataFrame([
            _hit_row("16S_a", "Escherichia coli"),
            _hit_row("16S_b", "Bacillus subtilis"),
            _hit_row("COI_c", "Daphnia pulex"),
        ])
        result = calculate_diversity_by_marker(df)
        assert result["16S"]["species_richness"] == 2
        assert result["COI"]["species_richness"] == 1

    def test_adds_marker_column_if_missing(self):
        # No 'marker' column supplied — function should derive it.
        df = pd.DataFrame([_hit_row("COI_c", "Daphnia pulex")])
        result = calculate_diversity_by_marker(df)
        assert "COI" in result

    def test_empty_dataframe_returns_empty_dict(self):
        assert calculate_diversity_by_marker(pd.DataFrame()) == {}

    def test_unknown_marker_still_reported(self):
        df = pd.DataFrame([_hit_row("seq_1", "Escherichia coli")])
        result = calculate_diversity_by_marker(df)
        assert UNKNOWN_MARKER in result
        assert result[UNKNOWN_MARKER]["species_richness"] == 1


# ---------------------------------------------------------------------------
# TestMarkerSummaryFrame
# ---------------------------------------------------------------------------

class TestMarkerSummaryFrame:
    def test_one_row_per_marker(self):
        df = pd.DataFrame([
            _hit_row("16S_a", "Escherichia coli"),
            _hit_row("COI_c", "Daphnia pulex"),
        ])
        md = calculate_diversity_by_marker(df)
        summary = marker_summary_frame(md)
        assert len(summary) == 2
        assert set(summary["marker"]) == {"16S", "COI"}

    def test_expected_columns(self):
        df = pd.DataFrame([_hit_row("16S_a", "Escherichia coli")])
        summary = marker_summary_frame(calculate_diversity_by_marker(df))
        assert list(summary.columns) == [
            "marker",
            "total_queries_with_hit",
            "species_richness",
            "shannon_index_H",
            "pielou_evenness_J",
            "unclassified_queries",
        ]

    def test_empty_input_returns_empty_frame(self):
        summary = marker_summary_frame({})
        assert summary.empty

    def test_sorted_by_marker(self):
        df = pd.DataFrame([
            _hit_row("COI_c", "Daphnia pulex"),
            _hit_row("16S_a", "Escherichia coli"),
            _hit_row("ITS_f", "Saccharomyces cerevisiae"),
        ])
        summary = marker_summary_frame(calculate_diversity_by_marker(df))
        assert list(summary["marker"]) == sorted(summary["marker"])
