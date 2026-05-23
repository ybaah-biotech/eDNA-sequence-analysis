#!/usr/bin/env python3
"""
Mock pond eDNA run — demonstrates the full pipeline without NCBI network calls.

Generates synthetic BLAST XML results for eight representative UK pond organisms
and runs the complete parser → LCA resolution → diversity pipeline. Each sample
is chosen to exercise a different classification scenario:

  POND_001  Chlorella vulgaris         high-confidence (98.5 %)
  POND_002  Microcystis aeruginosa     high-confidence (99.2 %)
  POND_003  uncultured Chlamydomonas   uncultured genus rescue  → Chlamydomonas sp.
  POND_004  Daphnia spp.               medium-confidence LCA    → Daphnia sp.
  POND_005  Chironomus spp.            low-confidence LCA       → Chironomus sp.
  POND_006  mixed diatom genera        LCA genus conflict       → unclassified
  POND_007  Phragmites australis       high-confidence (97.8 %)
  POND_008  Microcystis aeruginosa     second bloom sequence

Usage:
    python mock_run.py
"""

import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.parser import parse_all_results
from src.report import generate_report
from src.summarise import build_hit_table, calculate_diversity, export_results
from src.utils import setup_logging


# ── Synthetic BLAST XML generation ──────────────────────────────────────────

def _hsp(identity_count: int, align_len: int, query_len: int,
         evalue: str, bits: float) -> str:
    return textwrap.dedent(f"""\
            <Hsp>
              <Hsp_num>1</Hsp_num>
              <Hsp_bit-score>{bits}</Hsp_bit-score>
              <Hsp_score>{int(bits)}</Hsp_score>
              <Hsp_evalue>{evalue}</Hsp_evalue>
              <Hsp_query-from>1</Hsp_query-from>
              <Hsp_query-to>{query_len}</Hsp_query-to>
              <Hsp_hit-from>1</Hsp_hit-from>
              <Hsp_hit-to>{align_len}</Hsp_hit-to>
              <Hsp_query-frame>1</Hsp_query-frame>
              <Hsp_hit-frame>1</Hsp_hit-frame>
              <Hsp_identity>{identity_count}</Hsp_identity>
              <Hsp_positive>{identity_count}</Hsp_positive>
              <Hsp_gaps>0</Hsp_gaps>
              <Hsp_align-len>{align_len}</Hsp_align-len>
              <Hsp_qseq>ACGT</Hsp_qseq>
              <Hsp_hseq>ACGT</Hsp_hseq>
              <Hsp_midline>||||</Hsp_midline>
            </Hsp>""")


def _hit(num: int, accession: str, title: str,
         identity_pct: float, align_len: int, query_len: int,
         evalue: str, bits: float) -> str:
    identity_count = int(align_len * identity_pct / 100)
    return textwrap.dedent(f"""\
        <Hit>
          <Hit_num>{num}</Hit_num>
          <Hit_id>gi|{num * 1000}|gb|{accession}.1|</Hit_id>
          <Hit_def>{title}</Hit_def>
          <Hit_accession>{accession}</Hit_accession>
          <Hit_len>{align_len + 8}</Hit_len>
          <Hit_hsps>
{_hsp(identity_count, align_len, query_len, evalue, bits)}
          </Hit_hsps>
        </Hit>""")


