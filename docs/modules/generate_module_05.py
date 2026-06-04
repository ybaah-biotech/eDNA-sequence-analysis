#!/usr/bin/env python3
"""
Generate Module 05 — Curated Databases & Multi-marker Surveys
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

OUTPUT = Path(__file__).parent / "Module_05_Curated_Databases_and_Multi_Marker_Surveys.pdf"

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
        Paragraph("MODULE 05", s["module_label"]), TEAL_DARK, pad_top=28, pad_bot=6
    ))
    story.append(coloured_banner(
        Paragraph("Curated Databases &amp; Multi-marker Surveys", s["title_main"]),
        TEAL_MID, pad_top=14, pad_bot=14,
    ))
    story.append(coloured_banner(
        Paragraph("eDNA Bioinformatics Learning Series  ·  Yaw Baah", s["title_sub"]),
        GREEN_DARK, pad_top=7, pad_bot=7,
    ))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(
        "NCBI's nucleotide database contains hundreds of billions of base pairs "
        "and is growing daily — but size is not the same as quality. "
        "This module explains why specialist curated databases outperform NCBI nt "
        "for most eDNA surveys, which database to choose for which marker, "
        "and how running multiple markers in a single survey gives a far more "
        "complete picture of what lives in a water body.",
        s["body"],
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(info_box(
        "What you will learn",
        [Paragraph(
            "1. Why curated databases beat raw NCBI nt for specific surveys  &nbsp; "
            "2. The six key databases and their target organisms  &nbsp; "
            "3. Gene markers — COI, 12S, 16S, 18S, ITS — and what each detects  &nbsp; "
            "4. How to match the right marker to the right database  &nbsp; "
            "5. Why a single marker gives an incomplete community picture  &nbsp; "
            "6. How the pipeline will handle multi-marker runs  &nbsp; "
            "7. Practical storage and download considerations  &nbsp; "
            "8. Glossary",
            s["box_body"],
        )],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s,
    ))

    # ── 1. WHY CURATED DATABASES ──────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("1.  Why Curated Databases Beat NCBI nt", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "NCBI's nucleotide database (nt) contains sequences from every organism "
        "ever submitted — complete genomes, partial genes, environmental metagenomes, "
        "and millions of individual reads. It is the most comprehensive sequence "
        "repository on Earth. It is also, from the perspective of a specific eDNA "
        "survey, full of noise.",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "The problems with running a 16S bacterial eDNA sample against NCBI nt:",
        s["body"],
    ))
    for b in [
        "<b>Speed</b> — nt is ~300 GB. A BLAST search takes much longer when it must "
        "scan vertebrate genomes, plant chloroplasts, and human sequences that will "
        "never match your bacterial 16S amplicon.",
        "<b>Annotation quality</b> — sequences submitted by automated pipelines "
        "often carry species names copied from other records, or names like "
        "'uncultured bacterium clone X' with no real taxonomic value.",
        "<b>Outdated taxonomy</b> — NCBI nt accumulates records from the 1980s onward. "
        "Many species names are pre-reclassification synonyms. "
        "A curated database is regularly cleaned to reflect current taxonomy.",
        "<b>False positives</b> — a 16S primer hitting a partial rRNA sequence "
        "embedded in a vertebrate genome is a false match. "
        "A 16S-only database eliminates this class of error entirely.",
    ]:
        story.append(Paragraph(f"• {b}", s["bullet"]))
    story.append(Spacer(1, 0.15 * cm))
    story.append(info_box(
        "The practical difference",
        [Paragraph(
            "For a freshwater macroinvertebrate survey using COI primers, "
            "BLASTing against BOLD (the Barcode of Life Database, COI-only, ~3 GB) "
            "is faster, more accurate, and produces cleaner taxonomy than BLASTing "
            "against all 300 GB of nt. "
            "The curated database wins on every metric for marker-specific work.",
            s["box_body"],
        )],
        bg=GREEN_LIGHT, border=GREEN_DARK, s=s,
    ))

    # ── 2. THE SIX KEY DATABASES ──────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("2.  The Six Key Curated Databases", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Each database is maintained by a specialist community and covers "
        "a specific marker and taxonomic group. Knowing which one to reach for "
        "is a core bioinformatics skill.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))

    db_header = [
        Paragraph("Database", s["th"]),
        Paragraph("Marker", s["th"]),
        Paragraph("Target organisms", s["th"]),
        Paragraph("Approx. size", s["th"]),
    ]
    db_rows = [
        ("SILVA SSU",        "16S / 18S rRNA",  "Bacteria, archaea, eukaryotes",           "~10 GB"),
        ("SILVA LSU",        "23S / 28S rRNA",  "Bacteria, archaea, eukaryotes",           "~5 GB"),
        ("BOLD",             "COI",             "Animals — invertebrates, fish, birds, mammals", "~3 GB"),
        ("ITS_RefSeq_Fungi", "ITS1 / ITS2",     "Fungi",                                   "~1 GB"),
        ("MIDORI2",          "12S, COI, others","Vertebrates — fish, amphibians, mammals",  "~2 GB"),
        ("PR2",              "18S",             "Protists, algae, phytoplankton",           "~500 MB"),
    ]
    db_data = [db_header]
    for i, (db, marker, target, size) in enumerate(db_rows):
        bg = WHITE if i % 2 == 0 else GREY_LIGHT
        db_data.append([
            Paragraph(f"<b>{db}</b>", s["td"]),
            Paragraph(marker, s["td_c"]),
            Paragraph(target, s["td"]),
            Paragraph(size, s["td_c"]),
        ])
    db_table = Table(db_data, colWidths=[3.0*cm, 2.8*cm, 5.4*cm, 2.8*cm])
    db_table.setStyle(TableStyle([
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
    story.append(db_table)
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("SILVA — the workhorse for environmental surveys", s["h2"]))
    story.append(Paragraph(
        "SILVA is the most widely used database in environmental eDNA work. "
        "It is maintained by the Max Planck Institute for Marine Microbiology "
        "and released in numbered versions (SILVA 132, 138, 138.1, 138.2). "
        "It covers small-subunit (SSU, used for 16S/18S) and "
        "large-subunit (LSU, used for 23S/28S) ribosomal RNA. "
        "For a freshwater bacterial community survey, SILVA SSU is the standard choice.",
        s["body"],
    ))
    story.append(Paragraph("BOLD — the animal barcode library", s["h2"]))
    story.append(Paragraph(
        "The Barcode of Life Database holds COI sequences for over 200,000 animal species. "
        "COI (cytochrome c oxidase subunit I) is the universal animal barcode — "
        "a short, standardised gene region that varies enough between species "
        "to distinguish them, but is conserved enough to amplify with universal primers. "
        "For macroinvertebrate surveys, BOLD is the primary reference.",
        s["body"],
    ))
    story.append(Paragraph("MIDORI2 — vertebrates for eDNA surveys", s["h2"]))
    story.append(Paragraph(
        "MIDORI2 is a curated database of vertebrate mitochondrial genes "
        "including 12S rRNA, 16S rRNA, and COI. "
        "It is the recommended database for freshwater fish surveys and "
        "for the great crested newt pipeline, "
        "since 12S rRNA is the standard vertebrate eDNA marker "
        "(MiFish primers target 12S for fish; general vertebrate primers for amphibians).",
        s["body"],
    ))

    # ── 3. GENE MARKERS ───────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("3.  Gene Markers — Which Gene Does What", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "A gene marker is the specific region of DNA you amplify during PCR. "
        "Your primers define which marker you amplify. "
        "The marker determines which database you search. "
        "Getting this chain right — primer → marker → database — "
        "is one of the most consequential decisions in an eDNA survey design.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))

    marker_header = [
        Paragraph("Marker", s["th"]),
        Paragraph("Gene", s["th"]),
        Paragraph("What it detects", s["th"]),
        Paragraph("Database", s["th"]),
    ]
    marker_rows = [
        ("16S rRNA",  "Ribosomal RNA, small subunit",  "Bacteria and archaea",                    "SILVA SSU, RDP"),
        ("18S rRNA",  "Ribosomal RNA, small subunit",  "Eukaryotes — algae, protists, fungi",      "SILVA SSU, PR2"),
        ("ITS1/ITS2", "Internal transcribed spacer",   "Fungi (highly variable — good for ID)",   "ITS_RefSeq_Fungi"),
        ("COI",       "Cytochrome oxidase subunit I",  "Animals — invertebrates, fish, birds",     "BOLD, MIDORI2"),
        ("12S rRNA",  "Ribosomal RNA, small subunit",  "Vertebrates — fish, amphibians, mammals",  "MIDORI2, SILVA"),
    ]
    marker_data = [marker_header]
    for marker, gene, detects, db in marker_rows:
        marker_data.append([
            Paragraph(f"<b>{marker}</b>", s["td"]),
            Paragraph(gene, s["td"]),
            Paragraph(detects, s["td"]),
            Paragraph(db, s["td"]),
        ])
    marker_table = Table(marker_data, colWidths=[2.0*cm, 3.5*cm, 4.5*cm, 4.0*cm])
    marker_table.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  GREEN_DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ("BOX",            (0, 0), (-1, -1), 0.8, GREY_MID),
        ("INNERGRID",      (0, 0), (-1, -1), 0.4, GREY_MID),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(marker_table)
    story.append(Spacer(1, 0.2 * cm))
    story.append(info_box(
        "Critical rule: primer must match database",
        [Paragraph(
            "If you amplify with 16S primers but BLAST against BOLD (a COI database), "
            "you will get either no hits or meaningless hits. "
            "The primer defines what you amplified. The database must contain "
            "sequences of the same gene region. "
            "Mismatching these is one of the most common errors in bioinformatics "
            "pipelines built without domain knowledge.",
            s["box_body"],
        )],
        bg=RED_LIGHT, border=RED_DARK, s=s,
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph("The GCN pipeline specifically", s["h2"]))
    story.append(Paragraph(
        "Great crested newt eDNA surveys typically use primers targeting "
        "<b>12S rRNA</b> (vertebrate mitochondrial gene) or species-specific "
        "primers validated for <i>Triturus cristatus</i>. "
        "The reference database is MIDORI2 (for vertebrate 12S) or "
        "a bespoke validated reference set approved by Natural England. "
        "Using NCBI nt for GCN identification is technically possible "
        "but not recommended for regulatory submission — "
        "a versioned, species-validated reference is required for legal defensibility.",
        s["body"],
    ))

    # ── 4. MULTI-MARKER SURVEYS ───────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4.  Multi-marker Surveys — Why One Gene Is Not Enough", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Every gene marker has a taxonomic blind spot. "
        "16S tells you about bacteria but is blind to animals. "
        "COI tells you about animals but misses bacteria entirely. "
        "A single-marker survey always gives a partial picture of biodiversity.",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "A multi-marker survey runs several primer pairs on the same water sample. "
        "The sequencing library is <b>multiplexed</b> — "
        "multiple primer products are pooled and sequenced together, "
        "then separated by the primer sequences themselves during demultiplexing. "
        "The result is a much more complete view of the biological community:",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))

    survey_header = [
        Paragraph("Survey type", s["th"]),
        Paragraph("Markers run", s["th"]),
        Paragraph("Community picture", s["th"]),
    ]
    survey_rows = [
        ("Bacterial water quality",   "16S only",              "Bacteria and archaea only"),
        ("Freshwater fish survey",    "12S (MiFish)",           "Fish only"),
        ("Macroinvertebrate survey",  "COI",                   "Animals only"),
        ("Comprehensive biodiversity","16S + 18S + COI + ITS",  "Bacteria + eukaryotes + animals + fungi"),
        ("Regulatory GCN survey",     "12S + species-specific", "Vertebrates + GCN confirmation"),
    ]
    survey_data = [survey_header]
    for i, (stype, markers, picture) in enumerate(survey_rows):
        survey_data.append([
            Paragraph(stype, s["td"]),
            Paragraph(f"<b>{markers}</b>", s["td"]),
            Paragraph(picture, s["td"]),
        ])
    survey_table = Table(survey_data, colWidths=[4.0*cm, 4.0*cm, 6.0*cm])
    survey_table.setStyle(TableStyle([
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
    story.append(survey_table)
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Chimeric sequences — the multi-marker hazard", s["h2"]))
    story.append(Paragraph(
        "Chimeric sequences are PCR artefacts — sequences that are part "
        "organism A and part organism B, created when a partial amplicon from "
        "one template acts as a primer for a different template in the same reaction. "
        "They are more common when multiple primer pairs are in the same reaction. "
        "Chimera checking (e.g. UCHIME algorithm) is a standard pre-processing step "
        "in multi-marker pipelines. "
        "The pipeline will include chimera filtering in Phase 5.",
        s["body"],
    ))

    # ── 5. HOW THE PIPELINE HANDLES MULTI-MARKER ──────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("5.  How Phase 5 Will Handle Multiple Markers", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Phase 5 of the pipeline (planned) extends the current single-marker "
        "architecture to handle COI, ITS, 16S, and 18S in a single run. "
        "Here is the design:",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))

    steps = [
        ("Input",
         "User provides a FASTA file with sequences tagged by marker "
         "(e.g. query ID prefix: '16S_', 'COI_', 'ITS_'). "
         "Or a separate FASTA per marker."),
        ("Routing",
         "The pipeline reads the marker tag and routes each sequence to the "
         "appropriate BLAST run — 16S sequences to SILVA, COI to BOLD, ITS to "
         "ITS_RefSeq_Fungi, 12S to MIDORI2."),
        ("Separate BLAST runs",
         "Each marker group gets its own blastn call against its own database. "
         "XML cache files are prefixed by marker to avoid collisions."),
        ("Merged hit table",
         "Results from all markers are merged into a single hit table. "
         "A new 'marker' column records which gene each hit came from. "
         "LCA logic runs per-marker — you don't mix COI and 16S taxonomy."),
        ("Per-marker diversity",
         "Diversity metrics (Shannon H', Pielou J') are calculated separately "
         "per marker and combined in the report. "
         "This lets you compare bacterial diversity vs. animal diversity independently."),
        ("PDF report",
         "The report gains a new section: marker summary table showing "
         "how many sequences came from each marker and the top taxa per marker."),
    ]
    for i, (step, desc) in enumerate(steps):
        data = [[
            Paragraph(f"{i+1}. {step}",
                      ParagraphStyle("sth", fontName="Helvetica-Bold",
                                     fontSize=10, textColor=WHITE, leading=14)),
            Paragraph(desc, s["box_body"]),
        ]]
        t = Table(data, colWidths=[3.0 * cm, 11.0 * cm])
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

    # ── 6. VERSIONING AND REPRODUCIBILITY ─────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("6.  Database Versioning and Reproducibility", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "SILVA publishes numbered releases. BOLD is updated continuously. "
        "MIDORI2 versions are tied to NCBI taxonomy releases. "
        "A species identified as <i>Gammarus fossarum</i> in SILVA 132 "
        "may be reclassified in SILVA 138 as a result of genomic revision. "
        "If you cannot state which database version produced your results, "
        "those results are not reproducible — and in a regulatory context, "
        "not defensible.",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "The pipeline's <b>db_version.json</b> file (written on every local run) "
        "records the database path, version string from blastdbcmd, and UTC timestamp. "
        "This is automatically embedded in the PDF Methodology section. "
        "For multi-marker runs, Phase 5 will record a version entry per database.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(two_col(
        [
            ("SILVA release", "Notable change"),
            ("SILVA 132",     "2018 — widely used baseline"),
            ("SILVA 138",     "2020 — major taxonomy revision, ~500,000 new sequences"),
            ("SILVA 138.1",   "2021 — incremental update, improved eukaryote coverage"),
            ("SILVA 138.2",   "2024 — current recommended version"),
        ],
        col_a_w=3.5 * cm, header_bg=TEAL_DARK, s=s,
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(info_box(
        "Practical rule",
        [Paragraph(
            "Always note the database name AND version in your methods. "
            "When you set up a new local database, run: "
            "<font name='Courier' size='9'>blastdbcmd -db /path/to/db -info</font> "
            "and record the output. The pipeline does this automatically via "
            "stamp_db_version() in src/local_blast.py.",
            s["box_body"],
        )],
        bg=AMBER_LIGHT, border=AMBER, s=s,
    ))

    # ── 7. STORAGE AND DOWNLOADS ──────────────────────────────────────────────
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("7.  Practical: Storage and Download Sizes", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Most eDNA consultancy work can be covered by three databases "
        "totalling under 20 GB. NCBI nt at ~300 GB requires dedicated storage "
        "and is rarely necessary when a curated database is available for your marker.",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(two_col(
        [
            ("Database", "Download size"),
            ("SILVA 138.2 SSU", "~10 GB"),
            ("BOLD",            "~3 GB"),
            ("MIDORI2 (12S)",   "~2 GB"),
            ("ITS_RefSeq_Fungi","~1 GB"),
            ("PR2",             "~500 MB"),
            ("NCBI nt",         "~300 GB (not recommended for targeted work)"),
        ],
        col_a_w=5.0 * cm, header_bg=GREEN_DARK, s=s,
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(
        "To download a database using the pipeline's setup script:",
        s["body"],
    ))
    story.append(Paragraph(
        "python scripts/setup_db.py --db 16S_ribosomal_RNA --dest /data/blast/",
        s["code"],
    ))
    story.append(Paragraph(
        "python scripts/setup_db.py --db ITS_RefSeq_Fungi --dest /data/blast/",
        s["code"],
    ))

    # ── 8. GLOSSARY ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("8.  Glossary", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))

    glossary = [
        ("Gene marker",
         "The specific gene region amplified by a PCR primer pair. "
         "The marker determines which database to search against. "
         "Examples: 16S rRNA, COI, ITS, 12S rRNA."),
        ("SILVA",
         "A curated ribosomal RNA database maintained by the Max Planck Institute. "
         "SSU covers 16S (bacteria/archaea) and 18S (eukaryotes). "
         "Released in numbered versions (132, 138, 138.1, 138.2)."),
        ("BOLD (Barcode of Life Database)",
         "Curated COI sequences for over 200,000 animal species. "
         "The primary reference for invertebrate and fish identification via COI."),
        ("MIDORI2",
         "Curated vertebrate mitochondrial gene database. "
         "Covers 12S, 16S, and COI. "
         "The recommended database for freshwater fish and amphibian eDNA surveys."),
        ("COI (cytochrome c oxidase subunit I)",
         "The universal animal barcode gene. "
         "Amplified with universal primers (e.g. LCO1490/HCO2198). "
         "Variable enough between species for identification, "
         "conserved enough to amplify across all animals."),
        ("ITS (internal transcribed spacer)",
         "A non-coding region of ribosomal DNA between 18S and 5.8S genes. "
         "ITS1 and ITS2 are the universal fungal barcodes. "
         "Highly variable — ideal for distinguishing closely related fungal species."),
        ("12S rRNA",
         "A small ribosomal RNA gene in the mitochondrial genome. "
         "Standard marker for vertebrate eDNA surveys. "
         "MiFish primers (12S) are widely validated for fish detection."),
        ("Multiplexing",
         "Running multiple primer pairs in the same sequencing reaction. "
         "Products are pooled and separated during demultiplexing "
         "by their primer sequences."),
        ("Chimeric sequence",
         "A PCR artefact combining sequence from two different templates. "
         "Created when a partial amplicon acts as a primer for a second template. "
         "Must be removed before BLAST analysis. Detected using UCHIME or similar tools."),
        ("db_version.json",
         "File written by the pipeline on every local BLAST run. "
         "Records database path, version string, program, and UTC timestamp. "
         "Provides the version traceability required for regulatory submissions."),
    ]
    for term, defn in glossary:
        story.append(Paragraph(term, s["gl_term"]))
        story.append(Paragraph(defn, s["gl_def"]))

    story.append(info_box(
        "Key Takeaways",
        [Paragraph(
            "• For marker-specific eDNA work, a <b>curated database</b> outperforms "
            "NCBI nt on speed, accuracy, and taxonomy quality.<br/>"
            "• The chain is: <b>primer defines marker → marker defines database</b>. "
            "Mismatching them produces meaningless results.<br/>"
            "• A single marker always gives a partial picture. "
            "<b>Multi-marker surveys</b> are needed for comprehensive biodiversity assessment.<br/>"
            "• Always record the database <b>name and version</b>. "
            "The pipeline does this automatically via db_version.json.<br/>"
            "• For most freshwater surveys: SILVA (bacteria) + MIDORI2 (vertebrates) "
            "+ BOLD (invertebrates) covers the major community components.",
            s["box_body"],
        )],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s,
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Next: Module 06 — Rarefaction, Beta Diversity &amp; Community Comparison",
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
