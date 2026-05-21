"""
Unit tests for the BLAST XML parser.

Uses a minimal synthetic BLAST XML fixture so tests run without any
network calls. Covers: hit extraction, e-value filtering, species
name parsing, and graceful handling of empty results.
"""

import math
import textwrap
import tempfile
import unittest
from pathlib import Path

from src.parser import _extract_species, parse_blast_xml, BlastHit
from src.summarise import build_hit_table, calculate_diversity

# ── Minimal valid BLAST XML (two alignments, one above e-value threshold) ──
# Includes all elements Biopython's SAX-based NCBIXML parser expects.
_BLAST_XML = textwrap.dedent("""\
<?xml version="1.0"?>
<BlastOutput>
  <BlastOutput_program>blastn</BlastOutput_program>
  <BlastOutput_version>BLASTN 2.14.0+</BlastOutput_version>
  <BlastOutput_reference>Reference</BlastOutput_reference>
  <BlastOutput_db>nt</BlastOutput_db>
  <BlastOutput_query-ID>Query_1</BlastOutput_query-ID>
  <BlastOutput_query-def>QUERY_001 Betula_pendula_ITS2</BlastOutput_query-def>
  <BlastOutput_query-len>214</BlastOutput_query-len>
  <BlastOutput_param>
    <Parameters>
      <Parameters_matrix></Parameters_matrix>
      <Parameters_expect>10</Parameters_expect>
      <Parameters_sc-match>1</Parameters_sc-match>
      <Parameters_sc-mismatch>-3</Parameters_sc-mismatch>
      <Parameters_gap-open>5</Parameters_gap-open>
      <Parameters_gap-extend>2</Parameters_gap-extend>
      <Parameters_filter>L;m;</Parameters_filter>
    </Parameters>
  </BlastOutput_param>
  <BlastOutput_iterations>
    <Iteration>
      <Iteration_iter-num>1</Iteration_iter-num>
      <Iteration_query-ID>Query_1</Iteration_query-ID>
      <Iteration_query-def>QUERY_001 Betula_pendula_ITS2</Iteration_query-def>
      <Iteration_query-len>214</Iteration_query-len>
      <Iteration_hits>
        <Hit>
          <Hit_num>1</Hit_num>
          <Hit_id>gi|123456|gb|AJ312462.1|</Hit_id>
          <Hit_def>Betula pendula isolate BET1 internal transcribed spacer 2</Hit_def>
          <Hit_accession>AJ312462</Hit_accession>
          <Hit_len>220</Hit_len>
          <Hit_hsps>
            <Hsp>
              <Hsp_num>1</Hsp_num>
              <Hsp_bit-score>380.6</Hsp_bit-score>
              <Hsp_score>410</Hsp_score>
              <Hsp_evalue>1e-104</Hsp_evalue>
              <Hsp_query-from>1</Hsp_query-from>
              <Hsp_query-to>214</Hsp_query-to>
              <Hsp_hit-from>1</Hsp_hit-from>
              <Hsp_hit-to>214</Hsp_hit-to>
              <Hsp_query-frame>1</Hsp_query-frame>
              <Hsp_hit-frame>1</Hsp_hit-frame>
              <Hsp_identity>211</Hsp_identity>
              <Hsp_positive>211</Hsp_positive>
              <Hsp_gaps>0</Hsp_gaps>
              <Hsp_align-len>214</Hsp_align-len>
              <Hsp_qseq>ACGT</Hsp_qseq>
              <Hsp_hseq>ACGT</Hsp_hseq>
              <Hsp_midline>||||</Hsp_midline>
            </Hsp>
          </Hit_hsps>
        </Hit>
        <Hit>
          <Hit_num>2</Hit_num>
          <Hit_id>gi|999999|gb|ZZ999999.1|</Hit_id>
          <Hit_def>Betula pubescens isolate BPU2 internal transcribed spacer 2</Hit_def>
          <Hit_accession>ZZ999999</Hit_accession>
          <Hit_len>218</Hit_len>
          <Hit_hsps>
            <Hsp>
              <Hsp_num>1</Hsp_num>
              <Hsp_bit-score>5.0</Hsp_bit-score>
              <Hsp_score>3</Hsp_score>
              <Hsp_evalue>0.9</Hsp_evalue>
              <Hsp_query-from>1</Hsp_query-from>
              <Hsp_query-to>10</Hsp_query-to>
              <Hsp_hit-from>1</Hsp_hit-from>
              <Hsp_hit-to>10</Hsp_hit-to>
              <Hsp_query-frame>1</Hsp_query-frame>
              <Hsp_hit-frame>1</Hsp_hit-frame>
              <Hsp_identity>8</Hsp_identity>
              <Hsp_positive>8</Hsp_positive>
              <Hsp_gaps>0</Hsp_gaps>
              <Hsp_align-len>10</Hsp_align-len>
              <Hsp_qseq>ACGT</Hsp_qseq>
              <Hsp_hseq>ACGT</Hsp_hseq>
              <Hsp_midline>||||</Hsp_midline>
            </Hsp>
          </Hit_hsps>
        </Hit>
      </Iteration_hits>
      <Iteration_stat>
        <Statistics>
          <Statistics_db-num>1000</Statistics_db-num>
          <Statistics_db-len>1000000</Statistics_db-len>
          <Statistics_hsp-len>0</Statistics_hsp-len>
          <Statistics_eff-space>0</Statistics_eff-space>
          <Statistics_kappa>0.041</Statistics_kappa>
          <Statistics_lambda>0.267</Statistics_lambda>
          <Statistics_entropy>0.14</Statistics_entropy>
        </Statistics>
      </Iteration_stat>
    </Iteration>
  </BlastOutput_iterations>
</BlastOutput>
""")


