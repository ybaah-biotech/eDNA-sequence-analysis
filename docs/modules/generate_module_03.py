#!/usr/bin/env python3
"""
Generate Module 03 — Regulatory PDF Reports & Data Interpretation
eDNA Bioinformatics Learning Series
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)

OUTPUT = Path(__file__).parent / "Module_03_Regulatory_Reports_and_Interpretation.pdf"

TEAL_DARK    = colors.HexColor("#1B4F72")
TEAL_MID     = colors.HexColor("#2E86C1")
GREEN_DARK   = colors.HexColor("#1E8449")
GREEN_LIGHT  = colors.HexColor("#EAFAF1")
BLUE_LIGHT   = colors.HexColor("#EBF5FB")
AMBER        = colors.HexColor("#D4AC0D")
AMBER_LIGHT  = colors.HexColor("#FEF9E7")
RED_DARK     = colors.HexColor("#922B21")
RED_LIGHT    = colors.HexColor("#FDEDEC")
PURPLE_DARK  = colors.HexColor("#6C3483")
PURPLE_LIGHT = colors.HexColor("#F5EEF8")
GREY_LIGHT   = colors.HexColor("#F2F3F4")
GREY_MID     = colors.HexColor("#BDC3C7")
GREY_DARK    = colors.HexColor("#717D7E")
WHITE        = colors.white
BLACK        = colors.black


def make_styles():
    s = {}

    def st(name, **kw):
        s[name] = ParagraphStyle(name, **kw)

    st("title_main",   fontName="Helvetica-Bold",    fontSize=24, textColor=WHITE,
       leading=30, alignment=TA_CENTER)
    st("title_sub",    fontName="Helvetica",          fontSize=13,
       textColor=colors.HexColor("#AED6F1"), leading=18, alignment=TA_CENTER)
    st("module_label", fontName="Helvetica-Bold",    fontSize=44,
       textColor=colors.HexColor("#AED6F1"), leading=52, alignment=TA_CENTER)
    st("h1",           fontName="Helvetica-Bold",    fontSize=15, textColor=TEAL_DARK,
       leading=20, spaceBefore=14, spaceAfter=4)
    st("h2",           fontName="Helvetica-Bold",    fontSize=12, textColor=TEAL_MID,
       leading=16, spaceBefore=10, spaceAfter=3)
    st("body",         fontName="Helvetica",          fontSize=10, textColor=BLACK,
       leading=15, spaceAfter=5, alignment=TA_JUSTIFY)
    st("bullet",       fontName="Helvetica",          fontSize=10, textColor=BLACK,
       leading=15, leftIndent=14, spaceAfter=3)
    st("box_head",     fontName="Helvetica-Bold",    fontSize=10, textColor=TEAL_DARK,
       leading=14, spaceAfter=3)
    st("box_body",     fontName="Helvetica",          fontSize=10, textColor=BLACK,
       leading=14, alignment=TA_JUSTIFY)
    st("code",         fontName="Courier",            fontSize=8.5,
       textColor=colors.HexColor("#1A5276"), leading=13, leftIndent=6, spaceAfter=3)
    st("caption",      fontName="Helvetica-Oblique", fontSize=8.5,
       textColor=GREY_DARK, leading=12, alignment=TA_CENTER)
    st("gl_term",      fontName="Helvetica-Bold",    fontSize=10, textColor=GREEN_DARK,
       leading=13, spaceAfter=1)
    st("gl_def",       fontName="Helvetica",          fontSize=10, textColor=BLACK,
       leading=13, leftIndent=10, spaceAfter=7)
    st("th",           fontName="Helvetica-Bold",    fontSize=9.5, textColor=WHITE, leading=13)
    st("td",           fontName="Helvetica",          fontSize=9.5, textColor=BLACK, leading=13)
    st("td_c",         fontName="Helvetica",          fontSize=9.5, textColor=BLACK,
       leading=13, alignment=TA_CENTER)
    return s


def coloured_banner(text_para, bg, col_w=14 * cm, pad_top=12, pad_bot=12):
    t = Table([[text_para]], colWidths=[col_w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("LEFTPADDING",   (0, 0), (-1, -1), 24),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 24),
        ("TOPPADDING",    (0, 0), (-1, -1), pad_top),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad_bot),
    ]))
    return t


def info_box(title, paras, bg, border, s):
    inner = ([Paragraph(title, s["box_head"])] if title else []) + paras
    t = Table([[inner]], colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("BOX",           (0, 0), (-1, -1), 1.2, border),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def two_col(rows, col_a_w=4.0 * cm, header_bg=TEAL_DARK, s=None):
    th = ParagraphStyle("th2", fontName="Helvetica-Bold", fontSize=9.5,
                        textColor=WHITE, leading=13)
    td = ParagraphStyle("td2", fontName="Helvetica", fontSize=9.5,
                        textColor=BLACK, leading=13)
    data = []
    for i, (a, b) in enumerate(rows):
        data.append([Paragraph(a, th if i == 0 else td),
                     Paragraph(b, th if i == 0 else td)])
    col_b = 14 * cm - col_a_w
    t = Table(data, colWidths=[col_a_w, col_b])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  header_bg),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ("BOX",            (0, 0), (-1, -1), 0.8, GREY_MID),
        ("INNERGRID",      (0, 0), (-1, -1), 0.4, GREY_MID),
        ("LEFTPADDING",    (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 7),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def build(s):
    story = []

    # ── TITLE PAGE ────────────────────────────────────────────────────────────
    story.append(coloured_banner(
        Paragraph("MODULE 03", s["module_label"]), TEAL_DARK, pad_top=28, pad_bot=6
    ))
    story.append(coloured_banner(
        Paragraph("Regulatory Reports &amp; Data Interpretation", s["title_main"]),
        TEAL_MID, pad_top=14, pad_bot=14,
    ))
    story.append(coloured_banner(
        Paragraph("eDNA Bioinformatics Learning Series  ·  Yaw Baah", s["title_sub"]),
        GREEN_DARK, pad_top=7, pad_bot=7,
    ))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(
        "Modules 01 and 02 covered how the pipeline identifies species from sequences. "
        "This module focuses on what happens with those identifications: how to "
        "<b>interpret the results honestly</b>, how to <b>build a report a regulator "
        "will trust</b>, and what the numbers — Shannon H', Pielou J', confidence "
        "flags — actually mean for a real environmental survey.",
        s["body"],
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(info_box(
        "What you will learn",
        [Paragraph(
            "1. What a regulatory eDNA report must contain  &nbsp; "
            "2. How to read a confidence flag  &nbsp; "
            "3. Shannon H' and Pielou J' explained in plain English  &nbsp; "
            "4. How to generate your report with --report  &nbsp; "
            "5. The four sections of the PDF report  &nbsp; "
            "6. Common interpretation mistakes  &nbsp; "
            "7. Glossary",
            s["box_body"],
        )],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s,
    ))

    # ── 1. WHY A REGULATORY REPORT? ───────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("1.  Why Regulatory Reports Matter", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Environmental DNA surveys are increasingly accepted by UK regulators "
        "as evidence for species presence or absence — but only when the data is "
        "<b>traceable, reproducible, and interpreted within known confidence limits</b>. "
        "A results CSV file is not a report. A regulator needs to know:",
        s["body"],
    ))
    for b in [
        "Which species were detected and at what confidence level?",
        "What database and what version was used to identify them?",
        "How diverse is the community — and how was that measured?",
        "Who ran the analysis and when?",
        "Were any sequences unclassified — and why does that matter?",
    ]:
        story.append(Paragraph(f"• {b}", s["bullet"]))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(
        "The pipeline's PDF report answers all five questions automatically. "
        "It is designed around the evidence standards in the <b>GB Non-Native Species "
        "Secretariat</b> and <b>Environment Agency</b> eDNA guidance, and the "
        "<b>NERC-funded eDNA Metabarcoding Framework</b>.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(info_box(
        "Who uses eDNA reports?",
        [
            Paragraph(
                "• <b>Environment Agency</b> — water quality, invasive species surveillance",
                s["box_body"],
            ),
            Paragraph(
                "• <b>Natural England / NatureScot / NRW</b> — protected species surveys "
                "(great crested newt, white-clawed crayfish, water vole)",
                s["box_body"],
            ),
            Paragraph(
                "• <b>Planning consultants</b> — habitat assessments for development "
                "planning applications",
                s["box_body"],
            ),
            Paragraph(
                "• <b>Water companies</b> — reservoir and catchment biodiversity monitoring",
                s["box_body"],
            ),
        ],
        bg=AMBER_LIGHT, border=AMBER, s=s,
    ))

    # ── 2. CONFIDENCE FLAGS ───────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("2.  Reading Confidence Flags", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Every row in the species table carries a <b>confidence_flag</b>: "
        "<b>HIGH</b>, <b>MEDIUM</b>, or <b>LOW</b>. "
        "This is the single most important column for a regulator. "
        "Here is exactly how it is calculated and what it means:",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))

    conf_data = [
        [Paragraph("Flag",      s["th"]),
         Paragraph("Identity threshold",  s["th"]),
         Paragraph("What the pipeline reports", s["th"]),
         Paragraph("How to communicate it", s["th"])],
        [Paragraph("HIGH",      ParagraphStyle("hf", fontName="Helvetica-Bold",
                                fontSize=9.5, textColor=GREEN_DARK, leading=13)),
         Paragraph("≥ 97 %",    s["td_c"]),
         Paragraph("Species name (e.g. <i>Chlorella vulgaris</i>)", s["td"]),
         Paragraph(
             "State: '<i>C. vulgaris</i> detected with high confidence.' "
             "Safe to report at species level.",
             s["td"])],
        [Paragraph("MEDIUM",    ParagraphStyle("mf", fontName="Helvetica-Bold",
                                fontSize=9.5, textColor=AMBER, leading=13)),
         Paragraph("90 – 96 %", s["td_c"]),
         Paragraph("Genus only (e.g. <i>Daphnia</i> sp.)", s["td"]),
         Paragraph(
             "State: '<i>Daphnia</i> sp. detected at genus level — species "
             "uncertain.' Do <b>not</b> name a species.",
             s["td"])],
        [Paragraph("LOW",       ParagraphStyle("lf", fontName="Helvetica-Bold",
                                fontSize=9.5, textColor=RED_DARK, leading=13)),
         Paragraph("&lt; 90 %", s["td_c"]),
         Paragraph("Genus sp. or unclassified", s["td"]),
         Paragraph(
             "State: 'Sequence detected but confidence too low for "
             "reliable taxonomic assignment.' Flag for review.",
             s["td"])],
    ]
    conf_t = Table(conf_data, colWidths=[1.8*cm, 2.2*cm, 4.0*cm, 6.0*cm])
    conf_t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  TEAL_DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ("BOX",            (0, 0), (-1, -1), 0.8, GREY_MID),
        ("INNERGRID",      (0, 0), (-1, -1), 0.4, GREY_MID),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(conf_t)
    story.append(Spacer(1, 0.2 * cm))
    story.append(info_box(
        "LCA and the confidence_flag work together",
        [Paragraph(
            "The <b>confidence_flag</b> is set from the top-hit identity. "
            "But the <b>resolved_species</b> column — what the report actually shows — "
            "also applies LCA logic across all hits. "
            "So a sequence may have a HIGH flag (top hit ≥ 97 %) but still be "
            "reported as 'Genus sp.' if multiple hits with near-identical scores "
            "disagree on the species. "
            "Both columns are in blast_hit_table.csv for full transparency.",
            s["box_body"],
        )],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s,
    ))

    # ── 3. DIVERSITY INDICES ──────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("3.  Diversity Indices — Plain English", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "The pipeline calculates two biodiversity indices: "
        "<b>Shannon H'</b> and <b>Pielou J'</b>. "
        "These summarise the community into two numbers that ecologists and "
        "regulators recognise. Understanding them helps you explain your results "
        "in plain language.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))

    story.append(Paragraph("Shannon diversity index (H')", s["h2"]))
    story.append(Paragraph(
        "Shannon H' asks: <i>how much uncertainty is there about what species "
        "the next randomly-chosen sequence will belong to?</i> "
        "High uncertainty = many species, all roughly equally abundant = high diversity.",
        s["body"],
    ))
    story.append(Paragraph(
        "Formula: <b>H' = −Σ pᵢ · ln(pᵢ)</b> where pᵢ is the proportion of "
        "reads belonging to species i.",
        s["body"],
    ))
    story.append(two_col(
        [
            ("H' value",      "Typical interpretation"),
            ("0.0",           "Only one taxon present (H' = 0 when there is no uncertainty)"),
            ("0.5 – 1.5",     "Low diversity — one taxon strongly dominates"),
            ("1.5 – 2.5",     "Moderate diversity — several taxa, uneven"),
            ("2.5 – 3.5",     "High diversity — many taxa, relatively even"),
            ("&gt; 3.5",      "Very high — typical of pristine, species-rich habitats"),
        ],
        col_a_w=2.8 * cm, header_bg=TEAL_DARK, s=s,
    ))
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("Pielou evenness index (J')", s["h2"]))
    story.append(Paragraph(
        "Pielou J' answers: <i>are the taxa evenly distributed, or does one dominate?</i> "
        "It is always between 0 and 1. "
        "It is calculated as <b>J' = H' / ln(S)</b> where S is species richness. "
        "This normalises Shannon's index so you can compare communities "
        "with different numbers of species.",
        s["body"],
    ))
    story.append(two_col(
        [
            ("J' value",    "What it means"),
            ("1.0",         "Perfectly even — every taxon has exactly the same read count"),
            ("0.8 – 0.99",  "Highly even — no single taxon dominates"),
            ("0.5 – 0.79",  "Moderately uneven — one or two taxa more abundant"),
            ("&lt; 0.5",    "Strongly dominated — one taxon accounts for most reads"),
        ],
        col_a_w=2.8 * cm, header_bg=GREEN_DARK, s=s,
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(info_box(
        "Worked example — Cannock Chase Pond A (demo run)",
        [
            Paragraph(
                "Species richness S = 6 &nbsp;|&nbsp; "
                "Shannon H' = 1.748 &nbsp;|&nbsp; Pielou J' = 0.976",
                s["box_body"],
            ),
            Spacer(1, 0.05 * cm),
            Paragraph(
                "Interpretation: Six taxa identified. "
                "The community is <b>highly even</b> (J' = 0.976 — nearly perfect "
                "evenness) with <b>moderate overall diversity</b> (H' = 1.748). "
                "<i>Microcystis aeruginosa</i> appeared in two sequences (the cyanobacterial "
                "bloom) but because total richness is 6 and reads are spread across them, "
                "evenness remains high. "
                "One sequence (mixed diatom genera) returned 'unclassified' and is "
                "excluded from diversity calculations — this is transparently reported "
                "as 'Unclassified: 1'.",
                s["box_body"],
            ),
        ],
        bg=GREEN_LIGHT, border=GREEN_DARK, s=s,
    ))

    # ── 4. GENERATING THE REPORT ──────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4.  Generating Your Report", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Add <b>--report</b> to any pipeline run and a PDF is written alongside "
        "the CSV files. Three extra flags fill in the cover page:",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "python pipeline.py --fasta data/sample_sequences.fasta "
        "--local --db-path /data/blast/nt --threads 4 "
        "--report "
        "--site \"Cannock Chase Pond A\" "
        "--sample-date 2026-05-22 "
        "--analyst \"Yaw Baah\"",
        s["code"],
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(two_col(
        [
            ("Flag",              "Effect"),
            ("--report",          "Triggers PDF generation (off by default)"),
            ("--site NAME",       "Site name printed on the cover page and methodology section"),
            ("--sample-date DATE","Collection date (YYYY-MM-DD). Defaults to today if omitted"),
            ("--analyst NAME",    "Analyst name on cover and methodology"),
        ],
        col_a_w=4.0 * cm, header_bg=TEAL_DARK, s=s,
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "The PDF is saved as <b>data/results/eDNA_Report.pdf</b> (or whatever "
        "--output directory you set). "
        "If --local was used, the database version from db_version.json is "
        "automatically embedded in the Methodology section.",
        s["body"],
    ))

    # ── 5. THE FOUR REPORT SECTIONS ───────────────────────────────────────────
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("5.  The Four Sections of the PDF Report", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))

    sections = [
        ("Cover page",
         "Site name, sample date, analyst, report date. "
         "Plain-English description of the method. Designed to orient a "
         "non-technical regulator before they reach the numbers."),
        ("1. Executive Summary",
         "Five metric tiles (species richness, H', J', sequences analysed, "
         "unclassified). Auto-generated plain-English interpretation. "
         "Confidence level guide table showing what HIGH / MEDIUM / LOW mean."),
        ("2. Species Identification Table",
         "One row per sequence (top hit only). Columns: resolved species, "
         "confidence flag (colour-coded pill), identity %, e-value, accession. "
         "LOW confidence rows are shaded red to draw the eye immediately."),
        ("3. Biodiversity Metrics",
         "Alpha-diversity table (S, H', J') with formulas and interpretation. "
         "Taxon count table with inline bar chart showing relative abundance. "
         "Unclassified sequences are counted but excluded from diversity."),
        ("4. Methodology",
         "Pipeline description, LCA logic, identity thresholds. "
         "Database version box (from db_version.json). "
         "Sample metadata table (site, date, analyst, report date). "
         "Reproducibility statement."),
    ]
    for title, desc in sections:
        data = [[
            Paragraph(title, ParagraphStyle("sth", fontName="Helvetica-Bold",
                      fontSize=10, textColor=WHITE, leading=14)),
            Paragraph(desc,  s["box_body"]),
        ]]
        t = Table(data, colWidths=[3.5 * cm, 10.5 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0), TEAL_MID),
            ("BACKGROUND",    (1, 0), (1, 0), GREY_LIGHT),
            ("BOX",           (0, 0), (-1, -1), 0.8, GREY_MID),
            ("LEFTPADDING",   (0, 0), (-1, -1), 9),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 9),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.1 * cm))

    # ── 6. COMMON MISTAKES ────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("6.  Common Interpretation Mistakes", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))

    mistakes = [
        ("Reporting a MEDIUM hit at species level",
         "A 93 % identity hit to <i>Daphnia pulex</i> does NOT mean "
         "<i>D. pulex</i> was present. The pipeline correctly reports "
         "'<i>Daphnia</i> sp.' — stick to that in your write-up.",
         RED_DARK, RED_LIGHT),
        ("Treating 'unclassified' as a missing data problem",
         "Unclassified sequences are not errors — they are real sequences "
         "the database cannot confidently place. They may represent novel taxa, "
         "database gaps, or degraded DNA. Always report the unclassified count.",
         AMBER, AMBER_LIGHT),
        ("Comparing H' across datasets with different --max-hits",
         "Shannon H' in this pipeline is based on top-hit read counts. "
         "If one run used --max-hits 5 and another used --top-hit-only, "
         "the diversity numbers are not directly comparable.",
         TEAL_MID, BLUE_LIGHT),
        ("Ignoring LOW confidence rows",
         "LOW confidence hits are shown in red in the report. "
         "Do not silently include them in a species list — flag them explicitly. "
         "They may indicate PCR noise, chimeric sequences, or genuine rarities.",
         RED_DARK, RED_LIGHT),
        ("Not recording the database version",
         "If you use web BLAST and re-run six months later, you may get "
         "different species names — NCBI updates daily. "
         "Always use --local with a version-stamped database for any "
         "analysis that will be submitted to a regulator.",
         PURPLE_DARK, PURPLE_LIGHT),
    ]

    for title, desc, border, bg in mistakes:
        story.append(info_box(
            f"Mistake: {title}",
            [Paragraph(desc, s["box_body"])],
            bg=bg, border=border, s=s,
        ))
        story.append(Spacer(1, 0.12 * cm))

    # ── 7. GLOSSARY ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("7.  Glossary", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))

    glossary = [
        ("confidence_flag",
         "Column in blast_hit_table.csv. 'high' (≥97 %), 'medium' (90–96 %), "
         "or 'low' (&lt;90 %) based on the identity_pct of the top BLAST hit."),
        ("resolved_species",
         "The post-LCA species assignment used for reporting and diversity calculations. "
         "May differ from the raw 'species' column if LCA logic downgraded the rank."),
        ("species_richness (S)",
         "Count of distinct classified taxa in the top-hit table. "
         "Unclassified sequences are excluded."),
        ("Shannon index (H')",
         "H' = -Σ pᵢ ln(pᵢ). A measure of both the number of species and "
         "their relative abundances. Higher = more diverse. "
         "Maximum value = ln(S) (when all species are equally abundant)."),
        ("Pielou evenness (J')",
         "J' = H' / ln(S). Normalised evenness between 0 and 1. "
         "1.0 = all taxa equally abundant. "
         "0.0 = one taxon accounts for all reads (impossible in practice)."),
        ("unclassified_queries",
         "Sequences where resolved_species = 'unclassified'. "
         "Counted separately in the report — not included in richness or H'."),
        ("LCA (Lowest Common Ancestor)",
         "A strategy for resolving disagreeing BLAST hits. "
         "If hits to a query all belong to the same genus but different species, "
         "the assignment is downgraded to 'Genus sp.' "
         "This avoids falsely naming a species when the evidence is ambiguous."),
        ("blast_hit_table.csv",
         "The primary output file. One row per BLAST hit per query. "
         "Contains: query_id, species, resolved_species, confidence_flag, "
         "identity_pct, evalue, bit_score, query_coverage_pct, accession."),
        ("biodiversity_summary.csv",
         "Secondary output. One metric per row — S, H', J', total_queries, "
         "unclassified_queries, plus one row per taxon with read count."),
        ("db_version.json",
         "Written on every local BLAST run. Records the database path, "
         "version string, program, and UTC timestamp. "
         "Embedded in the PDF Methodology section automatically."),
    ]

    for term, defn in glossary:
        story.append(Paragraph(term, s["gl_term"]))
        story.append(Paragraph(defn, s["gl_def"]))

    story.append(info_box(
        "Key Takeaways",
        [Paragraph(
            "• A results CSV is not a regulatory report — use <b>--report</b> to "
            "generate a traceable, client-ready PDF.<br/>"
            "• <b>Confidence flags are not optional context</b> — they are the "
            "primary quality signal. Never report a MEDIUM or LOW hit at species level.<br/>"
            "• <b>Shannon H'</b> measures diversity; <b>Pielou J'</b> measures evenness. "
            "Report both — they tell different stories.<br/>"
            "• <b>Unclassified sequences</b> must be reported, not hidden. "
            "They are part of the evidence base.<br/>"
            "• <b>Database version</b> must be recorded for regulatory submissions. "
            "The pipeline does this automatically via db_version.json.",
            s["box_body"],
        )],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s,
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Next: Module 04 — Protected Species Detection &amp; UK Regulatory Frameworks",
        s["caption"],
    ))

    return story


def main():
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm,
        topMargin=2.2 * cm,  bottomMargin=2.2 * cm,
    )
    doc.build(build(make_styles()))
    print(f"PDF saved: {OUTPUT.resolve()}")


if __name__ == "__main__":
    main()