def _blast_xml(query_id: str, query_def: str, query_len: int,
               hits: list) -> str:
    """
    hits: list of (accession, title, identity_pct, align_len, evalue_str, bits)
    """
    hit_blocks = "\n".join(
        _hit(i + 1, acc, title, ident, alen, query_len, ev, bits)
        for i, (acc, title, ident, alen, ev, bits) in enumerate(hits)
    )
    return textwrap.dedent(f"""\
<?xml version="1.0"?>
<BlastOutput>
  <BlastOutput_program>blastn</BlastOutput_program>
  <BlastOutput_version>BLASTN 2.14.0+</BlastOutput_version>
  <BlastOutput_reference>Reference</BlastOutput_reference>
  <BlastOutput_db>nt</BlastOutput_db>
  <BlastOutput_query-ID>Query_1</BlastOutput_query-ID>
  <BlastOutput_query-def>{query_id} {query_def}</BlastOutput_query-def>
  <BlastOutput_query-len>{query_len}</BlastOutput_query-len>
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
      <Iteration_query-def>{query_id} {query_def}</Iteration_query-def>
      <Iteration_query-len>{query_len}</Iteration_query-len>
      <Iteration_hits>
{hit_blocks}
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


# ── Pond sample definitions ──────────────────────────────────────────────────
# Format: (query_id, query_def, query_len, [hits])
# Each hit: (accession, blast_title, identity_pct, align_len, evalue, bits)

POND_SAMPLES = [
    (
        "POND_001", "18S_rRNA_green_alga", 480,
        [
            ("KX580994", "Chlorella vulgaris strain CCAP 211 18S ribosomal RNA gene partial",       98.5, 472, "1e-210", 850.0),
            ("KX580995", "Chlorella sorokiniana strain CS-2 18S ribosomal RNA partial sequence",    97.1, 468, "1e-195", 805.0),
            ("KX580996", "Chlorella variabilis NC64A 18S ribosomal RNA partial",                    96.8, 465, "1e-190", 790.0),
        ],
    ),
    (
        "POND_002", "16S_rRNA_cyanobacterium", 410,
        [
            ("AB001339", "Microcystis aeruginosa strain NIES-843 16S ribosomal RNA gene",           99.2, 406, "1e-195", 800.0),
            ("AB001340", "Microcystis wesenbergii strain FACHB-908 16S ribosomal RNA partial",      98.0, 402, "1e-185", 765.0),
        ],
    ),
    (
        # Uncultured genus rescue scenario:
        # Top hit title says "uncultured Chlamydomonas sp." — old code returned
        # "unclassified"; new _extract_species rescues this to "Chlamydomonas sp."
        "POND_003", "18S_rRNA_unknown_green_alga", 520,
        [
            ("HQ659218", "uncultured Chlamydomonas sp. clone ENV45 18S ribosomal RNA partial",      98.8, 514, "1e-220", 890.0),
            ("HQ659219", "uncultured Chlamydomonas reinhardtii clone ENV46 18S partial sequence",   97.9, 508, "1e-208", 845.0),
            ("KJ133657", "Chlamydomonas reinhardtii isolate CC-503 18S ribosomal RNA",              97.2, 505, "1e-200", 820.0),
        ],
    ),
    (
        # Medium-confidence LCA scenario (90-96 %):
        # Three Daphnia species at 93, 92, 91 % → all agree on genus Daphnia
        # → resolved to "Daphnia sp." rather than mis-assigning species name
        "POND_004", "18S_rRNA_water_flea", 390,
        [
            ("AJ130819", "Daphnia pulex isolate DP4 18S ribosomal RNA partial sequence",            93.4, 364, "1e-140", 580.0),
            ("AJ130820", "Daphnia magna isolate DM12 18S ribosomal RNA partial",                    92.8, 361, "1e-135", 560.0),
            ("AJ130821", "Daphnia longispina clone DL7 18S ribosomal RNA partial sequence",         91.9, 358, "1e-128", 535.0),
        ],
    ),
    (
        # Low-confidence LCA scenario (<90 %): all hits within Chironomus genus
        # → single-genus consensus → "Chironomus sp."
        "POND_005", "COI_midge_larva", 650,
        [
            ("KM078453", "Chironomus riparius voucher CHR22 cytochrome oxidase subunit I partial",  84.1, 546, "1e-150", 620.0),
            ("KM078454", "Chironomus thummi strain EMBL cytochrome oxidase subunit I partial",      83.8, 545, "1e-148", 612.0),
            ("KM078455", "Chironomus plumosus isolate CP9 cytochrome oxidase subunit 1 partial",    82.9, 539, "1e-143", 590.0),
        ],
    ),
    (
        # Low-confidence LCA scenario: hits span three different diatom genera
        # → no genus consensus → "unclassified"
        "POND_006", "18S_rRNA_diatom", 460,
        [
            ("AY485484", "Fragilaria capucina strain FC1 18S ribosomal RNA partial sequence",       80.3, 369, "1e-90",  380.0),
            ("AY485485", "Synedra ulna isolate SU3 18S ribosomal RNA partial",                      79.7, 366, "1e-87",  368.0),
            ("AY485486", "Aulacoseira granulata clone AG5 18S ribosomal RNA partial sequence",      78.8, 362, "1e-83",  352.0),
        ],
    ),
    (
        "POND_007", "trnL_aquatic_macrophyte", 300,
        [
            ("AJ232936", "Phragmites australis voucher PA44 trnL intron partial sequence",          97.8, 293, "1e-130", 530.0),
            ("AJ232937", "Phragmites communis strain PC2 trnL partial",                             96.3, 289, "1e-122", 498.0),
        ],
    ),
    (
        # Second bloom sequence — Microcystis aeruginosa again (realistic in bloom events)
        "POND_008", "16S_rRNA_cyanobacterium_2", 415,
        [
            ("AB001341", "Microcystis aeruginosa strain PCC 7806 16S ribosomal RNA gene partial",   99.0, 411, "1e-193", 795.0),
            ("AB001342", "Microcystis flos-aquae strain MFA3 16S ribosomal RNA partial",            97.6, 405, "1e-182", 750.0),
        ],
    ),
]


# ── Runner ───────────────────────────────────────────────────────────────────

def main() -> None:
    setup_logging("WARNING")  # suppress info noise for the demo

    with tempfile.TemporaryDirectory() as tmpdir:
        xml_dir = Path(tmpdir) / "xml"
        xml_dir.mkdir()
        out_dir = Path(tmpdir) / "results"
        out_dir.mkdir()

        # Write mock XML files
        for query_id, query_def, query_len, hits in POND_SAMPLES:
            xml_path = xml_dir / f"{query_id}.xml"
            xml_path.write_text(
                _blast_xml(query_id, query_def, query_len, hits),
                encoding="utf-8",
            )

        # Parse
        all_hits = parse_all_results(xml_dir, max_hits=5, evalue_threshold=1e-10)

        # Build table (applies LCA + confidence flagging internally)
        df = build_hit_table(all_hits)

        # Diversity
        diversity = calculate_diversity(df)

        # Export CSVs
        export_results(df, diversity, out_dir)

        # Generate demo PDF report (written to Desktop so you can open it easily)
        demo_report = Path.home() / "OneDrive" / "Desktop" / \
            "edna bioinformatics learning" / "DEMO_eDNA_Report_Cannock_Chase.pdf"
        generate_report(
            hit_table=df,
            diversity=diversity,
            output_path=demo_report,
            site_name="Cannock Chase Pond A",
            sample_date="2026-05-22",
            analyst="Yaw Baah",
        )

        # ── Print results ────────────────────────────────────────────────────
        W = 76
        print()
        print("=" * W)
        print("  eDNA MOCK RUN — FRESHWATER POND SAMPLE")
        print(f"  {len(POND_SAMPLES)} sequences  |  database: nt (simulated)")
        print("=" * W)

        # Per-query summary (rank-1 hits only)
        top = df[df["hit_rank"] == 1].copy()
        print()
        print(f"  {'QUERY':<12}  {'RAW BLAST HIT':<28}  {'IDENT':>6}  {'FLAG':>6}  {'RESOLVED TAXON':<28}  NOTE")
        print("  " + "-" * (W - 2))

        scenario_notes = {
            "POND_003": "uncultured rescue",
            "POND_004": "LCA medium (genus)",
            "POND_005": "LCA low (genus)",
            "POND_006": "LCA low (conflict)",
        }

        for _, row in top.sort_values("query_id").iterrows():
            raw     = row["species"][:26]
            resolve = row["resolved_species"][:26]
            ident   = f"{row['identity_pct']:.1f}%"
            flag    = row["confidence_flag"]
            note    = scenario_notes.get(row["query_id"], "")
            changed = " *" if resolve != raw else ""
            print(f"  {row['query_id']:<12}  {raw:<28}  {ident:>6}  {flag:>6}  {resolve:<28}  {note}{changed}")

        print()
        print("  (* resolved_species differs from raw BLAST hit)")

        # Diversity summary
        print()
        print("  BIODIVERSITY SUMMARY")
        print("  " + "-" * (W - 2))
        d = diversity
        print(f"  Species richness   : {d['species_richness']}")
        print(f"  Shannon H'         : {d['shannon_index']:.4f}")
        print(f"  Pielou J'          : {d['pielou_evenness']:.4f}")
        print(f"  Classified queries : {d['total_queries_with_hit']}")
        print(f"  Unclassified       : {d['unclassified_queries']}")
        print()
        print("  TAXON COUNTS (resolved)")
        print("  " + "-" * (W - 2))
        for taxon, count in sorted(d["species_counts"].items(), key=lambda x: -x[1]):
            bar = "#" * count
            print(f"  {taxon:<32}  {count}  {bar}")
        print()
        print("=" * W)
        print()

        # Show CSV paths note
        print(f"  Output files written to: {out_dir}")
        print(f"  blast_hit_table.csv      — {len(df)} rows")
        print(f"  biodiversity_summary.csv — {5 + len(d['species_counts'])} rows")
        print(f"  PDF report               — {demo_report}")
        print()


if __name__ == "__main__":
    main()
