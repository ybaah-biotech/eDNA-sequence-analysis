#!/usr/bin/env python3
"""
Generate Module 01 — BLAST & Sequence Alignment
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

OUTPUT = Path(__file__).parent / "Module_01_BLAST_and_Alignment.pdf"

# ── Colour palette ────────────────────────────────────────────────────────────
TEAL_DARK   = colors.HexColor("#1B4F72")
TEAL_MID    = colors.HexColor("#2E86C1")
GREEN_DARK  = colors.HexColor("#1E8449")
GREEN_LIGHT = colors.HexColor("#EAFAF1")
BLUE_LIGHT  = colors.HexColor("#EBF5FB")
ORANGE      = colors.HexColor("#D35400")
GREY_LIGHT  = colors.HexColor("#F2F3F4")
GREY_MID    = colors.HexColor("#BDC3C7")
WHITE       = colors.white
BLACK       = colors.black


# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    s = {}
    def st(name, **kw):
        s[name] = ParagraphStyle(name, **kw)

    st("title_main",    fontName="Helvetica-Bold",    fontSize=26, textColor=WHITE,       leading=32, alignment=TA_CENTER)
    st("title_sub",     fontName="Helvetica",          fontSize=13, textColor=colors.HexColor("#AED6F1"), leading=18, alignment=TA_CENTER)
    st("module_label",  fontName="Helvetica-Bold",    fontSize=44, textColor=colors.HexColor("#AED6F1"), leading=52, alignment=TA_CENTER)
    st("h1",            fontName="Helvetica-Bold",    fontSize=15, textColor=TEAL_DARK,   leading=20, spaceBefore=14, spaceAfter=4)
    st("h2",            fontName="Helvetica-Bold",    fontSize=12, textColor=TEAL_MID,    leading=16, spaceBefore=10, spaceAfter=3)
    st("body",          fontName="Helvetica",          fontSize=10, textColor=BLACK,       leading=15, spaceAfter=5,  alignment=TA_JUSTIFY)
    st("body_b",        fontName="Helvetica-Bold",    fontSize=10, textColor=BLACK,       leading=15, spaceAfter=4)
    st("bullet",        fontName="Helvetica",          fontSize=10, textColor=BLACK,       leading=15, leftIndent=14, spaceAfter=3)
    st("box_head",      fontName="Helvetica-Bold",    fontSize=10, textColor=TEAL_DARK,   leading=14, spaceAfter=3)
    st("box_body",      fontName="Helvetica",          fontSize=10, textColor=BLACK,       leading=14, alignment=TA_JUSTIFY)
    st("code",          fontName="Courier",            fontSize=9,  textColor=colors.HexColor("#1A5276"), leading=13, leftIndent=6, spaceAfter=3)
    st("caption",       fontName="Helvetica-Oblique", fontSize=8.5,textColor=colors.HexColor("#707B7C"), leading=12, alignment=TA_CENTER)
    st("gl_term",       fontName="Helvetica-Bold",    fontSize=10, textColor=GREEN_DARK,  leading=13, spaceAfter=1)
    st("gl_def",        fontName="Helvetica",          fontSize=10, textColor=BLACK,       leading=13, leftIndent=10, spaceAfter=7)
    return s


# ── Helpers ───────────────────────────────────────────────────────────────────
def coloured_banner(text_para, bg, col_w=14*cm, pad_top=12, pad_bot=12):
    t = Table([[text_para]], colWidths=[col_w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("LEFTPADDING",   (0,0),(-1,-1), 24),
        ("RIGHTPADDING",  (0,0),(-1,-1), 24),
        ("TOPPADDING",    (0,0),(-1,-1), pad_top),
        ("BOTTOMPADDING", (0,0),(-1,-1), pad_bot),
    ]))
    return t


def info_box(title, paras, bg, border=None, s=None):
    border = border or TEAL_MID
    inner  = ([Paragraph(title, s["box_head"])] if title else []) + paras
    t = Table([[inner]], colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("BOX",           (0,0),(-1,-1), 1.2, border),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    return t


def two_col_table(headers, rows, s, col_widths=None):
    n = len(headers)
    col_widths = col_widths or [14*cm/n]*n
    data = [[Paragraph(h, s["body_b"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(c, s["body"]) for c in row])
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1, 0), TEAL_DARK),
        ("TEXTCOLOR",     (0,0),(-1, 0), WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, GREY_LIGHT]),
        ("BOX",           (0,0),(-1,-1), 0.8, GREY_MID),
        ("INNERGRID",     (0,0),(-1,-1), 0.4, GREY_MID),
        ("LEFTPADDING",   (0,0),(-1,-1), 7),
        ("RIGHTPADDING",  (0,0),(-1,-1), 7),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    return t


def step_row(num, title, colour, desc, s):
    t = Table(
        [[Paragraph(f"{num}. {title}", ParagraphStyle("sr", fontName="Helvetica-Bold",
           fontSize=10, textColor=WHITE, leading=14)),
          Paragraph(desc, s["box_body"])]],
        colWidths=[3.2*cm, 10.8*cm]
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,0), colour),
        ("BACKGROUND",    (1,0),(1,0), GREY_LIGHT),
        ("BOX",           (0,0),(-1,-1), 0.8, GREY_MID),
        ("LEFTPADDING",   (0,0),(-1,-1), 9),
        ("RIGHTPADDING",  (0,0),(-1,-1), 9),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    return t


# ── Document build ────────────────────────────────────────────────────────────
def build(s):
    story = []

    # ── TITLE PAGE ────────────────────────────────────────────────────────────
    story.append(coloured_banner(
        Paragraph("MODULE 01", s["module_label"]), TEAL_DARK, pad_top=28, pad_bot=6
    ))
    story.append(coloured_banner(
        Paragraph("BLAST &amp; Sequence Alignment", s["title_main"]), TEAL_MID, pad_top=14, pad_bot=14
    ))
    story.append(coloured_banner(
        Paragraph("eDNA Bioinformatics Learning Series  ·  Yaw Baah", s["title_sub"]), GREEN_DARK, pad_top=7, pad_bot=7
    ))
    story.append(Spacer(1, 0.8*cm))

    story.append(Paragraph(
        "This module covers the foundational tool behind the entire eDNA pipeline: "
        "<b>BLAST</b> (Basic Local Alignment Search Tool). You will learn how sequence "
        "alignment works, what BLAST is doing under the hood, how to read its key "
        "output metrics, and why switching from web BLAST to a local installation is "
        "critical for large-scale and commercial environmental studies.",
        s["body"]
    ))
    story.append(Spacer(1, 0.4*cm))

    story.append(info_box("What you will learn", [
        Paragraph("&#x2714;  What sequence alignment is and why it matters for eDNA", s["bullet"]),
        Paragraph("&#x2714;  How BLAST works step by step, in plain English", s["bullet"]),
        Paragraph("&#x2714;  How to read BLAST output: E-value, % identity, bit score, query coverage", s["bullet"]),
        Paragraph("&#x2714;  The difference between web BLAST and local BLAST+", s["bullet"]),
        Paragraph("&#x2714;  Where BLAST sits in your complete eDNA pipeline", s["bullet"]),
    ], BLUE_LIGHT, TEAL_MID, s))
    story.append(PageBreak())

    # ── 1. THE PROBLEM ───────────────────────────────────────────────────────
    story.append(Paragraph("1.  The Problem BLAST Solves", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "When you collect an eDNA sample from a pond and sequence it, you get back "
        "thousands — sometimes millions — of short DNA sequences. Each one looks "
        "something like this:",
        s["body"]
    ))
    story.append(Paragraph("ATCGATCGGAATCTACGATCGATCGATCGATCGATCGTACGATCGATCG...", s["code"]))
    story.append(Paragraph(
        "There are no labels. No organism names. Just raw nucleotide letters. "
        "The fundamental question is: <b>which organism does this sequence come from?</b> "
        "BLAST answers this by comparing your unknown sequence against a database of "
        "hundreds of millions of sequences from known organisms.",
        s["body"]
    ))
    story.append(Spacer(1, 0.25*cm))
    story.append(info_box("Analogy — The Forensic Library", [Paragraph(
        "Imagine finding a page torn from an unknown book. To identify it, you visit a "
        "library and compare that page against every book on the shelves. When you find "
        "the closest match — even if not word-for-word identical — you can say: "
        "<i>this page probably came from that book</i>. "
        "<b>BLAST is the librarian performing that search for DNA sequences.</b> "
        "The library is the NCBI nucleotide database — currently over 500 billion bases "
        "from millions of known organisms worldwide.",
        s["box_body"]
    )], GREEN_LIGHT, GREEN_DARK, s))

    # ── 2. ALIGNMENT ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("2.  What is Sequence Alignment?", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Alignment means lining up two sequences so matching bases sit above each other. "
        "Gaps ( - ) are inserted where one sequence has an insertion or deletion the other lacks.",
        s["body"]
    ))
    story.append(Paragraph("Query  :   ATCG-ATCGATCG", s["code"]))
    story.append(Paragraph("           |||| ||||||||", s["code"]))
    story.append(Paragraph("Subject:   ATCGAATCGATCG", s["code"]))
    story.append(Paragraph("12 of 13 positions match — 92.3 % identity. The dash is a gap (one base insertion in subject).", s["caption"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(two_col_table(
        ["Type", "What it does", "When used"],
        [
            ["<b>Global</b>", "Aligns end-to-end across full length", "Closely related sequences of similar length"],
            ["<b>Local</b>", "Finds best-matching region — even a sub-segment", "BLAST uses this — your eDNA read may only match part of a long database entry"],
        ],
        s, col_widths=[2.5*cm, 5.5*cm, 6*cm]
    ))

    # ── 3. HOW BLAST WORKS ───────────────────────────────────────────────────
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("3.  How BLAST Works — Three Stages", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "A naive approach would check every sequence in the database — impossible at "
        "500 billion bases. BLAST uses a three-stage shortcut to be fast without "
        "sacrificing accuracy:",
        s["body"]
    ))
    story.append(Spacer(1, 0.2*cm))
    for step in [
        (1, "Seeding", TEAL_MID,
         "BLAST breaks your query into short overlapping words called <b>k-mers</b> "
         "(default: 11 bases). It scans the database for exact matches to these words "
         "using an index — like looking up a term in a book's index rather than reading "
         "every page."),
        (2, "Extension", GREEN_DARK,
         "Each seed match is extended in both directions, one base at a time. "
         "Extension continues while the alignment score improves. When the score drops "
         "below a cutoff, it stops — preventing wasted time on poor matches."),
        (3, "Scoring and Reporting", ORANGE,
         "Each extended match (called an <b>HSP — High-Scoring Pair</b>) receives a "
         "score based on: identical bases (+), mismatches (-), gap penalties. "
         "BLAST calculates statistical confidence and reports all alignments above "
         "your threshold, ranked by score."),
    ]:
        story.append(step_row(*step, s=s))
        story.append(Spacer(1, 0.12*cm))

    # ── 4. KEY METRICS ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4.  Reading BLAST Output — The Four Key Numbers", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Every BLAST hit returns four numbers. Your pipeline stores all of them in "
        "<b>blast_hit_table.csv</b>. Knowing what they mean is essential to interpreting "
        "biodiversity results correctly.",
        s["body"]
    ))
    story.append(Spacer(1, 0.25*cm))

    metrics = [
        ("% Identity  (identity_pct)", TEAL_DARK, GREEN_LIGHT, GREEN_DARK,
         "The percentage of aligned bases that are <i>identical</i> between your query and the database match.",
         [("97 – 100 %", "Species-level assignment reliable"),
          ("90 – 96 %",  "Genus-level reliable; species uncertain"),
          ("80 – 89 %",  "Family-level only; treat with caution"),
          ("&lt; 80 %",    "Too divergent for confident classification")],
         "Your pipeline uses this to set the <b>confidence_flag</b> column (high / medium / low) "
         "and drives the LCA downgrading logic in resolve_taxonomy()."),

        ("E-value  (evalue)", colors.HexColor("#1A5276"), BLUE_LIGHT, TEAL_MID,
         "The number of times you would expect to see a match this good <i>by chance</i> "
         "in a database of this size. Lower = more significant.",
         [("1e-100",  "Near-certain match — extremely significant"),
          ("1e-10",   "Significant — your pipeline default threshold"),
          ("1e-5",    "Weak but possibly real — use with caution"),
          ("&gt; 0.01", "Likely random noise — discard")],
         "Think of E-value like a p-value in statistics. Your pipeline filters out anything "
         "above 1e-10 by default via the <b>--evalue</b> flag."),

        ("Bit Score  (bit_score)", colors.HexColor("#7D6608"), colors.HexColor("#FEFCBF"), colors.HexColor("#9A7D0A"),
         "A normalised score that accounts for the scoring matrix used. Higher is always better. "
         "Unlike raw scores, bit scores are comparable across different database sizes.",
         [("&gt; 200", "Strong alignment"),
          ("50 – 200", "Moderate alignment"),
          ("&lt; 50",  "Weak — likely unreliable")],
         "Your pipeline uses bit score to select the <b>best HSP</b> when a single alignment "
         "has multiple non-contiguous matching segments."),

        ("Query Coverage %  (query_coverage_pct)", colors.HexColor("#7B241C"), colors.HexColor("#FDEDEC"), colors.HexColor("#922B21"),
         "The percentage of your query sequence covered by the alignment. "
         "High identity on a tiny fragment is far less meaningful than high identity across the full sequence.",
         [("&gt; 90 %",  "Good — full-length match"),
          ("50 – 90 %", "Partial match — interpret carefully"),
          ("&lt; 50 %",  "Fragment only — low confidence")],
         "Your pipeline clamps this to 100 % maximum. Subject insertions can push the raw "
         "value above 100, which is mathematically meaningless."),
    ]

    for metric_name, hdr_col, bg_col, border_col, desc, thresholds, note in metrics:
        story.append(Paragraph(metric_name, s["h2"]))
        story.append(Paragraph(desc, s["body"]))
        thresh_data = [[Paragraph("Value", s["body_b"]), Paragraph("Interpretation", s["body_b"])]]
        for val, interp in thresholds:
            thresh_data.append([Paragraph(val, s["code"]), Paragraph(interp, s["body"])])
        t = Table(thresh_data, colWidths=[3.5*cm, 10.5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1, 0), hdr_col),
            ("TEXTCOLOR",     (0,0),(-1, 0), WHITE),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [bg_col, WHITE]),
            ("BOX",           (0,0),(-1,-1), 0.8, GREY_MID),
            ("INNERGRID",     (0,0),(-1,-1), 0.4, GREY_MID),
            ("LEFTPADDING",   (0,0),(-1,-1), 7),
            ("RIGHTPADDING",  (0,0),(-1,-1), 7),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.1*cm))
        story.append(info_box("Pipeline note:", [Paragraph(note, s["box_body"])], GREY_LIGHT, GREY_MID, s))
        story.append(Spacer(1, 0.35*cm))

    # ── 5. WEB vs LOCAL ───────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("5.  Web BLAST vs Local BLAST+", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Your original pipeline used NCBI's web BLAST service. Phase 1 of the commercial "
        "build replaces this with a local BLAST+ installation. Here is exactly why that matters:",
        s["body"]
    ))
    story.append(Spacer(1, 0.25*cm))
    story.append(two_col_table(
        ["Property", "Web BLAST (original)", "Local BLAST+ (Phase 1)"],
        [
            ["Speed per sequence",      "30 – 120 seconds",              "0.01 – 1 second"],
            ["10,000 sequences",        "~9 hours",                      "5 – 15 minutes"],
            ["Rate limit",              "3 requests/sec (NCBI enforced)","No limit — uses your CPU"],
            ["Reproducibility",         "Database updates silently",     "Database version locked and logged"],
            ["Regulatory compliance",   "Cannot cite 'NCBI as of today'","Version stamped in every output CSV"],
            ["Internet required",       "Yes — fails offline",           "No — fully local"],
            ["Cost",                    "Free but limited",              "Free, unlimited, scales with hardware"],
        ],
        s, col_widths=[4*cm, 5*cm, 5*cm]
    ))
    story.append(Spacer(1, 0.35*cm))
    story.append(info_box("Why reproducibility is non-negotiable for commercial work", [
        Paragraph(
            "If you run your pipeline today and again in six months, NCBI will have added new sequences. "
            "You could get different species assignments for the same input — not because the biology "
            "changed, but because the database did. A client comparing two reports would see "
            "inconsistencies that look like errors. "
            "<b>Local BLAST+ with a versioned database eliminates this entirely.</b> "
            "The database version is stamped into every output file — the same way a lab "
            "records the reagent batch number for regulatory traceability.",
            s["box_body"]
        )
    ], BLUE_LIGHT, TEAL_MID, s))
    story.append(Spacer(1, 0.35*cm))

    story.append(Paragraph("What changes in the code", s["h2"]))
    story.append(Paragraph(
        "The science is <i>identical</i> — same algorithm, same scoring, same XML output. "
        "Only the transport layer changes: instead of an HTTP request to NCBI, "
        "Python calls the local <b>blastn</b> binary via subprocess:",
        s["body"]
    ))
    story.append(Paragraph("# BEFORE — web BLAST (network call to NCBI)", s["code"]))
    story.append(Paragraph("result = NCBIWWW.qblast('blastn', 'nt', sequence)", s["code"]))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph("# AFTER — local BLAST+ (subprocess call to binary)", s["code"]))
    story.append(Paragraph("blastn -query seq.fasta -db /data/nt -outfmt 5 -num_threads 8", s["code"]))
    story.append(Spacer(1, 0.2*cm))
    story.append(info_box("What -num_threads 8 does", [
        Paragraph(
            "BLAST is <i>embarrassingly parallel</i> — each query sequence is independent of the others. "
            "The <b>-num_threads</b> flag tells BLAST to process multiple sequences simultaneously "
            "across CPU cores. On a modern 8-core laptop this gives a 6-8x speed boost. "
            "On a 32-core cloud server you can classify tens of thousands of sequences in minutes.",
            s["box_body"]
        )
    ], GREEN_LIGHT, GREEN_DARK, s))

    # ── 6. PIPELINE FLOW ─────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("6.  Where BLAST Sits in Your Pipeline", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Full data flow from a pond water sample to a classified species report, "
        "showing exactly where BLAST fits:",
        s["body"]
    ))
    story.append(Spacer(1, 0.25*cm))

    flow = [
        ("1", "Sample collection",  False, "Pond water filtered through a membrane. DNA extracted and amplified by PCR using marker-specific primers (16S rRNA for bacteria, 18S rRNA for eukaryotes, ITS for fungi, COI for invertebrates)."),
        ("2", "Sequencing",         False, "Illumina or Oxford Nanopore reads the amplified DNA. Output: millions of short sequences in FASTQ format, each with a quality score per base."),
        ("3", "Quality filtering",  False, "Low-quality reads, chimeric sequences, and primer artefacts removed. Output: clean FASTA file ready for identification."),
        ("4", "BLAST",              True,  "Each clean sequence is aligned against the reference database. Output: XML file with top hits, scores, and E-values per query sequence."),
        ("5", "Parsing + LCA",      False, "src/parser.py extracts species names from BLAST XML. resolve_taxonomy() applies Lowest Common Ancestor logic to determine the most confident taxonomic level."),
        ("6", "Diversity metrics",  False, "Shannon H', Pielou J', and species richness calculated from resolved taxonomy. Output: biodiversity_summary.csv"),
        ("7", "PDF report",         False, "Formatted report generated with species table, confidence flags, protected species alerts, and diversity charts. (Phase 2)"),
    ]

    flow_data = [[
        Paragraph("#", ParagraphStyle("fh", fontName="Helvetica-Bold", fontSize=9.5, textColor=WHITE)),
        Paragraph("Stage", ParagraphStyle("fh", fontName="Helvetica-Bold", fontSize=9.5, textColor=WHITE)),
        Paragraph("What happens", ParagraphStyle("fh", fontName="Helvetica-Bold", fontSize=9.5, textColor=WHITE)),
    ]]
    for num, stage, highlight, desc in flow:
        note = "   <-- YOU ARE HERE" if highlight else ""
        stage_col = GREEN_DARK if highlight else BLACK
        row_bg    = GREEN_LIGHT if highlight else (WHITE if int(num)%2 else GREY_LIGHT)
        flow_data.append([
            Paragraph(num,                 s["body_b"]),
            Paragraph(f"<b>{stage}</b>{note}", ParagraphStyle("fs", fontName="Helvetica-Bold", fontSize=10, textColor=stage_col, leading=14)),
            Paragraph(desc,                s["body"]),
        ])

    ft = Table(flow_data, colWidths=[0.7*cm, 3.8*cm, 9.5*cm])
    # Build per-row background
    style_cmds = [
        ("BACKGROUND",    (0,0),(-1, 0), TEAL_DARK),
        ("BOX",           (0,0),(-1,-1), 0.8, GREY_MID),
        ("INNERGRID",     (0,0),(-1,-1), 0.4, GREY_MID),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]
    for i, (num, _, highlight, _) in enumerate(flow, start=1):
        bg = GREEN_LIGHT if highlight else (WHITE if i%2==1 else GREY_LIGHT)
        style_cmds.append(("BACKGROUND", (0,i),(-1,i), bg))
    ft.setStyle(TableStyle(style_cmds))
    story.append(ft)

    # ── 7. GLOSSARY ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("7.  Glossary", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))

    for term, defn in sorted([
        ("Alignment",      "Arranging two or more sequences to identify regions of similarity."),
        ("ASV",            "Amplicon Sequence Variant — exact sequence produced by denoising; higher resolution than OTUs."),
        ("Bit score",      "Normalised alignment score — higher is better, comparable across database sizes."),
        ("BLAST",          "Basic Local Alignment Search Tool — finds similar sequences in a database."),
        ("blastn",         "BLAST program for nucleotide vs nucleotide searches (DNA query, DNA database)."),
        ("COI",            "Cytochrome c Oxidase subunit I — mitochondrial gene used as a barcode for animals."),
        ("E-value",        "Expect value — expected number of random hits with that score. Lower = more significant."),
        ("eDNA",           "Environmental DNA — genetic material shed into surroundings (water, soil, air)."),
        ("HSP",            "High-Scoring Pair — a local alignment found by BLAST. One alignment can have multiple HSPs."),
        ("ITS",            "Internal Transcribed Spacer — ribosomal DNA region used as a barcode, especially for fungi."),
        ("k-mer",          "Short sequence of k bases used as a seed in BLAST's initial scanning step."),
        ("LCA",            "Lowest Common Ancestor — assigns taxonomy at the deepest level all top hits agree on."),
        ("Metabarcoding",  "Sequencing and identifying DNA from mixed environmental samples."),
        ("OTU",            "Operational Taxonomic Unit — cluster of sequences at 97 % identity, used as a species proxy."),
        ("Query coverage", "Percentage of your query sequence spanned by the BLAST alignment."),
        ("16S rRNA",       "Bacterial ribosomal gene — universal prokaryote barcode."),
        ("18S rRNA",       "Eukaryotic ribosomal gene — used for algae, protists, micro-eukaryotes."),
        ("% identity",     "Percentage of aligned bases that are identical between query and subject."),
    ], key=lambda x: x[0].lower()):
        story.append(Paragraph(term, s["gl_term"]))
        story.append(Paragraph(defn, s["gl_def"]))

    # ── KEY TAKEAWAYS ─────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Key Takeaways", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.3*cm))

    for title, desc in [
        ("BLAST is a seed-and-extend algorithm, not brute force",
         "It finds short exact k-mer matches first, then extends them — making it thousands of times faster than aligning against every database sequence naively."),
        ("E-value is your primary significance filter",
         "It tells you the statistical probability of a random hit. Your pipeline defaults to 1e-10. Anything above 0.01 is likely noise."),
        ("97 % identity is the species-level threshold",
         "Below 97 %, the sequence is too divergent to reliably name a species for most eDNA barcoding markers (16S, 18S, ITS, COI). Your pipeline's LCA logic respects this boundary automatically."),
        ("Web BLAST is not reproducible — local BLAST+ is",
         "Database updates silently on NCBI. For commercial and regulatory work, you need a version-locked local database with the version number stamped in your outputs."),
        ("Local BLAST+ is the same science, faster delivery",
         "Same algorithm, same scoring matrix, same XML output format — just runs on your hardware instead of NCBI's servers. Your pipeline wraps this transparently behind --local."),
    ]:
        story.append(info_box(f"&#x2B50;  {title}", [Paragraph(desc, s["box_body"])], BLUE_LIGHT, TEAL_MID, s))
        story.append(Spacer(1, 0.18*cm))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREY_MID))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        "Next:  <b>Module 02 — Regulatory Reporting &amp; Data Visualisation</b>  "
        "·  eDNA Bioinformatics Learning Series",
        s["caption"]
    ))
    return story


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm,
        title="Module 01 — BLAST & Sequence Alignment",
        author="eDNA Bioinformatics Learning Series",
    )
    doc.build(build(make_styles()))
    print(f"PDF saved: {OUTPUT}")


if __name__ == "__main__":
    main()
