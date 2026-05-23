"""
Regulatory PDF report generator — Phase 2.

Produces a professional, client-ready PDF from pipeline outputs.
The report is designed to meet the evidence standards expected by UK
environmental regulators (Environment Agency, NatureScot, NRW).

Typical usage
-------------
    from src.report import generate_report
    generate_report(
        hit_table=hit_table,
        diversity=diversity,
        output_path=output_dir / "eDNA_Report.pdf",
        site_name="Cannock Chase Pond A",
        sample_date="2026-05-22",
        analyst="Yaw Baah",
        db_version_file=output_dir / "db_version.json",
    )
"""

import json
import logging
import math
from datetime import date as _date
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

log = logging.getLogger(__name__)

# ── Colour palette ────────────────────────────────────────────────────────────
_TEAL_DARK    = colors.HexColor("#1B4F72")
_TEAL_MID     = colors.HexColor("#2E86C1")
_GREEN_DARK   = colors.HexColor("#1E8449")
_GREEN_LIGHT  = colors.HexColor("#EAFAF1")
_AMBER        = colors.HexColor("#D4AC0D")
_AMBER_LIGHT  = colors.HexColor("#FEF9E7")
_RED_DARK     = colors.HexColor("#922B21")
_RED_LIGHT    = colors.HexColor("#FDEDEC")
_BLUE_LIGHT   = colors.HexColor("#EBF5FB")
_GREY_LIGHT   = colors.HexColor("#F2F3F4")
_GREY_MID     = colors.HexColor("#BDC3C7")
_GREY_DARK    = colors.HexColor("#717D7E")
_WHITE        = colors.white
_BLACK        = colors.black

# Confidence colour mapping
_CONF_COLOURS = {
    "high":   (_GREEN_DARK,  _GREEN_LIGHT),
    "medium": (_AMBER,       _AMBER_LIGHT),
    "low":    (_RED_DARK,    _RED_LIGHT),
}

PAGE_W = A4[0] - 5.0 * cm   # usable width (left+right margin = 2.5cm each)


# ── Style factory ─────────────────────────────────────────────────────────────

def _styles() -> Dict[str, ParagraphStyle]:
    s: Dict[str, ParagraphStyle] = {}

    def st(name: str, **kw):
        s[name] = ParagraphStyle(name, **kw)

    st("cover_title",  fontName="Helvetica-Bold",    fontSize=28, textColor=_WHITE,
       leading=34, alignment=TA_CENTER)
    st("cover_sub",    fontName="Helvetica",          fontSize=13,
       textColor=colors.HexColor("#AED6F1"), leading=18, alignment=TA_CENTER)
    st("cover_meta",   fontName="Helvetica",          fontSize=11, textColor=_WHITE,
       leading=16, alignment=TA_CENTER)
    st("section",      fontName="Helvetica-Bold",    fontSize=14, textColor=_TEAL_DARK,
       leading=18, spaceBefore=16, spaceAfter=4)
    st("subsection",   fontName="Helvetica-Bold",    fontSize=11, textColor=_TEAL_MID,
       leading=15, spaceBefore=8, spaceAfter=3)
    st("body",         fontName="Helvetica",          fontSize=10, textColor=_BLACK,
       leading=15, spaceAfter=5, alignment=TA_JUSTIFY)
    st("body_c",       fontName="Helvetica",          fontSize=10, textColor=_BLACK,
       leading=15, alignment=TA_CENTER)
    st("body_r",       fontName="Helvetica",          fontSize=10, textColor=_BLACK,
       leading=15, alignment=TA_RIGHT)
    st("small",        fontName="Helvetica",          fontSize=8.5,
       textColor=_GREY_DARK, leading=12, spaceAfter=3)
    st("small_c",      fontName="Helvetica",          fontSize=8.5,
       textColor=_GREY_DARK, leading=12, alignment=TA_CENTER)
    st("footer",       fontName="Helvetica-Oblique",  fontSize=8,
       textColor=_GREY_DARK, leading=11, alignment=TA_CENTER)
    st("th",           fontName="Helvetica-Bold",    fontSize=9,  textColor=_WHITE,
       leading=12)
    st("td",           fontName="Helvetica",          fontSize=9,  textColor=_BLACK,
       leading=12)
    st("td_c",         fontName="Helvetica",          fontSize=9,  textColor=_BLACK,
       leading=12, alignment=TA_CENTER)
    st("metric_val",   fontName="Helvetica-Bold",    fontSize=20, textColor=_TEAL_DARK,
       leading=24, alignment=TA_CENTER)
    st("metric_label", fontName="Helvetica",          fontSize=9,  textColor=_GREY_DARK,
       leading=12, alignment=TA_CENTER)
    return s