class TestExtractSpecies(unittest.TestCase):
    # ── Original passing cases ────────────────────────────────────────────────

    def test_standard_genbank_title(self):
        title = "gb|AJ312462.1| Betula pendula isolate BET1 internal transcribed spacer"
        assert _extract_species(title) == "Betula pendula"

    def test_title_without_accession_prefix(self):
        title = "Alternaria alternata strain CBS 916.96 ITS region"
        assert _extract_species(title) == "Alternaria alternata"

    def test_organism_in_brackets_fallback(self):
        title = "predicted mRNA, partial sequence [Quercus robur]"
        assert _extract_species(title) == "Quercus robur"

    # ── Fix 1: cf. / aff. qualifiers ─────────────────────────────────────────
    # Previously returned "Alternaria cf" / "Penicillium aff" because "cf" and
    # "aff" passed the lowercase+isalpha epithet checks.

    def test_cf_qualifier_skipped(self):
        title = "Alternaria cf. alternata strain CBS isolate"
        assert _extract_species(title) == "Alternaria alternata"

    def test_aff_qualifier_skipped(self):
        title = "Penicillium aff. expansum culture collection"
        assert _extract_species(title) == "Penicillium expansum"

    def test_var_qualifier_returns_species(self):
        # var. sits after species epithet; species name comes first
        title = "Betula pendula var. pubescens isolate"
        assert _extract_species(title) == "Betula pendula"

    def test_subsp_qualifier_returns_species(self):
        title = "Puccinia striiformis subsp. tritici specimen"
        assert _extract_species(title) == "Puccinia striiformis"

    # ── Fix 2: multi-hit title concatenation ─────────────────────────────────
    # Previously iterated over all tokens from all concatenated records,
    # risking a species name from the wrong database entry being returned.

    def test_multi_hit_title_uses_only_first_record(self):
        title = (
            "gb|AJ312462.1| Betula pendula isolate BET1 "
            ">gb|AJ312463.2| Populus tremula clone PT99"
        )
        # Must return species from the first record only
        assert _extract_species(title) == "Betula pendula"

    # ── Fix 3: uncultured / environmental sequences ───────────────────────────
    # Previously "uncultured" was skipped (lowercase), then a clone identifier
    # or "environmental sample" could be returned as the species name.

    def test_uncultured_returns_unclassified(self):
        title = "uncultured fungus clone ABC123 [environmental sample]"
        assert _extract_species(title) == "unclassified"

    def test_uncultured_genus_is_rescued(self):
        # Uncultured rescue: genus name is present after "uncultured" — return
        # "Genus sp." rather than discarding as "unclassified"
        title = "uncultured Alternaria sp. clone XY9 [environmental sample]"
        assert _extract_species(title) == "Alternaria sp."

    def test_uncultured_with_known_genus_clone_rescued(self):
        title = "uncultured Chlorella sp. clone ENV45 18S ribosomal RNA partial"
        assert _extract_species(title) == "Chlorella sp."

    def test_metagenome_returns_unclassified(self):
        title = "soil metagenome sequence [metagenome]"
        assert _extract_species(title) == "unclassified"

    # ── Fix 4: hybrid × notation ─────────────────────────────────────────────
    # Previously × caused isalpha() to fail, skipping the hybrid entirely and
    # potentially returning the accession prefix as output.

    def test_hybrid_unicode_cross(self):
        title = "gb|MK123456.1| Populus × canadensis clone POP1 ITS"
        assert _extract_species(title) == "Populus canadensis"

    def test_hybrid_lowercase_x(self):
        title = "Betula x pubescens hybrid specimen"
        assert _extract_species(title) == "Betula pubescens"

    # ── Fix 5: genus-only resolution uses sp. notation ───────────────────────
    # Previously returned bare "Genus" when no epithet could be found.
    # Correct notation for an unresolved species within a known genus is "Genus sp."

    def test_genus_only_gets_sp_suffix(self):
        # "BET001" has a digit so epithet check fails → genus sp.
        title = "Betula BET001 barcode sequence"
        assert _extract_species(title) == "Betula sp."

    def test_sp_abbreviation_returns_genus_sp(self):
        title = "Cladosporium sp. isolate CL44 ITS"
        assert _extract_species(title) == "Cladosporium sp."


