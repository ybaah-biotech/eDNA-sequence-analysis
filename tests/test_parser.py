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
    def test_standard_genbank_title(self):
        title = "gb|AJ312462.1| Betula pendula isolate BET1 internal transcribed spacer"
        assert _extract_species(title) == "Betula pendula"

    def test_title_without_accession_prefix(self):
        title = "Alternaria alternata strain CBS 916.96 ITS region"
        assert _extract_species(title) == "Alternaria alternata"

    def test_organism_in_brackets_fallback(self):
        title = "predicted mRNA, partial sequence [Quercus robur]"
        assert _extract_species(title) == "Quercus robur"


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
        empty_xml = '<?xml version="1.0"?><BlastOutput><BlastOutput_program>blastn</BlastOutput_program><BlastOutput_version>2.14</BlastOutput_version><BlastOutput_db>nt</BlastOutput_db><BlastOutput_iterations></BlastOutput_iterations></BlastOutput>'
        xml_path = self._write_xml(empty_xml)
        hits = parse_blast_xml(xml_path)
        self.assertEqual(hits, [])
        xml_path.unlink()


class TestBiodiversityMetrics(unittest.TestCase):
    def _make_hits(self) -> list:
        return [
            BlastHit("Q1", 200, 1, "ACC1", "Betula pendula",    "desc", 98.0, 1e-50, 300.0, 196, 98.0),
            BlastHit("Q2", 500, 1, "ACC2", "Alternaria alternata", "desc", 97.5, 1e-90, 450.0, 480, 96.0),
            BlastHit("Q3", 350, 1, "ACC3", "Pinus sylvestris",  "desc", 96.0, 1e-60, 320.0, 340, 97.0),
            BlastHit("Q4", 480, 1, "ACC4", "Alternaria alternata", "desc", 99.0, 1e-95, 460.0, 462, 96.0),
        ]

    def test_species_richness(self):
        import pandas as pd
        hits = self._make_hits()
        df = build_hit_table(hits)
        div = calculate_diversity(df)
        self.assertEqual(div["species_richness"], 3)

    def test_shannon_positive_for_multiple_species(self):
        import pandas as pd
        hits = self._make_hits()
        df = build_hit_table(hits)
        div = calculate_diversity(df)
        self.assertGreater(div["shannon_index"], 0)

    def test_single_species_evenness_is_one(self):
        import pandas as pd
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


if __name__ == "__main__":
    unittest.main()