# ── Layout helpers ────────────────────────────────────────────────────────────

def _banner(content, bg: colors.Color, pad_top: int = 12, pad_bot: int = 12,
            left_pad: int = 24) -> Table:
    t = Table([[content]], colWidths=[PAGE_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("LEFTPADDING",   (0, 0), (-1, -1), left_pad),
        ("RIGHTPADDING",  (0, 0), (-1, -1), left_pad),
        ("TOPPADDING",    (0, 0), (-1, -1), pad_top),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad_bot),
    ]))
    return t


def _metric_box(value: str, label: str, s: Dict) -> Table:
    """A tall tile showing one key metric (value + label underneath)."""
    inner = Table(
        [[Paragraph(value, s["metric_val"])],
         [Paragraph(label, s["metric_label"])]],
        colWidths=[4.0 * cm],
    )
    t = Table([[inner]], colWidths=[4.4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), _BLUE_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 1.0, _TEAL_MID),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _confidence_pill(flag: str, s: Dict) -> Table:
    """Inline coloured cell for the confidence_flag column."""
    fg, bg = _CONF_COLOURS.get(flag, (_GREY_DARK, _GREY_LIGHT))
    ps = ParagraphStyle(
        "pill", fontName="Helvetica-Bold", fontSize=8.5,
        textColor=fg, leading=12, alignment=TA_CENTER,
    )
    t = Table([[Paragraph(flag.upper(), ps)]], colWidths=[1.6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("BOX",           (0, 0), (-1, -1), 0.6, fg),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def _info_box(title: str, paras: list, bg: colors.Color,
              border: colors.Color, s: Dict) -> Table:
    inner = ([Paragraph(title, s["subsection"])] if title else []) + paras
    t = Table([[inner]], colWidths=[PAGE_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("BOX",           (0, 0), (-1, -1), 1.2, border),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return t


# ── Report sections ───────────────────────────────────────────────────────────

def _cover_page(story: list, site_name: str, sample_date: str,
                analyst: str, s: Dict) -> None:
    story.append(Spacer(1, 0.6 * cm))
    story.append(_banner(
        Paragraph("eDNA BIODIVERSITY SURVEY", s["cover_title"]),
        _TEAL_DARK, pad_top=34, pad_bot=10,
    ))
    story.append(_banner(
        Paragraph("Species Identification &amp; Biodiversity Report", s["cover_sub"]),
        _TEAL_MID, pad_top=12, pad_bot=12,
    ))
    story.append(_banner(
        Paragraph(
            f"Site: <b>{site_name}</b> &nbsp;·&nbsp; "
            f"Sample date: <b>{sample_date}</b> &nbsp;·&nbsp; "
            f"Analyst: <b>{analyst}</b>",
            s["cover_meta"],
        ),
        _GREEN_DARK, pad_top=9, pad_bot=9,
    ))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        f"Report generated: {_date.today().isoformat()}",
        s["small_c"],
    ))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        "This report presents the results of an environmental DNA (eDNA) "
        "metabarcoding analysis. Sequences extracted from the water sample were "
        "aligned against a reference database using BLAST+. "
        "Species assignments use Lowest Common Ancestor (LCA) logic with "
        "identity-based confidence scoring to ensure biologically accurate "
        "and reproducible identifications.",
        s["body"],
    ))