class TestParseBlastXml(unittest.TestCase):
    def _write_xml(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        )
        tmp.write(content)
        tmp.close()
        return Path(tmp.name)

    def test_single_hit_passes_evalue(self):
        xml_path = self._write_xml(_BLAST_XML)
        hits = parse_blast_xml(xml_path, max_hits=5, evalue_threshold=1e-10)
        self.assertEqual(len(hits), 1)
        hit = hits[0]
        self.assertEqual(hit.query_id, "QUERY_001")
        self.assertAlmostEqual(hit.identity_pct, 98.6, places=0)
        self.assertEqual(hit.hit_rank, 1)
        self.assertAlmostEqual(hit.query_coverage_pct, 100.0, places=0)
        xml_path.unlink()

    def test_high_evalue_hit_is_filtered(self):
        xml_path = self._write_xml(_BLAST_XML)
        hits = parse_blast_xml(xml_path, max_hits=5, evalue_threshold=1e-10)
        evalues = [h.evalue for h in hits]
        self.assertTrue(all(e <= 1e-10 for e in evalues))
        xml_path.unlink()

    def test_empty_xml_returns_empty_list(self):
        empty_xml = (
            '<?xml version="1.0"?><BlastOutput>'
            '<BlastOutput_program>blastn</BlastOutput_program>'
            '<BlastOutput_version>2.14</BlastOutput_version>'
            '<BlastOutput_db>nt</BlastOutput_db>'
            '<BlastOutput_iterations></BlastOutput_iterations>'
            '</BlastOutput>'
        )
        xml_path = self._write_xml(empty_xml)
        hits = parse_blast_xml(xml_path)
        self.assertEqual(hits, [])
        xml_path.unlink()

    # ── Fix 6: coverage clamped to 100 % ────────────────────────────────────

    def test_coverage_never_exceeds_100(self):
        xml_path = self._write_xml(_BLAST_XML)
        hits = parse_blast_xml(xml_path, max_hits=5, evalue_threshold=1e-10)
        for hit in hits:
            self.assertLessEqual(hit.query_coverage_pct, 100.0)
        xml_path.unlink()


