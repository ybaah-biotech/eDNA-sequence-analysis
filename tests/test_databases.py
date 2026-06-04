"""
tests/test_databases.py — Unit tests for src/databases.py (Phase 4).

Tests cover:
  - DATABASE_REGISTRY structure and completeness
  - get_database_info() — valid keys, case folding, unknown keys
  - recommend_database() — each marker, case insensitivity, unknown marker
  - list_databases() — return type and completeness
"""

import pytest
from src.databases import (
    DATABASE_REGISTRY,
    DatabaseInfo,
    get_database_info,
    list_databases,
    recommend_database,
)


# ---------------------------------------------------------------------------
# TestDatabaseRegistry
# ---------------------------------------------------------------------------

class TestDatabaseRegistry:
    """DATABASE_REGISTRY structure and content checks."""

    EXPECTED_KEYS = {
        "silva_ssu",
        "bold",
        "midori2",
        "its_refseq_fungi",
        "16s_rrna",
        "pr2",
        "nt",
    }

    def test_all_expected_databases_present(self):
        assert self.EXPECTED_KEYS.issubset(set(DATABASE_REGISTRY.keys()))

    def test_all_entries_are_database_info(self):
        for key, val in DATABASE_REGISTRY.items():
            assert isinstance(val, DatabaseInfo), (
                f"DATABASE_REGISTRY['{key}'] is not a DatabaseInfo instance"
            )

    def test_all_entries_have_non_empty_markers(self):
        for key, db in DATABASE_REGISTRY.items():
            assert db.markers, f"'{key}' has an empty markers list"

    def test_all_entries_have_non_empty_download_url(self):
        for key, db in DATABASE_REGISTRY.items():
            assert db.download_url.startswith("http"), (
                f"'{key}' download_url does not start with http"
            )

    def test_ncbi_databases_have_ncbi_name(self):
        ncbi_dbs = {k: v for k, v in DATABASE_REGISTRY.items() if v.source == "ncbi"}
        for key, db in ncbi_dbs.items():
            assert db.ncbi_name is not None, (
                f"NCBI database '{key}' is missing ncbi_name"
            )

    def test_silva_covers_16s_and_18s(self):
        silva = DATABASE_REGISTRY["silva_ssu"]
        assert "16S" in silva.markers
        assert "18S" in silva.markers

    def test_nt_size_reflects_large_database(self):
        nt = DATABASE_REGISTRY["nt"]
        assert nt.approx_size_gb >= 100, (
            "nt database should be flagged as large (>=100 GB)"
        )


# ---------------------------------------------------------------------------
# TestGetDatabaseInfo
# ---------------------------------------------------------------------------

class TestGetDatabaseInfo:
    """get_database_info() — lookup by name."""

    def test_exact_key_returns_correct_db(self):
        db = get_database_info("silva_ssu")
        assert db.name == "silva_ssu"
        assert db.display_name == "SILVA 138.2 SSU"

    def test_ncbi_name_lookup(self):
        """Should resolve NCBI name like 'ITS_RefSeq_Fungi'."""
        db = get_database_info("ITS_RefSeq_Fungi")
        assert db.name == "its_refseq_fungi"

    def test_unknown_name_raises_key_error(self):
        with pytest.raises(KeyError, match="Unknown database"):
            get_database_info("nonexistent_db_xyz")

    def test_bold_lookup(self):
        db = get_database_info("bold")
        assert "COI" in db.markers

    def test_midori2_lookup(self):
        db = get_database_info("midori2")
        assert "12S" in db.markers

    def test_pr2_lookup(self):
        db = get_database_info("pr2")
        assert "18S" in db.markers


# ---------------------------------------------------------------------------
# TestRecommendDatabase
# ---------------------------------------------------------------------------

class TestRecommendDatabase:
    """recommend_database() — marker to database routing."""

    def test_16s_recommends_silva(self):
        db = recommend_database("16S")
        assert db.name == "silva_ssu"

    def test_18s_recommends_silva(self):
        db = recommend_database("18S")
        assert db.name == "silva_ssu"

    def test_coi_recommends_bold(self):
        db = recommend_database("COI")
        assert db.name == "bold"

    def test_12s_recommends_midori2(self):
        db = recommend_database("12S")
        assert db.name == "midori2"

    def test_its_recommends_its_refseq_fungi(self):
        db = recommend_database("ITS")
        assert db.name == "its_refseq_fungi"

    def test_its1_recommends_its_refseq_fungi(self):
        db = recommend_database("ITS1")
        assert db.name == "its_refseq_fungi"

    def test_its2_recommends_its_refseq_fungi(self):
        db = recommend_database("ITS2")
        assert db.name == "its_refseq_fungi"

    def test_case_insensitive_lowercase(self):
        db = recommend_database("16s")
        assert db.name == "silva_ssu"

    def test_case_insensitive_mixed(self):
        db = recommend_database("cOi")
        assert db.name == "bold"

    def test_unknown_marker_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown marker"):
            recommend_database("UNKNOWN_GENE")

    def test_recommended_db_contains_marker_in_markers_list(self):
        """Every recommendation should be for a DB that lists that marker."""
        for marker in ["16S", "18S", "COI", "12S", "ITS", "ITS1", "ITS2"]:
            db = recommend_database(marker)
            assert marker.upper() in db.markers, (
                f"recommend_database('{marker}') returned '{db.name}' "
                f"but '{marker}' not in its markers list {db.markers}"
            )


# ---------------------------------------------------------------------------
# TestListDatabases
# ---------------------------------------------------------------------------

class TestListDatabases:
    """list_databases() — returns all registered databases."""

    def test_returns_list(self):
        result = list_databases()
        assert isinstance(result, list)

    def test_returns_all_databases(self):
        result = list_databases()
        assert len(result) == len(DATABASE_REGISTRY)

    def test_all_items_are_database_info(self):
        for item in list_databases():
            assert isinstance(item, DatabaseInfo)

    def test_sorted_by_name(self):
        result = list_databases()
        names = [db.name for db in result]
        assert names == sorted(names)