def _executive_summary(story: list, diversity: Dict[str, Any],
                       n_sequences: int, s: Dict) -> None:
    story.append(PageBreak())
    story.append(Paragraph("1.  Executive Summary", s["section"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_TEAL_DARK))
    story.append(Spacer(1, 0.25 * cm))

    richness  = diversity.get("species_richness", 0)
    shannon   = diversity.get("shannon_index", 0.0)
    evenness  = diversity.get("pielou_evenness", 0.0)
    n_unclass = diversity.get("unclassified_queries", 0)
    n_classif = diversity.get("total_queries_with_hit", 0)

    # Metric tiles
    tiles = [
        (str(richness),           "Species richness"),
        (f"{shannon:.3f}",        "Shannon H'"),
        (f"{evenness:.3f}",       "Pielou J'"),
        (str(n_sequences),        "Sequences analysed"),
        (str(n_unclass),          "Unclassified"),
    ]
    tile_row = [_metric_box(v, lbl, s) for v, lbl in tiles]
    tiles_t = Table([tile_row], colWidths=[PAGE_W / len(tile_row)] * len(tile_row))
    tiles_t.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]))
    story.append(tiles_t)
    story.append(Spacer(1, 0.3 * cm))

    # Plain-English interpretation
    if richness == 0:
        health = "No taxa were successfully identified. Review sequence quality."
    elif richness <= 3:
        health_desc = "low"
    elif richness <= 8:
        health_desc = "moderate"
    else:
        health_desc = "high"

    if richness > 0:
        if evenness >= 0.8:
            even_desc = "highly even (community dominated by no single taxon)"
        elif evenness >= 0.5:
            even_desc = "moderately even"
        else:
            even_desc = "uneven (one or a few taxa dominate)"
        health = (
            f"The sample yielded <b>{richness} distinct taxon/taxa</b>, "
            f"indicating a <b>{health_desc}</b> species richness. "
            f"Shannon diversity of <b>{shannon:.3f}</b> reflects a "
            f"{even_desc} community (Pielou J' = {evenness:.3f}). "
            f"{n_unclass} sequence(s) could not be classified and are excluded "
            "from diversity calculations."
        )

    story.append(Paragraph(health, s["body"]))

    # Confidence breakdown
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph("Confidence level guide:", s["subsection"]))
    conf_data = [
        [Paragraph("Level", s["th"]),
         Paragraph("Identity threshold", s["th"]),
         Paragraph("Interpretation", s["th"])],
        [_confidence_pill("high",   s),
         Paragraph("≥ 97 %", s["td_c"]),
         Paragraph("Species-level assignment reliable", s["td"])],
        [_confidence_pill("medium", s),
         Paragraph("90 – 96 %", s["td_c"]),
         Paragraph("Genus-level reliable; species uncertain — reported as Genus sp.", s["td"])],
        [_confidence_pill("low",    s),
         Paragraph("&lt; 90 %", s["td_c"]),
         Paragraph("Alignment too divergent; treat with caution", s["td"])],
    ]
    conf_t = Table(conf_data, colWidths=[2.0 * cm, 3.0 * cm, PAGE_W - 5.0 * cm])
    conf_t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  _TEAL_DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _GREY_LIGHT]),
        ("BOX",            (0, 0), (-1, -1), 0.8, _GREY_MID),
        ("INNERGRID",      (0, 0), (-1, -1), 0.4, _GREY_MID),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(conf_t)