class TestBiodiversityMetrics(unittest.TestCase):
    def _make_hits(self) -> list:
        return [
            BlastHit("Q1", 200, 1, "ACC1", "Betula pendula",       "desc", 98.0, 1e-50, 300.0, 196, 98.0),
            BlastHit("Q2", 500, 1, "ACC2", "Alternaria alternata", "desc", 97.5, 1e-90, 450.0, 480, 96.0),
            BlastHit("Q3", 350, 1, "ACC3", "Pinus sylvestris",     "desc", 96.0, 1e-60, 320.0, 340, 97.0),
            BlastHit("Q4", 480, 1, "ACC4", "Alternaria alternata", "desc", 99.0, 1e-95, 460.0, 462, 96.0),
        ]

    def test_species_richness(self):
        hits = self._make_hits()
        df = build_hit_table(hits)
        div = calculate_diversity(df)
        self.assertEqual(div["species_richness"], 3)

    def test_shannon_positive_for_multiple_species(self):
        hits = self._make_hits()
        df = build_hit_table(hits)
        div = calculate_diversity(df)
        self.assertGreater(div["shannon_index"], 0)

    def test_single_species_evenness_is_one(self):
        hits = [
            BlastHit("Q1", 200, 1, "ACC1", "Betula pendula", "desc", 98.0, 1e-50, 300.0, 196, 98.0),
            BlastHit("Q2", 200, 1, "ACC2", "Betula pendula", "desc", 97.0, 1e-48, 290.0, 194, 97.0),
        ]
        df = build_hit_table(hits)
        div = calculate_diversity(df)
        self.assertEqual(div["pielou_evenness"], 1.0)

    def test_empty_dataframe_returns_zeros(self):
        import pandas as pd
        div = calculate_diversity(pd.DataFrame())
        self.assertEqual(div["species_richness"], 0)
        self.assertEqual(div["shannon_index"], 0.0)

    # ── Fix 7: unclassified queries excluded from diversity ──────────────────
    # Previously "unclassified" was treated as a real taxon, inflating richness
    # and distorting Shannon/Pielou values.

    def test_unclassified_excluded_from_richness(self):
        hits = [
            BlastHit("Q1", 200, 1, "ACC1", "Betula pendula",  "desc", 98.0, 1e-50, 300.0, 196, 98.0),
            BlastHit("Q2", 200, 1, "ACC2", "Pinus sylvestris","desc", 97.0, 1e-48, 290.0, 194, 97.0),
            BlastHit("Q3", 200, 1, "ACC3", "unclassified",    "desc", 78.0, 1e-20, 150.0, 180, 90.0),
        ]
        df = build_hit_table(hits)
        div = calculate_diversity(df)
        self.assertEqual(div["species_richness"], 2)
        self.assertEqual(div["unclassified_queries"], 1)

    def test_unclassified_queries_counted_separately(self):
        hits = [
            BlastHit("Q1", 200, 1, "ACC1", "Betula pendula", "desc", 98.0, 1e-50, 300.0, 196, 98.0),
            BlastHit("Q2", 200, 1, "ACC2", "unclassified",   "desc", 75.0, 1e-15, 120.0, 170, 85.0),
            BlastHit("Q3", 200, 1, "ACC3", "unclassified",   "desc", 72.0, 1e-12, 110.0, 165, 82.0),
        ]
        df = build_hit_table(hits)
        div = calculate_diversity(df)
        self.assertEqual(div["unclassified_queries"], 2)
        self.assertEqual(div["total_queries_with_hit"], 1)

    # ── Fix 8: confidence_flag column present ────────────────────────────────

    def test_confidence_flag_column_exists(self):
        hits = self._make_hits()
        df = build_hit_table(hits)
        self.assertIn("confidence_flag", df.columns)

    def test_confidence_flag_values(self):
        hits = [
            BlastHit("Q1", 200, 1, "ACC1", "Betula pendula",  "desc", 98.5, 1e-50, 300.0, 196, 98.0),
            BlastHit("Q2", 200, 1, "ACC2", "Pinus sylvestris","desc", 93.0, 1e-40, 250.0, 185, 92.0),
            BlastHit("Q3", 200, 1, "ACC3", "Quercus robur",   "desc", 82.0, 1e-20, 150.0, 160, 80.0),
        ]
        df = build_hit_table(hits)
        flags = dict(zip(df["species"], df["confidence_flag"]))
        self.assertEqual(flags["Betula pendula"],   "high")
        self.assertEqual(flags["Pinus sylvestris"], "medium")
        self.assertEqual(flags["Quercus robur"],    "low")


