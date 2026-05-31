"""
Unit tests for src/protected.py — Phase 3 protected species cross-reference.

Test DataFrames are constructed directly from dict literals to avoid any
dependency on BlastHit or the BLAST parsing pipeline.  The minimum columns
required by check_protected / get_alerts are:
    query_id, hit_rank, species, resolved_species, identity_pct,
    confidence_flag

All 12 tests are grouped into three TestCase classes:
    TestCheckProtected   (6 tests) — column-level behaviour of check_protected
    TestGetAlerts        (4 tests) — dict structure returned by get_alerts
    TestProtectedGenera  (2 tests) — integrity of the auto-built genus lookup
"""

import unittest

import pandas as pd

from src.protected import (
    PROTECTED_GENERA,
    PROTECTED_UK_SPECIES,
    check_protected,
    get_alerts,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_df(**col_overrides) -> pd.DataFrame:
    """
    Return a single-row DataFrame with sensible defaults.

    Keyword arguments override individual column values.  Pass lists to
    create multi-row DataFrames (all lists must be the same length).
    """
    defaults = {
        "query_id": "Q1",
        "hit_rank": 1,
        "species": "Chlorella vulgaris",
        "resolved_species": "Chlorella vulgaris",
        "identity_pct": 98.5,
        "confidence_flag": "high",
    }
    defaults.update(col_overrides)
    # If any value is a list, all values must be lists of the same length.
    if any(isinstance(v, list) for v in defaults.values()):
        return pd.DataFrame(defaults)
    return pd.DataFrame([defaults])


# ---------------------------------------------------------------------------
# TestCheckProtected
# ---------------------------------------------------------------------------

class TestCheckProtected(unittest.TestCase):

    def test_confirmed_exact_match(self):
        """Exact resolved_species match to PROTECTED_UK_SPECIES → CONFIRMED."""
        df = _make_df(resolved_species="Triturus cristatus", hit_rank=1)
        result = check_protected(df)
        self.assertEqual(result.loc[0, "protected_flag"], "CONFIRMED")

    def test_possible_genus_match(self):
        """'Triturus sp.' at hit_rank=1 → POSSIBLE (genus in PROTECTED_GENERA)."""
        df = _make_df(resolved_species="Triturus sp.", hit_rank=1)
        result = check_protected(df)
        self.assertEqual(result.loc[0, "protected_flag"], "POSSIBLE")

    def test_non_protected_species_no_flag(self):
        """A species absent from both dicts → protected_flag is None."""
        df = _make_df(resolved_species="Chlorella vulgaris", hit_rank=1)
        result = check_protected(df)
        self.assertIsNone(result.loc[0, "protected_flag"])

    def test_only_rank1_rows_flagged(self):
        """
        Two rows with the same query: rank 1 = Triturus cristatus,
        rank 2 = Triturus cristatus.  Only rank 1 should be CONFIRMED;
        rank 2 must be None.
        """
        df = _make_df(
            query_id=["Q1", "Q1"],
            hit_rank=[1, 2],
            species=["Triturus cristatus", "Triturus cristatus"],
            resolved_species=["Triturus cristatus", "Triturus cristatus"],
            identity_pct=[98.5, 97.8],
            confidence_flag=["high", "high"],
        )
        result = check_protected(df)
        rank1_flag = result.loc[result["hit_rank"] == 1, "protected_flag"].iloc[0]
        rank2_flag = result.loc[result["hit_rank"] == 2, "protected_flag"].iloc[0]
        self.assertEqual(rank1_flag, "CONFIRMED")
        self.assertIsNone(rank2_flag)

    def test_case_insensitive_match(self):
        """Lower-case resolved_species 'triturus cristatus' → still CONFIRMED."""
        df = _make_df(resolved_species="triturus cristatus", hit_rank=1)
        result = check_protected(df)
        self.assertEqual(result.loc[0, "protected_flag"], "CONFIRMED")

    def test_unclassified_gets_no_flag(self):
        """'unclassified' resolved_species → protected_flag is None."""
        df = _make_df(resolved_species="unclassified", hit_rank=1)
        result = check_protected(df)
        self.assertIsNone(result.loc[0, "protected_flag"])


# ---------------------------------------------------------------------------
# TestGetAlerts
# ---------------------------------------------------------------------------

class TestGetAlerts(unittest.TestCase):

    def _flagged(self, **overrides) -> pd.DataFrame:
        """Build a flagged DataFrame via check_protected."""
        return check_protected(_make_df(**overrides))

    def test_confirmed_alert_returned(self):
        """
        A DataFrame containing Triturus cristatus should produce
        has_alerts=True with a non-empty confirmed list.
        """
        df = self._flagged(resolved_species="Triturus cristatus", hit_rank=1)
        alerts = get_alerts(df)
        self.assertTrue(alerts["has_alerts"])
        self.assertGreater(len(alerts["confirmed"]), 0)
        self.assertEqual(alerts["confirmed"][0]["species"], "Triturus cristatus")

    def test_possible_alert_returned(self):
        """
        A DataFrame containing 'Lutra sp.' should produce a non-empty
        possible list.
        """
        df = self._flagged(resolved_species="Lutra sp.", hit_rank=1)
        alerts = get_alerts(df)
        self.assertGreater(len(alerts["possible"]), 0)
        genera = [entry["genus"] for entry in alerts["possible"]]
        self.assertIn("Lutra", genera)

    def test_no_alerts_empty_result(self):
        """
        A DataFrame with only Chlorella vulgaris should return
        has_alerts=False with empty confirmed and possible lists.
        """
        df = self._flagged(resolved_species="Chlorella vulgaris", hit_rank=1)
        alerts = get_alerts(df)
        self.assertFalse(alerts["has_alerts"])
        self.assertEqual(alerts["confirmed"], [])
        self.assertEqual(alerts["possible"], [])

    def test_highest_alert_level_high(self):
        """
        A DataFrame containing a HIGH-alert EPS species should return
        highest_alert_level='HIGH'.
        """
        df = self._flagged(resolved_species="Lutra lutra", hit_rank=1)
        alerts = get_alerts(df)
        self.assertEqual(alerts["highest_alert_level"], "HIGH")


# ---------------------------------------------------------------------------
# TestProtectedGenera
# ---------------------------------------------------------------------------

class TestProtectedGenera(unittest.TestCase):

    def test_triturus_in_protected_genera(self):
        """'Triturus' must be present as a key in PROTECTED_GENERA."""
        self.assertIn("Triturus", PROTECTED_GENERA)

    def test_protected_genera_built_from_species(self):
        """
        Every genus in PROTECTED_GENERA must have at least one corresponding
        entry in PROTECTED_UK_SPECIES, confirming the dict was built correctly.
        """
        for genus, species_list in PROTECTED_GENERA.items():
            self.assertGreater(
                len(species_list),
                0,
                msg=f"Genus '{genus}' has an empty species list in PROTECTED_GENERA",
            )
            for species_name in species_list:
                self.assertIn(
                    species_name,
                    PROTECTED_UK_SPECIES,
                    msg=(
                        f"'{species_name}' listed under genus '{genus}' in "
                        "PROTECTED_GENERA but not found in PROTECTED_UK_SPECIES"
                    ),
                )


if __name__ == "__main__":
    unittest.main()