def _species_table(story: list, df: pd.DataFrame, s: Dict) -> None:
    story.append(PageBreak())
    story.append(Paragraph("2.  Species Identification Table", s["section"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_TEAL_DARK))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(
        "The table below shows the top BLAST hit for each query sequence after "
        "LCA-based taxonomy resolution. "
        "<b>Resolved species</b> is the biologically honest classification — "
        "it may be downgraded from the raw BLAST hit when identity falls below "
        "the species-level threshold. "
        "The raw BLAST hit title is preserved in the <i>Accession</i> column for audit.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))

    species_col = "resolved_species" if "resolved_species" in df.columns else "species"
    top_hits = df[df["hit_rank"] == 1].copy()

    # Column widths
    col_widths = [
        0.8 * cm,   # #
        4.5 * cm,   # Resolved species
        1.7 * cm,   # Confidence
        1.8 * cm,   # Identity %
        2.0 * cm,   # E-value
        PAGE_W - (0.8 + 4.5 + 1.7 + 1.8 + 2.0) * cm,  # Accession
    ]

    header = [
        Paragraph("#",               s["th"]),
        Paragraph("Resolved species",s["th"]),
        Paragraph("Confidence",      s["th"]),
        Paragraph("Identity %",      s["th"]),
        Paragraph("E-value",         s["th"]),
        Paragraph("Accession",       s["th"]),
    ]
    table_data = [header]

    for i, (_, row) in enumerate(top_hits.iterrows(), start=1):
        evalue = row.get("evalue", "")
        try:
            evalue_str = f"{float(evalue):.1e}"
        except (TypeError, ValueError):
            evalue_str = str(evalue)

        identity = row.get("identity_pct", "")
        try:
            identity_str = f"{float(identity):.1f} %"
        except (TypeError, ValueError):
            identity_str = str(identity)

        conf_flag = str(row.get("confidence_flag", "low")).lower()
        accession = str(row.get("accession", ""))[:30]

        table_data.append([
            Paragraph(str(i),          s["td_c"]),
            Paragraph(f"<i>{str(row.get(species_col, ''))}</i>", s["td"]),
            _confidence_pill(conf_flag, s),
            Paragraph(identity_str,    s["td_c"]),
            Paragraph(evalue_str,      s["td_c"]),
            Paragraph(accession,       s["td"]),
        ])

    sp_t = Table(table_data, colWidths=col_widths, repeatRows=1)
    row_bgs = []
    for i in range(1, len(table_data)):
        bg = _WHITE if i % 2 == 1 else _GREY_LIGHT
        conf = str(top_hits.iloc[i - 1].get("confidence_flag", "")).lower()
        if conf == "low":
            bg = _RED_LIGHT
        row_bgs.append(("BACKGROUND", (0, i), (-1, i), bg))

    sp_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  _TEAL_DARK),
        ("BOX",           (0, 0), (-1, -1), 0.8, _GREY_MID),
        ("INNERGRID",     (0, 0), (-1, -1), 0.4, _GREY_MID),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ] + row_bgs))
    story.append(sp_t)