class TestStopWords(unittest.TestCase):
    """Descriptor words (clone, isolate, strain …) must not be returned as epithets."""

    def test_isolate_not_returned_as_epithet(self):
        # "isolate" is a stop word — loop stops, returns genus sp.
        title = "Betula isolate BET001 barcode sequence"
        assert _extract_species(title) == "Betula sp."

    def test_clone_not_returned_as_epithet(self):
        title = "Chlamydomonas clone C4 18S ribosomal RNA"
        assert _extract_species(title) == "Chlamydomonas sp."

    def test_strain_not_returned_as_epithet(self):
        title = "Chlorella strain CCAP211 18S rRNA"
        assert _extract_species(title) == "Chlorella sp."

    def test_species_before_stop_word_still_extracted(self):
        # "pendula" comes before "isolate" — correct species name returned
        title = "Betula pendula isolate BET1 ITS region"
        assert _extract_species(title) == "Betula pendula"


class TestResolveTaxonomy(unittest.TestCase):
    """LCA-based resolve_taxonomy behaviour across confidence levels."""

    def _df(self, hits):
        return build_hit_table(hits)

    def test_high_confidence_species_unchanged(self):
        # ≥97 % → species name accepted directly
        hits = [BlastHit("Q1", 300, 1, "A1", "Betula pendula", "d", 98.5, 1e-80, 400.0, 295, 98.0)]
        df = self._df(hits)
        self.assertEqual(df.loc[0, "resolved_species"], "Betula pendula")

    def test_medium_confidence_genus_consensus(self):
        # 90-96 % with same genus across hits → downgrade to "Genus sp."
        hits = [
            BlastHit("Q1", 390, 1, "A1", "Daphnia pulex",      "d", 93.4, 1e-120, 500.0, 364, 93.0),
            BlastHit("Q1", 390, 2, "A2", "Daphnia magna",      "d", 92.8, 1e-115, 488.0, 361, 92.0),
            BlastHit("Q1", 390, 3, "A3", "Daphnia longispina", "d", 91.9, 1e-108, 470.0, 358, 91.0),
        ]
        df = self._df(hits)
        top = df[df["hit_rank"] == 1].iloc[0]
        self.assertEqual(top["resolved_species"], "Daphnia sp.")

    def test_low_confidence_genus_consensus(self):
        # <90 % but all same genus → "Genus sp."
        hits = [
            BlastHit("Q1", 650, 1, "A1", "Chironomus riparius", "d", 84.1, 1e-130, 560.0, 546, 84.0),
            BlastHit("Q1", 650, 2, "A2", "Chironomus thummi",   "d", 83.8, 1e-128, 552.0, 545, 83.0),
            BlastHit("Q1", 650, 3, "A3", "Chironomus plumosus", "d", 82.9, 1e-123, 530.0, 539, 82.0),
        ]
        df = self._df(hits)
        top = df[df["hit_rank"] == 1].iloc[0]
        self.assertEqual(top["resolved_species"], "Chironomus sp.")

    def test_low_confidence_genus_conflict_returns_unclassified(self):
        # <90 % and hits span multiple genera → unclassified
        hits = [
            BlastHit("Q1", 460, 1, "A1", "Fragilaria capucina", "d", 80.3, 1e-80, 370.0, 369, 80.0),
            BlastHit("Q1", 460, 2, "A2", "Synedra ulna",        "d", 79.7, 1e-77, 358.0, 366, 79.0),
            BlastHit("Q1", 460, 3, "A3", "Aulacoseira granulata","d", 78.8, 1e-73, 342.0, 362, 78.0),
        ]
        df = self._df(hits)
        top = df[df["hit_rank"] == 1].iloc[0]
        self.assertEqual(top["resolved_species"], "unclassified")

    def test_resolved_species_column_present(self):
        hits = [BlastHit("Q1", 300, 1, "A1", "Betula pendula", "d", 98.0, 1e-80, 400.0, 295, 98.0)]
        df = self._df(hits)
        self.assertIn("resolved_species", df.columns)

    def test_uncultured_genus_high_identity_rescued(self):
        # Uncultured but ≥97 % → rescued genus name kept in resolved_species
        hits = [BlastHit("Q1", 520, 1, "A1", "Chlamydomonas sp.", "d", 98.8, 1e-200, 850.0, 514, 98.0)]
        df = self._df(hits)
        self.assertEqual(df.loc[0, "resolved_species"], "Chlamydomonas sp.")


if __name__ == "__main__":
    unittest.main()
