#!/usr/bin/env python3
"""
Generate Module 02 — Local BLAST+ & Reference Databases
eDNA Bioinformatics Learning Series
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)

OUTPUT = Path(__file__).parent / "Module_02_Local_BLAST_and_Databases.pdf"

# ── Colour palette ────────────────────────────────────────────────────────────
TEAL_DARK    = colors.HexColor("#1B4F72")
TEAL_MID     = colors.HexColor("#2E86C1")
GREEN_DARK   = colors.HexColor("#1E8449")
GREEN_LIGHT  = colors.HexColor("#EAFAF1")
BLUE_LIGHT   = colors.HexColor("#EBF5FB")
PURPLE_DARK  = colors.HexColor("#6C3483")
PURPLE_LIGHT = colors.HexColor("#F5EEF8")
ORANGE       = colors.HexColor("#D35400")
ORANGE_LIGHT = colors.HexColor("#FEF9E7")
RED_DARK     = colors.HexColor("#922B21")
GREY_LIGHT   = colors.HexColor("#F2F3F4")
GREY_MID     = colors.HexColor("#BDC3C7")
WHITE        = colors.white
BLACK        = colors.black


# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    s = {}

    def st(name, **kw):
        s[name] = ParagraphStyle(name, **kw)

    st("title_main",   fontName="Helvetica-Bold",    fontSize=26, textColor=WHITE,
       leading=32, alignment=TA_CENTER)
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
    st("body_b",       fontName="Helvetica-Bold",    fontSize=10, textColor=BLACK,
       leading=15, spaceAfter=4)
    st("bullet",       fontName="Helvetica",          fontSize=10, textColor=BLACK,
       leading=15, leftIndent=14, spaceAfter=3)
    st("box_head",     fontName="Helvetica-Bold",    fontSize=10, textColor=TEAL_DARK,
       leading=14, spaceAfter=3)
    st("box_body",     fontName="Helvetica",          fontSize=10, textColor=BLACK,
       leading=14, alignment=TA_JUSTIFY)
    st("code",         fontName="Courier",            fontSize=8.5,
       textColor=colors.HexColor("#1A5276"), leading=13, leftIndent=6, spaceAfter=3)
    st("code_comment", fontName="Courier-Oblique",   fontSize=8.5,
       textColor=colors.HexColor("#5D6D7E"), leading=13, leftIndent=6, spaceAfter=1)
    st("caption",      fontName="Helvetica-Oblique", fontSize=8.5,
       textColor=colors.HexColor("#707B7C"), leading=12, alignment=TA_CENTER)
    st("gl_term",      fontName="Helvetica-Bold",    fontSize=10, textColor=GREEN_DARK,
       leading=13, spaceAfter=1)
    st("gl_def",       fontName="Helvetica",          fontSize=10, textColor=BLACK,
       leading=13, leftIndent=10, spaceAfter=7)
    return s


# ── Helpers ───────────────────────────────────────────────────────────────────
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


def info_box(title, paras, bg, border=None, s=None):
    border = border or TEAL_MID
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


def two_col_table(rows, col_a_w=4.5 * cm, header_bg=TEAL_DARK, s=None):
    header_style = ParagraphStyle(
        "th", fontName="Helvetica-Bold", fontSize=9.5,
        textColor=WHITE, leading=13
    )
    cell_style = ParagraphStyle(
        "td", fontName="Helvetica", fontSize=9.5,
        textColor=BLACK, leading=13
    )
    table_data = []
    for i, (left, right) in enumerate(rows):
        lp = Paragraph(left,  header_style if i == 0 else cell_style)
        rp = Paragraph(right, header_style if i == 0 else cell_style)
        table_data.append([lp, rp])

    col_b_w = 14 * cm - col_a_w
    t = Table(table_data, colWidths=[col_a_w, col_b_w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  header_bg),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ("BOX",           (0, 0), (-1, -1), 0.8, GREY_MID),
        ("INNERGRID",     (0, 0), (-1, -1), 0.4, GREY_MID),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def step_row(num, title, colour, desc, s):
    t = Table(
        [[Paragraph(f"{num}. {title}", ParagraphStyle(
            "sr", fontName="Helvetica-Bold", fontSize=10,
            textColor=WHITE, leading=14)),
          Paragraph(desc, s["box_body"])]],
        colWidths=[3.6 * cm, 10.4 * cm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), colour),
        ("BACKGROUND",    (1, 0), (1, 0), GREY_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 0.8, GREY_MID),
        ("LEFTPADDING",   (0, 0), (-1, -1), 9),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 9),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def compare_row(feature, web, local, s):
    cell = ParagraphStyle("cmp", fontName="Helvetica", fontSize=9.5,
                          textColor=BLACK, leading=13)
    feat = ParagraphStyle("cmpF", fontName="Helvetica-Bold", fontSize=9.5,
                          textColor=TEAL_DARK, leading=13)
    return [Paragraph(feature, feat), Paragraph(web, cell), Paragraph(local, cell)]


# ── Document build ────────────────────────────────────────────────────────────
def build(s):
    story = []

    # ── TITLE PAGE ────────────────────────────────────────────────────────────
    story.append(coloured_banner(
        Paragraph("MODULE 02", s["module_label"]), TEAL_DARK, pad_top=28, pad_bot=6
    ))
    story.append(coloured_banner(
        Paragraph("Local BLAST+ &amp; Reference Databases", s["title_main"]),
        TEAL_MID, pad_top=14, pad_bot=14
    ))
    story.append(coloured_banner(
        Paragraph("eDNA Bioinformatics Learning Series  ·  Yaw Baah", s["title_sub"]),
        GREEN_DARK, pad_top=7, pad_bot=7
    ))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(
        "Module 01 explained <i>what</i> BLAST is and how it scores alignments. "
        "This module answers the next practical question: <b>how do you run BLAST "
        "on your own machine</b>, against a database you control, without rate limits, "
        "internet delays, or reproducibility surprises? "
        "By the end you will understand local databases, the BLAST+ toolchain, "
        "how the pipeline's <b>--local</b> flag works, and why database version "
        "stamping matters for scientific credibility.",
        s["body"],
    ))
    story.append(Spacer(1, 0.3 * cm))

    # Contents overview
    story.append(info_box(
        "What you will learn",
        [Paragraph(
            "1. Web vs Local BLAST — when to use each  &nbsp; "
            "2. How BLAST+ database files are structured  &nbsp; "
            "3. Which database to choose for eDNA  &nbsp; "
            "4. Setting up a database with scripts/setup_db.py  &nbsp; "
            "5. Running the pipeline in --local mode  &nbsp; "
            "6. Threading and performance  &nbsp; "
            "7. Database version stamping for reproducibility  &nbsp; "
            "8. Glossary",
            s["box_body"],
        )],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s,
    ))

    # ── 1. WEB vs LOCAL ───────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("1.  Web BLAST vs Local BLAST+ — Choose the Right Mode", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "The pipeline ships with two BLAST backends. "
        "Both produce identical XML output — the same parser reads both. "
        "The choice of backend affects <b>speed</b>, <b>reproducibility</b>, and "
        "<b>cost</b>, not the biology.",
        s["body"],
    ))
    story.append(Spacer(1, 0.2 * cm))

    # Comparison table
    cmp_header_style = ParagraphStyle(
        "cmpH", fontName="Helvetica-Bold", fontSize=9.5, textColor=WHITE, leading=13
    )
    cmp_cell = ParagraphStyle(
        "cmpC", fontName="Helvetica", fontSize=9.5, textColor=BLACK, leading=13
    )
    cmp_feat = ParagraphStyle(
        "cmpF", fontName="Helvetica-Bold", fontSize=9.5, textColor=TEAL_DARK, leading=13
    )

    def crow(feat, web_txt, local_txt):
        return [
            Paragraph(feat,      cmp_feat if feat != "Feature" else cmp_header_style),
            Paragraph(web_txt,   cmp_cell if feat != "Feature" else cmp_header_style),
            Paragraph(local_txt, cmp_cell if feat != "Feature" else cmp_header_style),
        ]

    cmp_data = [
        crow("Feature",          "Web BLAST (NCBI)",              "Local BLAST+"),
        crow("Speed",            "30 – 120 s per sequence (queue-dependent)",
             "Seconds on SSD; milliseconds for 16S"),
        crow("Rate limit",       "3 requests/sec max (blocked if exceeded)",
             "None — limited only by your CPU"),
        crow("Internet required","Yes",                           "No"),
        crow("Database version", "Updated daily — changes between runs",
             "Fixed to your local copy — fully reproducible"),
        crow("Database size",    "Always up to date, no local disk needed",
             "nt ~300 GB; 16S ~1 GB; SILVA SSU ~7 GB"),
        crow("Best for",         "Quick checks, small datasets, no BLAST+ installed",
             "Production runs, large datasets, offline environments"),
        crow("Pipeline flag",    "--email you@example.com",       "--local --db-path /data/blast/nt"),
    ]
    cmp_t = Table(cmp_data, colWidths=[4.2 * cm, 4.9 * cm, 4.9 * cm])
    cmp_t.setStyle(TableStyle([
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
    story.append(cmp_t)
    story.append(Spacer(1, 0.25 * cm))
    story.append(info_box(
        "Rule of thumb",
        [Paragraph(
            "Use <b>web BLAST</b> when you are testing a handful of sequences "
            "and do not need to reproduce the exact same database version. "
            "Switch to <b>local BLAST+</b> for any run that will go into a "
            "report, paper, or client deliverable — the version-locked database "
            "guarantees the same result if you re-run six months later.",
            s["box_body"],
        )],
        bg=ORANGE_LIGHT, border=ORANGE, s=s,
    ))

    # ── 2. HOW BLAST+ DATABASE FILES WORK ─────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("2.  How BLAST+ Database Files Are Structured", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "A BLAST database is not a single file — it is a family of binary files "
        "that together form an indexed, searchable copy of millions of sequences. "
        "Understanding the structure helps you diagnose errors "
        "(wrong path, corrupted download, wrong database type).",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph("Nucleotide database files (blastn uses these):", s["h2"]))
    story.append(two_col_table(
        [
            ("Extension",           "What it contains"),
            (".nsq",                "Sequence data — the raw nucleotide letters, compressed"),
            (".nin",                "Index — maps sequence IDs to positions in .nsq"),
            (".nhr",                "Header — human-readable titles for each sequence (BLAST hit titles)"),
            (".nsi / .nsd",         "String index — for text searches by accession or title"),
            (".nal",                "Alias file — for multi-volume databases (nt is split across volumes)"),
            (".njs  (BLAST5)",      "JSON metadata — database title, date, BLAST version used to build"),
        ],
        col_a_w=3.8 * cm, header_bg=TEAL_DARK, s=s,
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "When you pass <b>--db-path /data/blast/nt</b> to the pipeline, BLAST+ "
        "automatically finds all the volume files (nt.00.nsq, nt.01.nsq …) via the "
        "<b>nt.nal</b> alias file. You never need to specify individual volumes.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))

    story.append(info_box(
        "Checking a database with blastdbcmd",
        [Paragraph("blastdbcmd is a diagnostic tool bundled with BLAST+.", s["box_body"]),
         Spacer(1, 0.1 * cm),
         Paragraph("blastdbcmd -db /data/blast/nt -info", s["code"]),
         Paragraph(
             "This prints the database title, creation date, number of sequences, "
             "and total base count. "
             "The pipeline calls this automatically and saves the result to "
             "<b>data/results/db_version.json</b> every time you run with --local.",
             s["box_body"],
         )],
        bg=GREEN_LIGHT, border=GREEN_DARK, s=s,
    ))

    # ── 3. WHICH DATABASE TO CHOOSE ───────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("3.  Choosing the Right Reference Database", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "The database you choose has a bigger impact on your results than any "
        "parameter. A sequence that perfectly matches an organism in SILVA but has "
        "no representative in nt will return <i>unclassified</i> if you use nt. "
        "Below are the four databases most relevant to freshwater / environmental eDNA.",
        s["body"],
    ))
    story.append(Spacer(1, 0.2 * cm))

    db_data = [
        [
            Paragraph("Database", ParagraphStyle("dh", fontName="Helvetica-Bold",
                       fontSize=9.5, textColor=WHITE, leading=13)),
            Paragraph("Best for", ParagraphStyle("dh2", fontName="Helvetica-Bold",
                       fontSize=9.5, textColor=WHITE, leading=13)),
            Paragraph("Size", ParagraphStyle("dh3", fontName="Helvetica-Bold",
                       fontSize=9.5, textColor=WHITE, leading=13)),
            Paragraph("Notes", ParagraphStyle("dh4", fontName="Helvetica-Bold",
                       fontSize=9.5, textColor=WHITE, leading=13)),
        ],
    ]
    db_rows = [
        ("NCBI nt",               "General purpose — any organism",
         "~300 GB", "Broadest coverage; includes all GenBank sequences; very large"),
        ("16S_ribosomal_RNA",     "Bacteria and Archaea (16S marker)",
         "~1 GB",   "Curated NCBI set; much faster than nt; install in minutes"),
        ("ITS_RefSeq_Fungi",      "Fungi (ITS1/ITS2 marker)",
         "~300 MB",  "Used for mycology eDNA; small and fast"),
        ("SILVA 138 SSU",         "Eukaryotes, bacteria, archaea (18S/16S)",
         "~7 GB",   "Gold standard for rRNA; must be downloaded from arb-silva.de"),
    ]
    for db, best, size, notes in db_rows:
        cell = ParagraphStyle("dbc", fontName="Helvetica", fontSize=9.5,
                              textColor=BLACK, leading=13)
        db_data.append([
            Paragraph(f"<b>{db}</b>", cell),
            Paragraph(best,  cell),
            Paragraph(size,  cell),
            Paragraph(notes, cell),
        ])
    db_t = Table(db_data, colWidths=[3.5 * cm, 3.5 * cm, 1.8 * cm, 5.2 * cm])
    db_t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  PURPLE_DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PURPLE_LIGHT]),
        ("BOX",            (0, 0), (-1, -1), 0.8, GREY_MID),
        ("INNERGRID",      (0, 0), (-1, -1), 0.4, GREY_MID),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(db_t)
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("Decision guide for UK pond eDNA:", s["h2"]))
    for bullet in [
        "<b>Phytoplankton / microalgae (18S marker)</b> → SILVA 138 SSU or NCBI nt",
        "<b>Bacteria / cyanobacteria (16S marker)</b> → 16S_ribosomal_RNA (fastest) or SILVA 138",
        "<b>Fungi (ITS marker)</b> → ITS_RefSeq_Fungi",
        "<b>Macroinvertebrates / fish / plants (COI or rbcL)</b> → NCBI nt (only comprehensive option)",
        "<b>Unknown / mixed marker</b> → NCBI nt (safest fallback)",
    ]:
        story.append(Paragraph(f"• {bullet}", s["bullet"]))

    # ── 4. SETTING UP A DATABASE ──────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4.  Setting Up a Local Database — scripts/setup_db.py", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "The pipeline includes <b>scripts/setup_db.py</b> — a one-command wrapper "
        "around BLAST+'s built-in <i>update_blastdb.pl</i> utility. "
        "You do not need to manually navigate NCBI's FTP servers.",
        s["body"],
    ))
    story.append(Spacer(1, 0.2 * cm))

    for step in [
        (1, "Install BLAST+", TEAL_MID,
         "Ubuntu/Debian: <b>sudo apt-get install ncbi-blast+</b> &nbsp;|&nbsp; "
         "macOS: <b>brew install blast</b> &nbsp;|&nbsp; "
         "Codespaces: already installed in the devcontainer.  "
         "Verify with: blastn -version"),
        (2, "Download a database", GREEN_DARK,
         "Run: <b>python scripts/setup_db.py --db 16S_ribosomal_RNA --dest /data/blast/</b> "
         "for a quick (~1 GB) start. "
         "For the full nt database (300 GB): "
         "<b>python scripts/setup_db.py --db nt --dest /data/blast/</b> "
         "(allow 1–6 hours on a fast connection)."),
        (3, "Check what is installed", PURPLE_DARK,
         "Run: <b>python scripts/setup_db.py --list --dest /data/blast/</b> "
         "to see all databases already present and their titles."),
        (4, "Run the pipeline", ORANGE,
         "Run: <b>python pipeline.py --fasta data/sample_sequences.fasta "
         "--local --db-path /data/blast/16S_ribosomal_RNA --threads 4</b>  "
         "No --email needed in local mode."),
    ]:
        story.append(step_row(*step, s=s))
        story.append(Spacer(1, 0.12 * cm))

    story.append(Spacer(1, 0.15 * cm))
    story.append(info_box(
        "SILVA 138 — manual download",
        [Paragraph(
            "SILVA is not available via update_blastdb.pl. "
            "Download the FASTA from <b>arb-silva.de/download/arb-files/</b> "
            "(file: SILVA_138_SSURef_NR99_tax_silva.fasta.gz), then format it "
            "with:",
            s["box_body"],
        ),
         Spacer(1, 0.05 * cm),
         Paragraph(
             "makeblastdb -in SILVA_138_SSURef_NR99_tax_silva.fasta "
             "-dbtype nucl -title SILVA_138 -out /data/silva/SILVA_138_SSU",
             s["code"],
         ),
         Paragraph(
             "Then use: <b>--db-path /data/silva/SILVA_138_SSU</b>",
             s["box_body"],
         )],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s,
    ))

    # ── 5. THE --local FLAG EXPLAINED ─────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("5.  How the Pipeline's --local Mode Works", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "When you pass <b>--local</b>, pipeline.py calls <b>src/local_blast.py</b> "
        "instead of src/blast_query.py. "
        "Everything downstream — XML parsing, species extraction, LCA resolution, "
        "diversity metrics — is identical. The switch is invisible to the biology.",
        s["body"],
    ))
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("What src/local_blast.py does:", s["h2"]))
    story.append(two_col_table(
        [
            ("Step",                      "Detail"),
            ("Binary check",              "Locates the blastn binary using shutil.which(). "
                                          "Prints clear installation instructions if not found."),
            ("DB version stamp",          "Calls blastdbcmd -info and writes db_version.json "
                                          "to your results folder. Recorded once before any queries."),
            ("Cache check",               "Skips a query if its .xml file already exists and is "
                                          "non-empty — identical to web mode."),
            ("BLAST via subprocess",      "Passes the FASTA sequence on stdin (no temp files). "
                                          "Writes XML directly to the results/xml/ folder."),
            ("Timeout guard",             "Kills a stalled BLAST process after 300 seconds "
                                          "with a clear error message."),
            ("Threading",                 "Runs N workers in parallel using ThreadPoolExecutor "
                                          "when --threads N > 1. Each query writes its own file — "
                                          "no race conditions."),
        ],
        col_a_w=3.8 * cm, header_bg=TEAL_DARK, s=s,
    ))
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("Caching explained:", s["h2"]))
    story.append(Paragraph(
        "Caching is critical for large datasets. If your run is interrupted at "
        "sequence 847 of 1000, re-running the pipeline picks up at 848 — the "
        "847 completed XML files are reused instantly. "
        "This is the same behaviour as the web BLAST backend — the pipeline never "
        "wastes a query it has already computed.",
        s["body"],
    ))

    story.append(Spacer(1, 0.15 * cm))
    story.append(info_box(
        "Command reference",
        [
            Paragraph("# Minimal local run:", s["code_comment"]),
            Paragraph(
                "python pipeline.py --fasta data/sample_sequences.fasta "
                "--local --db-path /data/blast/16S_ribosomal_RNA",
                s["code"],
            ),
            Spacer(1, 0.08 * cm),
            Paragraph("# With threading and strict e-value:", s["code_comment"]),
            Paragraph(
                "python pipeline.py --fasta data/sample_sequences.fasta "
                "--local --db-path /data/blast/nt "
                "--threads 8 --evalue 1e-20 --max-hits 10",
                s["code"],
            ),
            Spacer(1, 0.08 * cm),
            Paragraph("# Keep only best hit per sequence:", s["code_comment"]),
            Paragraph(
                "python pipeline.py --fasta data/sample_sequences.fasta "
                "--local --db-path /data/blast/nt "
                "--threads 4 --top-hit-only",
                s["code"],
            ),
        ],
        bg=GREEN_LIGHT, border=GREEN_DARK, s=s,
    ))

    # ── 6. THREADING AND PERFORMANCE ──────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("6.  Threading and Performance", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Local BLAST+ supports parallel execution — you can run multiple sequences "
        "simultaneously across CPU cores. "
        "The pipeline exposes this via the <b>--threads N</b> flag.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph("Choosing the right thread count:", s["h2"]))
    story.append(two_col_table(
        [
            ("Storage type",  "Recommended --threads"),
            ("Spinning HDD",  "1  (sequential only — parallel seeks thrash the drive)"),
            ("SATA SSD",      "2 – 4  (I/O is fast enough; don't exceed CPU core count)"),
            ("NVMe SSD",      "4 – 8  (high bandwidth; safe to use all cores)"),
            ("GitHub Codespaces / devcontainer",
             "4 – 8  (NVMe-backed; BLAST+ pre-installed)"),
        ],
        col_a_w=4.8 * cm, header_bg=TEAL_DARK, s=s,
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Each thread runs a completely independent BLAST process — one per query "
        "sequence. They write to separate XML files so there are no shared-state "
        "issues. If any worker fails (e.g. timeout), the pipeline reports all "
        "failures together rather than silently dropping sequences.",
        s["body"],
    ))

    # ── 7. DB VERSION STAMPING ────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("7.  Database Version Stamping — Why It Matters", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "NCBI updates the nt database <b>daily</b>. "
        "A sequence that returns <i>Chlorella vulgaris</i> today might return "
        "<i>Chlorella sorokiniana</i> in three months if NCBI's curators reclassify "
        "a reference entry. "
        "For regulatory eDNA surveys (e.g. protected species detection), "
        "this non-reproducibility is a serious problem.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(
        "The solution is simple: <b>lock the database version</b>. "
        "With local BLAST+ you download a database snapshot and never update it "
        "mid-project. The pipeline automatically records which snapshot you used:",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))

    story.append(info_box(
        "data/results/db_version.json  — written on every local run",
        [Paragraph(
            '{ &nbsp;"db_path": "/data/blast/nt", &nbsp;'
            '"db_version": "Database: nt | Date: Feb 14, 2025", &nbsp;'
            '"program": "blastn", &nbsp;'
            '"stamped_at": "2026-05-22T09:00:00Z" }',
            s["code"],
        ),
         Paragraph(
             "This file travels with your results CSV. "
             "Anyone auditing your data — a regulator, a journal reviewer, "
             "or yourself in a year's time — can see exactly which database "
             "produced which identifications.",
             s["box_body"],
         )],
        bg=ORANGE_LIGHT, border=ORANGE, s=s,
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Best practice: archive the db_version.json file alongside your "
        "blast_hit_table.csv. "
        "If you ever re-run the analysis, compare the new version stamp against "
        "the archived one — any difference means results could legitimately differ.",
        s["body"],
    ))

    # ── 8. GLOSSARY ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("8.  Glossary", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))

    glossary = [
        ("BLAST+",
         "The NCBI command-line suite of BLAST programs: blastn, blastx, tblastn, "
         "blastdbcmd, makeblastdb, update_blastdb.pl. The '+' distinguishes the modern "
         "C++ rewrite from the original legacy BLAST."),
        ("blastn",
         "Nucleotide vs nucleotide BLAST. The main program used by this pipeline. "
         "Takes a DNA query and searches a nucleotide database."),
        ("blastdbcmd",
         "A utility for querying and inspecting local BLAST databases. Used by the "
         "pipeline to extract the database version stamp."),
        ("makeblastdb",
         "Converts a plain FASTA file into the binary BLAST database format "
         "(.nsq / .nin / .nhr files). Used when building a custom database "
         "(e.g. SILVA)."),
        ("update_blastdb.pl",
         "A Perl script bundled with BLAST+ that downloads and decompresses "
         "pre-built NCBI databases. Wrapped by scripts/setup_db.py."),
        (".nal file",
         "Database alias file. Points to all volumes of a multi-part database "
         "(e.g. nt.00 through nt.99). BLAST+ reads the alias and automatically "
         "searches all volumes."),
        ("BLAST5 format",
         "The current binary database format introduced in BLAST+ 2.10. "
         "Each database includes a .njs metadata file in JSON format."),
        ("--outfmt 5",
         "The BLAST command-line flag that requests XML output. "
         "The pipeline always uses this format because Biopython's parser reads it "
         "reliably without ambiguity."),
        ("Version stamping",
         "Recording the exact database title and creation date alongside results "
         "so the analysis can be reproduced or audited in the future."),
        ("ThreadPoolExecutor",
         "Python's concurrent.futures class used to run multiple BLAST processes "
         "in parallel. Each worker is an independent process — no shared memory."),
        ("Cache hit",
         "When the pipeline finds an existing non-empty .xml file for a query "
         "and skips the BLAST search entirely. Prevents redundant computation on "
         "re-runs."),
        ("db_version.json",
         "A JSON file written to data/results/ on every local BLAST run. "
         "Records db_path, db_version string, program, and UTC timestamp."),
    ]

    for term, defn in glossary:
        story.append(Paragraph(term, s["gl_term"]))
        story.append(Paragraph(defn, s["gl_def"]))

    # ── KEY TAKEAWAYS ─────────────────────────────────────────────────────────
    story.append(info_box(
        "Key Takeaways",
        [Paragraph(
            "• <b>Local BLAST+ is the production choice.</b>  Faster, no rate limits, "
            "fully offline — use it for any run that matters.<br/>"
            "• <b>Database choice matters more than parameters.</b>  Pick the database "
            "that covers your marker gene and target organisms.<br/>"
            "• <b>Small databases first.</b>  16S (~1 GB) or ITS (~300 MB) let you test "
            "everything before committing to nt (~300 GB).<br/>"
            "• <b>Version-stamp every run.</b>  db_version.json is your audit trail — "
            "commit it alongside your results.<br/>"
            "• <b>Threading scales with storage speed.</b>  --threads 4 is a safe "
            "default on SSDs; --threads 1 is safest on spinning hard drives.",
            s["box_body"],
        )],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s,
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Next: Module 03 — Regulatory PDF Reports &amp; Data Visualisation",
        s["caption"],
    ))

    return story


# ── Entry point ───────────────────────────────────────────────────────────────
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