def _diversity_section(story: list, diversity: Dict[str, Any], s: Dict) -> None:
    story.append(PageBreak())
    story.append(Paragraph("3.  Biodiversity Metrics", s["section"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))

    # Metrics table
    story.append(Paragraph("Alpha-diversity indices:", s["subsection"]))
    richness = diversity.get("species_richness", 0)
    shannon  = diversity.get("shannon_index", 0.0)
    evenness = diversity.get("pielou_evenness", 0.0)

    # Shannon max = ln(S)
    shannon_max = math.log(richness) if richness > 1 else 1.0

    metrics_data = [
        [Paragraph("Metric",       s["th"]),
         Paragraph("Value",        s["th"]),
         Paragraph("Formula",      s["th"]),
         Paragraph("Interpretation", s["th"])],
        [Paragraph("Species richness (S)", s["td"]),
         Paragraph(str(richness),   s["td_c"]),
         Paragraph("Count of distinct classified taxa", s["td"]),
         Paragraph(
             "Low (&lt;3) / Moderate (3–8) / High (&gt;8)",
             s["td"])],
        [Paragraph("Shannon index (H')", s["td"]),
         Paragraph(f"{shannon:.4f}", s["td_c"]),
         Paragraph("-Σ pᵢ · ln(pᵢ)", s["td"]),
         Paragraph(
             f"Max possible for S={richness}: {shannon_max:.4f}. "
             "Higher = more diverse.",
             s["td"])],
        [Paragraph("Pielou evenness (J')", s["td"]),
         Paragraph(f"{evenness:.4f}", s["td_c"]),
         Paragraph("H' / ln(S)", s["td"]),
         Paragraph(
             "0 = one species dominates; 1 = perfectly even community.",
             s["td"])],
    ]
    met_t = Table(
        metrics_data,
        colWidths=[3.5 * cm, 2.0 * cm, 3.5 * cm, PAGE_W - 9.0 * cm],
    )
    met_t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  _TEAL_DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _GREY_LIGHT]),
        ("BOX",            (0, 0), (-1, -1), 0.8, _GREY_MID),
        ("INNERGRID",      (0, 0), (-1, -1), 0.4, _GREY_MID),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(met_t)
    story.append(Spacer(1, 0.3 * cm))

    # Species count table
    story.append(Paragraph("Taxon read counts (top-hit abundance):", s["subsection"]))
    counts: Dict[str, int] = diversity.get("species_counts", {})
    if counts:
        total = sum(counts.values())
        count_data = [
            [Paragraph("Taxon",           s["th"]),
             Paragraph("Read count",      s["th"]),
             Paragraph("Relative abundance (%)", s["th"])],
        ]
        for sp, cnt in sorted(counts.items(), key=lambda x: -x[1]):
            pct = 100.0 * cnt / total if total > 0 else 0.0
            bar_fill = int(pct / 5)   # 1 block per 5%
            bar_empty = 20 - bar_fill
            bar = "[" + "#" * bar_fill + "." * bar_empty + "]"
            count_data.append([
                Paragraph(f"<i>{sp}</i>",        s["td"]),
                Paragraph(str(cnt),               s["td_c"]),
                Paragraph(f"{pct:.1f} %  {bar}",  s["td"]),
            ])
        cnt_t = Table(
            count_data,
            colWidths=[5.0 * cm, 2.4 * cm, PAGE_W - 7.4 * cm],
            repeatRows=1,
        )
        cnt_t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  _GREEN_DARK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _GREY_LIGHT]),
            ("BOX",            (0, 0), (-1, -1), 0.8, _GREY_MID),
            ("INNERGRID",      (0, 0), (-1, -1), 0.4, _GREY_MID),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
            ("TOPPADDING",     (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(cnt_t)
    else:
        story.append(Paragraph("No classified taxa to display.", s["body"]))


def _methodology_section(story: list, db_version: str, analyst: str,
                         site_name: str, sample_date: str, s: Dict) -> None:
    story.append(PageBreak())
    story.append(Paragraph("4.  Methodology", s["section"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))

    story.append(_info_box(
        "Bioinformatics pipeline",
        [Paragraph(
            "Environmental DNA sequences were quality-filtered and aligned against "
            "the reference database using <b>NCBI BLAST+</b> (blastn). "
            "A maximum of five hits per sequence were retained (E-value threshold: "
            "1 × 10<super>-10</super>). "
            "Species assignments were determined using <b>Lowest Common Ancestor "
            "(LCA)</b> logic: sequences with ≥ 97 % identity to a reference are "
            "assigned at species level; 90–96 % identity yields genus-level "
            "assignment; &lt; 90 % identity returns 'unclassified'. "
            "Diversity indices (Shannon H', Pielou J') were computed from "
            "top-hit read counts, excluding unclassified sequences.",
            s["body"],
        )],
        bg=_BLUE_LIGHT, border=_TEAL_MID, s=s,
    ))
    story.append(Spacer(1, 0.2 * cm))

    story.append(_info_box(
        "Reference database",
        [Paragraph(
            f"<b>Version:</b> {db_version}",
            s["body"],
        ),
         Paragraph(
            "The exact database version is recorded in <b>db_version.json</b> "
            "alongside the raw results files to ensure reproducibility. "
            "Re-running the pipeline against this database snapshot will yield "
            "identical species assignments.",
            s["body"],
        )],
        bg=_GREEN_LIGHT, border=_GREEN_DARK, s=s,
    ))
    story.append(Spacer(1, 0.2 * cm))

    # Sample metadata
    meta_data = [
        [Paragraph("Field",   s["th"]), Paragraph("Value", s["th"])],
        [Paragraph("Site",    s["td"]), Paragraph(site_name,   s["td"])],
        [Paragraph("Sample date", s["td"]), Paragraph(sample_date, s["td"])],
        [Paragraph("Analyst", s["td"]), Paragraph(analyst,    s["td"])],
        [Paragraph("Report date", s["td"]),
         Paragraph(_date.today().isoformat(), s["td"])],
    ]
    meta_t = Table(meta_data, colWidths=[4.0 * cm, PAGE_W - 4.0 * cm])
    meta_t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  _TEAL_DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_WHITE, _GREY_LIGHT]),
        ("BOX",            (0, 0), (-1, -1), 0.8, _GREY_MID),
        ("INNERGRID",      (0, 0), (-1, -1), 0.4, _GREY_MID),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta_t)
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "This report was produced by the eDNA Sequence Analysis Pipeline "
        "(github.com/ybaah-biotech/eDNA-sequence-analysis). "
        "Results should be interpreted alongside field collection metadata, "
        "sample quality indicators, and relevant ecological context.",
        s["small"],
    ))


