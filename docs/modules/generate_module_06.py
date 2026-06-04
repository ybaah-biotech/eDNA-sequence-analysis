#!/usr/bin/env python3
"""
Generate Module 06 — Rarefaction, Beta Diversity & Community Comparison
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

OUTPUT = Path(__file__).parent / "Module_06_Rarefaction_and_Beta_Diversity.pdf"

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
        Paragraph("MODULE 06", s["module_label"]), TEAL_DARK, pad_top=28, pad_bot=6
    ))
    story.append(coloured_banner(
        Paragraph("Rarefaction, Beta Diversity &amp; Community Comparison", s["title_main"]),
        TEAL_MID, pad_top=14, pad_bot=14,
    ))
    story.append(coloured_banner(
        Paragraph("eDNA Bioinformatics Learning Series  ·  Yaw Baah", s["title_sub"]),
        GREEN_DARK, pad_top=7, pad_bot=7,
    ))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(
        "Modules 01 to 05 taught you how to identify species from sequences "
        "and how to summarise one community with Shannon H' and Pielou J'. "
        "This module introduces two new questions: "
        "<b>are your samples comparable?</b> (rarefaction) "
        "and <b>how different are two communities from each other?</b> (beta diversity). "
        "These are the tools that turn a list of species into ecological insight.",
        s["body"],
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(info_box(
        "What you will learn",
        [Paragraph(
            "1. The sampling depth problem and why it makes raw comparisons unfair  &nbsp; "
            "2. Rarefaction — what it is, how it works, rarefaction curves  &nbsp; "
            "3. Alpha diversity recap — Shannon H', Pielou J', and Chao1  &nbsp; "
            "4. Beta diversity — Bray-Curtis and Jaccard explained  &nbsp; "
            "5. Ordination — PCoA and how to read a community plot  &nbsp; "
            "6. Real-world applications in freshwater eDNA surveys  &nbsp; "
            "7. Glossary",
            s["box_body"],
        )],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s,
    ))

    # ── 1. THE SAMPLING DEPTH PROBLEM ─────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("1.  The Sampling Depth Problem", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Imagine you take eDNA samples from two ponds and send them for sequencing. "
        "The sequencer returns:",
        s["body"],
    ))
    story.append(Paragraph("• Pond A — 10,000 reads → 22 species identified", s["bullet"]))
    story.append(Paragraph("• Pond B — 800 reads → 9 species identified", s["bullet"]))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "Is Pond A genuinely more diverse? Or did it simply receive more sequencing "
        "and therefore more opportunities to detect rare species? "
        "You cannot tell. The comparison is not fair.",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "This is the <b>sequencing depth problem</b>. "
        "Deeper sequencing always finds more species — not because they weren't "
        "there before, but because rare species only appear in a small fraction "
        "of reads and require large sample sizes to detect. "
        "Comparing species richness or Shannon H' across samples "
        "with different sequencing depths introduces systematic bias.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(info_box(
        "Why this matters for eDNA consulting",
        [Paragraph(
            "If you are comparing two sites — upstream and downstream of a discharge "
            "point, or a reference site against an impacted site — "
            "and one sample has five times the sequencing depth of the other, "
            "any apparent difference in diversity could be entirely explained "
            "by that depth difference. "
            "A regulator reviewing your report should ask: "
            "were these samples rarefied before comparison? "
            "The answer must be yes.",
            s["box_body"],
        )],
        bg=AMBER_LIGHT, border=AMBER, s=s,
    ))

    # ── 2. RAREFACTION ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("2.  Rarefaction", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Rarefaction is the solution to the sampling depth problem. "
        "The principle is simple: <b>randomly subsample all samples down "
        "to the same sequencing depth</b>, then compare.",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "Using the example above: both samples are subsampled to 800 reads "
        "(the depth of the shallower sample). "
        "You randomly discard reads from Pond A until it also has 800. "
        "Now both samples have been given the same number of reads to 'work with', "
        "and species richness can be compared fairly.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph("Rarefaction curves", s["h2"]))
    story.append(Paragraph(
        "A rarefaction curve plots <b>number of reads sampled</b> (x-axis) "
        "against <b>number of species discovered</b> (y-axis). "
        "Every additional read has some probability of belonging to a species "
        "not yet seen — early reads find species quickly, "
        "later reads increasingly find species already counted.",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))

    curve_header = [
        Paragraph("Curve shape", s["th"]),
        Paragraph("What it tells you", s["th"]),
        Paragraph("Action", s["th"]),
    ]
    curve_rows = [
        ("Plateau reached",
         "Species accumulation has levelled off. "
         "Additional reads are unlikely to find new species.",
         "Sample is well-sequenced. Diversity estimate is reliable."),
        ("Still climbing steeply",
         "Many species remain undetected. "
         "The true community is richer than the data shows.",
         "Undersample — treat richness as a minimum estimate. "
         "Consider deeper sequencing if budget allows."),
        ("Flat from the start",
         "Very low diversity — one or two taxa dominate. "
         "Saturation reached almost immediately.",
         "Low-diversity community. "
         "Check for contamination or stress-dominated site."),
    ]
    curve_data = [curve_header]
    for shape, meaning, action in curve_rows:
        curve_data.append([
            Paragraph(f"<b>{shape}</b>", s["td"]),
            Paragraph(meaning, s["td"]),
            Paragraph(action, s["td"]),
        ])
    curve_table = Table(curve_data, colWidths=[3.5*cm, 5.5*cm, 5.0*cm])
    curve_table.setStyle(TableStyle([
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
    story.append(curve_table)
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Choosing the rarefaction depth", s["h2"]))
    story.append(Paragraph(
        "Standard practice: rarefy all samples to the <b>minimum sequencing depth</b> "
        "across the dataset. This ensures all samples are treated equally. "
        "The cost is information loss — samples with 10,000 reads are "
        "reduced to the minimum. "
        "If one sample has drastically fewer reads than all others (e.g. 50 reads "
        "vs 5,000), it is usually better to remove that outlier than "
        "to sacrifice 99% of the data from every other sample.",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(info_box(
        "Pipeline note — Phase 6",
        [Paragraph(
            "Phase 6 of the pipeline will add rarefaction to the workflow. "
            "The pipeline will generate rarefaction curves per sample, "
            "rarefy all samples to a user-specified or auto-detected minimum depth, "
            "and re-calculate Shannon H' and Pielou J' on the rarefied table. "
            "The PDF report will include a rarefaction curve plot for each sample.",
            s["box_body"],
        )],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s,
    ))

    # ── 3. ALPHA DIVERSITY RECAP + CHAO1 ──────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("3.  Alpha Diversity Recap and Chao1", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "<b>Alpha diversity</b> measures diversity <i>within</i> a single sample. "
        "You already know Shannon H' and Pielou J' from Module 03. "
        "This section introduces a third metric — Chao1 — "
        "which estimates how many species you probably missed.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(two_col(
        [
            ("Metric",      "What it measures"),
            ("Shannon H'",  "Diversity combining richness and evenness. "
                            "Higher = more diverse. Maximum = ln(S)."),
            ("Pielou J'",   "Evenness only. 0-1 scale. "
                            "1.0 = perfectly even distribution across all taxa."),
            ("Species richness (S)",
                            "Raw count of distinct taxa. "
                            "Sensitive to sequencing depth — always report alongside rarefaction."),
            ("Chao1",       "Estimated true richness including unseen species. "
                            "Always &gt;= S. Useful when samples are undersequenced."),
        ],
        col_a_w=3.5 * cm, header_bg=TEAL_DARK, s=s,
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Chao1 — estimating unseen species", s["h2"]))
    story.append(Paragraph(
        "eDNA surveys inevitably miss rare species. "
        "A species present at very low abundance may not appear in any reads "
        "even when present in the water. "
        "Chao1 uses the number of <b>singletons</b> (species seen exactly once) "
        "and <b>doubletons</b> (species seen exactly twice) "
        "to estimate how many species are likely present but unseen.",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "Formula: <b>S_chao1 = S_obs + (F1<super>2</super> / 2 x F2)</b>",
        s["body"],
    ))
    story.append(Paragraph(
        "Where S_obs = observed species, F1 = number of singletons, "
        "F2 = number of doubletons.",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(info_box(
        "Worked example",
        [Paragraph(
            "A survey returns S_obs = 14 species. "
            "F1 = 6 singletons (6 species seen in only one read). "
            "F2 = 3 doubletons. "
            "Chao1 = 14 + (36 / 6) = 14 + 6 = <b>20 estimated species</b>. "
            "The pipeline detected 14 but Chao1 suggests 20 are likely present. "
            "The gap (6 species) represents the estimated detection gap — "
            "real organisms whose DNA was present but too rare to appear in the reads.",
            s["box_body"],
        )],
        bg=GREEN_LIGHT, border=GREEN_DARK, s=s,
    ))

    # ── 4. BETA DIVERSITY ─────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4.  Beta Diversity — Comparing Communities", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "<b>Beta diversity</b> measures how different two communities are from each other. "
        "Where alpha diversity describes one sample, "
        "beta diversity describes the relationship between samples.",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "Alpha diversity: <i>How diverse is Pond A?</i>",
        s["body"],
    ))
    story.append(Paragraph(
        "Beta diversity: <i>How different is Pond A from Pond B?</i>",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph("Bray-Curtis dissimilarity", s["h2"]))
    story.append(Paragraph(
        "Bray-Curtis is the most widely used beta diversity metric in ecology. "
        "It ranges from 0 (identical communities) to 1 (completely different). "
        "It accounts for <b>abundance</b> — not just whether a species is present, "
        "but how many reads it produced.",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "Formula: <b>BC = 1 - (2 x shared abundance) / (total A + total B)</b>",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(two_col(
        [
            ("Bray-Curtis value", "Interpretation"),
            ("0.0",              "Identical communities — same species, same abundances"),
            ("0.0 – 0.3",        "Very similar — minor compositional differences"),
            ("0.3 – 0.6",        "Moderately different — some shared taxa, clear differences"),
            ("0.6 – 0.9",        "Substantially different — few shared dominant taxa"),
            ("1.0",              "Completely different — no shared species"),
        ],
        col_a_w=4.0 * cm, header_bg=TEAL_DARK, s=s,
    ))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Jaccard index", s["h2"]))
    story.append(Paragraph(
        "Jaccard is a simpler metric based on <b>presence/absence only</b>. "
        "It ignores abundance — a species seen once counts the same as one seen 1,000 times. "
        "Use Jaccard when you care about community composition "
        "(which species are there?) not relative dominance "
        "(how many of each?).",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "Formula: <b>J = shared species / (species in A + species in B - shared species)</b>",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(info_box(
        "Bray-Curtis vs Jaccard — when to use which",
        [
            Paragraph(
                "<b>Use Bray-Curtis</b> when abundance matters — "
                "e.g. is one taxon dominating Pond B compared to Pond A? "
                "Is the community structure shifted even if the same species are present?",
                s["box_body"],
            ),
            Spacer(1, 0.05 * cm),
            Paragraph(
                "<b>Use Jaccard</b> when you only care about species turnover — "
                "e.g. how many species are unique to the impacted site vs the reference? "
                "Good for biodiversity assessments where abundance data is unreliable.",
                s["box_body"],
            ),
        ],
        bg=PURPLE_LIGHT, border=PURPLE_DARK, s=s,
    ))

    # ── 5. ORDINATION ─────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("5.  Ordination — Visualising Beta Diversity", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "With ten samples, you have 45 pairwise beta diversity comparisons. "
        "With 50 samples, you have 1,225. "
        "A table of pairwise distances is unreadable. "
        "<b>Ordination</b> reduces this distance matrix to two dimensions "
        "so you can see the pattern at a glance.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph("PCoA — Principal Coordinates Analysis", s["h2"]))
    story.append(Paragraph(
        "PCoA takes the beta diversity matrix (e.g. all pairwise Bray-Curtis values) "
        "and finds the two axes that capture the most variation. "
        "Each sample is plotted as a single dot. "
        "<b>Samples that are ecologically similar cluster together. "
        "Samples that are ecologically different are far apart.</b>",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph("How to read a PCoA plot:", s["h2"]))
    story.append(Spacer(1, 0.05 * cm))
    for b in [
        "<b>Axis labels</b> show the percentage of total variation explained — "
        "e.g. 'PC1 (42% variance)'. PC1 captures the biggest ecological gradient. "
        "PC2 captures the second biggest.",
        "<b>Clusters</b> — dots that group together represent samples with similar "
        "community composition. A cluster of upstream samples vs a cluster of "
        "downstream samples indicates the discharge is changing community structure.",
        "<b>Distance between dots</b> is meaningful — samples far apart are "
        "substantially different communities. Samples close together are similar.",
        "<b>Outliers</b> — a single sample far from all others may indicate "
        "contamination, a failed sequencing run, or a genuinely unusual community.",
        "<b>Overlapping clusters</b> — if impacted and reference samples "
        "completely overlap, the communities are similar and no impact is detectable.",
    ]:
        story.append(Paragraph(f"• {b}", s["bullet"]))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph("NMDS — an alternative to PCoA", s["h2"]))
    story.append(Paragraph(
        "Non-metric Multidimensional Scaling (NMDS) is another ordination method "
        "commonly used in ecology. Unlike PCoA, it uses rank-order distances "
        "rather than actual distances, making it more robust to non-linear "
        "community gradients. "
        "NMDS results are reported with a <b>stress value</b>: "
        "stress &lt; 0.1 is a good representation; "
        "stress &gt; 0.2 means the 2D plot is a poor representation of the data.",
        s["body"],
    ))
    story.append(Spacer(1, 0.15 * cm))
    story.append(info_box(
        "Pipeline note — Phase 7",
        [Paragraph(
            "Phase 7 will add beta diversity calculation and ordination to the pipeline. "
            "It will compute pairwise Bray-Curtis and Jaccard matrices across samples, "
            "run PCoA using scipy/scikit-learn, and embed the ordination plot in "
            "the PDF report. A PERMANOVA test will assess whether sample groups "
            "(e.g. upstream vs downstream) are statistically different.",
            s["box_body"],
        )],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s,
    ))

    # ── 6. REAL-WORLD APPLICATIONS ────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("6.  Real-world Applications in Freshwater eDNA", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Beta diversity and ordination are the tools that make eDNA surveys "
        "scientifically powerful, not just descriptive. "
        "Here are the four main applications in UK freshwater consultancy work:",
        s["body"],
    ))
    story.append(Spacer(1, 0.1 * cm))

    applications = [
        ("Upstream vs downstream comparison",
         "EPS (Habitats Regulations)",
         "Sample upstream and downstream of a point source discharge. "
         "If the communities cluster separately on a PCoA plot, "
         "the discharge is demonstrably altering the biological community. "
         "This is evidence for an Environment Agency enforcement investigation.",
         RED_DARK, RED_LIGHT),
        ("Reference vs impacted sites",
         "Development planning / EIA",
         "Compare a reference site (unaffected) to a proposed development site. "
         "High Bray-Curtis dissimilarity (>0.6) indicates the impacted site "
         "hosts a distinctly different community. "
         "This feeds into the Environmental Impact Assessment baseline.",
         AMBER, AMBER_LIGHT),
        ("Seasonal monitoring",
         "Long-term biodiversity baseline",
         "Sample the same site in spring, summer, and autumn. "
         "PCoA reveals seasonal community succession — normal seasonal "
         "turnover appears as an arc in ordination space. "
         "Unusual outliers may indicate pollution events.",
         TEAL_MID, BLUE_LIGHT),
        ("Restoration effectiveness",
         "NERC Act / S41 reporting",
         "Sample a restored habitat before and after intervention. "
         "If post-restoration samples cluster towards a reference community, "
         "the restoration is working. This is the gold-standard evidence "
         "for Section 41 species recovery reporting.",
         GREEN_DARK, GREEN_LIGHT),
    ]
    for title, legislation, desc, border, bg in applications:
        story.append(info_box(
            title,
            [
                Paragraph(f"<i>Context: {legislation}</i>", s["box_body"]),
                Spacer(1, 0.04 * cm),
                Paragraph(desc, s["box_body"]),
            ],
            bg=bg, border=border, s=s,
        ))
        story.append(Spacer(1, 0.12 * cm))

    story.append(Paragraph("PERMANOVA — statistical testing", s["h2"]))
    story.append(Paragraph(
        "PCoA shows you whether communities look different. "
        "PERMANOVA (Permutational Multivariate Analysis of Variance) "
        "tells you whether that difference is statistically significant. "
        "It tests the null hypothesis that samples from different groups "
        "(e.g. upstream vs downstream) are drawn from the same community distribution. "
        "A significant PERMANOVA result (p &lt; 0.05) means the groups are "
        "genuinely different, not just random variation.",
        s["body"],
    ))

    # ── 7. GLOSSARY ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("7.  Glossary", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2 * cm))

    glossary = [
        ("Alpha diversity",
         "Diversity within a single sample. "
         "Measured by Shannon H', Pielou J', species richness, and Chao1. "
         "Answers: how diverse is this community?"),
        ("Beta diversity",
         "Dissimilarity between samples. "
         "Measured by Bray-Curtis dissimilarity and Jaccard index. "
         "Answers: how different are these two communities?"),
        ("Rarefaction",
         "Random subsampling of sequencing reads to equalise depth across samples. "
         "All samples are subsampled to the minimum depth in the dataset "
         "before diversity comparisons are made."),
        ("Rarefaction curve",
         "A plot of species discovered (y) vs reads sampled (x). "
         "A plateau indicates adequate sequencing depth. "
         "A still-rising curve indicates undersampling."),
        ("Sequencing depth",
         "The number of sequencing reads generated from a sample. "
         "Deeper sequencing finds more species. "
         "Samples must be rarefied before cross-sample diversity comparison."),
        ("Chao1",
         "A richness estimator that predicts the true number of species "
         "including those not observed. "
         "Formula: S_chao1 = S_obs + (F1^2 / 2F2), where F1 = singletons, F2 = doubletons."),
        ("Bray-Curtis dissimilarity",
         "Beta diversity metric ranging from 0 (identical) to 1 (completely different). "
         "Accounts for abundance. The most common metric in environmental ecology."),
        ("Jaccard index",
         "Presence/absence beta diversity metric. "
         "J = shared species / (species in A + species in B - shared). "
         "Use when abundance data is unreliable or irrelevant."),
        ("PCoA (Principal Coordinates Analysis)",
         "An ordination method that reduces a beta diversity matrix to 2D. "
         "Each sample = one dot. Dot distance = ecological dissimilarity. "
         "Axis labels show percentage of variance explained."),
        ("NMDS (Non-metric Multidimensional Scaling)",
         "Alternative ordination method using rank-order distances. "
         "Reported with a stress value — below 0.1 is a good fit, "
         "above 0.2 means the 2D representation is poor."),
        ("PERMANOVA",
         "Permutational Multivariate Analysis of Variance. "
         "Statistical test for whether groups of samples (e.g. upstream vs downstream) "
         "have significantly different community composition. p &lt; 0.05 = significant."),
        ("Singleton",
         "A species observed in exactly one read in a sample. "
         "Singletons are used by Chao1 to estimate undetected diversity. "
         "A high singleton count indicates many rare or low-abundance species."),
    ]
    for term, defn in glossary:
        story.append(Paragraph(term, s["gl_term"]))
        story.append(Paragraph(defn, s["gl_def"]))

    story.append(info_box(
        "Key Takeaways",
        [Paragraph(
            "• Never compare species richness or Shannon H' across samples with "
            "<b>different sequencing depths</b> — always rarefy first.<br/>"
            "• A <b>rarefaction curve plateau</b> means you've sampled enough. "
            "A curve still climbing means you probably missed rare species — "
            "report Chao1 alongside observed richness.<br/>"
            "• <b>Bray-Curtis</b> = abundance-based dissimilarity (0 to 1). "
            "<b>Jaccard</b> = presence/absence dissimilarity. Use both.<br/>"
            "• <b>PCoA</b> translates a distance matrix into a visual plot — "
            "clusters mean similar communities, separation means different ones.<br/>"
            "• <b>PERMANOVA</b> tells you if the visual separation on a PCoA "
            "is statistically real, not random sampling noise.",
            s["box_body"],
        )],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s,
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Next: Module 07 — Cloud API, Scalability &amp; Deployment",
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