# ── Public API ────────────────────────────────────────────────────────────────

def generate_report(
    hit_table: pd.DataFrame,
    diversity: Dict[str, Any],
    output_path: Path,
    site_name: str = "Unknown site",
    sample_date: str = "",
    analyst: str = "Unknown",
    db_version_file: Optional[Path] = None,
) -> Path:
    """
    Generate a regulatory-grade PDF report from pipeline outputs.

    Parameters
    ----------
    hit_table:
        DataFrame from :func:`~src.summarise.build_hit_table`.
    diversity:
        Dict from :func:`~src.summarise.calculate_diversity`.
    output_path:
        Destination PDF path (e.g. ``data/results/eDNA_Report.pdf``).
    site_name:
        Human-readable site name for the cover page.
    sample_date:
        ISO date string (YYYY-MM-DD) or free text.
    analyst:
        Name of the analyst for the cover page.
    db_version_file:
        Path to ``db_version.json`` written by the local BLAST runner.
        If absent or unreadable, the DB version is shown as 'NCBI web BLAST
        (version not recorded)'.

    Returns
    -------
    Path
        The path of the generated PDF.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Read DB version
    db_version = "NCBI web BLAST (version not recorded)"
    if db_version_file and Path(db_version_file).exists():
        try:
            meta = json.loads(Path(db_version_file).read_text(encoding="utf-8"))
            db_version = meta.get("db_version", db_version)
        except Exception:  # noqa: BLE001
            pass

    if not sample_date:
        sample_date = _date.today().isoformat()

    n_sequences = len(hit_table["query_id"].unique()) if not hit_table.empty else 0

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
        title=f"eDNA Report — {site_name}",
        author=analyst,
        subject="Environmental DNA Biodiversity Survey",
    )

    s = _styles()
    story: list = []

    _cover_page(story, site_name, sample_date, analyst, s)
    _executive_summary(story, diversity, n_sequences, s)
    _species_table(story, hit_table, s)
    _diversity_section(story, diversity, s)
    _methodology_section(story, db_version, analyst, site_name, sample_date, s)

    doc.build(story)
    log.info(f"Report generated -> {output_path}")
    return output_path
