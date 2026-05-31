#!/usr/bin/env python3
"""
Generate Module 04 — Protected Species & UK Environmental Law
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

OUTPUT = Path(__file__).parent / "Module_04_Protected_Species_and_UK_Law.pdf"

# ── Palette ───────────────────────────────────────────────────────────────────
TEAL_DARK    = colors.HexColor("#1B4F72")
TEAL_MID     = colors.HexColor("#2E86C1")
GREEN_DARK   = colors.HexColor("#1E8449")
GREEN_LIGHT  = colors.HexColor("#EAFAF1")
RED_DARK     = colors.HexColor("#922B21")
RED_LIGHT    = colors.HexColor("#FDEDEC")
AMBER        = colors.HexColor("#D4AC0D")
AMBER_LIGHT  = colors.HexColor("#FEF9E7")
PURPLE_DARK  = colors.HexColor("#6C3483")
PURPLE_LIGHT = colors.HexColor("#F5EEF8")
BLUE_LIGHT   = colors.HexColor("#EBF5FB")
GREY_LIGHT   = colors.HexColor("#F2F3F4")
GREY_MID     = colors.HexColor("#BDC3C7")
GREY_DARK    = colors.HexColor("#717D7E")
WHITE        = colors.white
BLACK        = colors.black


# ── Styles ────────────────────────────────────────────────────────────────────
def make_styles():
    s = {}
    def st(n, **k): s[n] = ParagraphStyle(n, **k)

    st("title_main",   fontName="Helvetica-Bold",   fontSize=26, textColor=WHITE,
       leading=32, alignment=TA_CENTER)
    st("title_sub",    fontName="Helvetica",         fontSize=13,
       textColor=colors.HexColor("#AED6F1"), leading=18, alignment=TA_CENTER)
    st("module_label", fontName="Helvetica-Bold",   fontSize=44,
       textColor=colors.HexColor("#AED6F1"), leading=52, alignment=TA_CENTER)
    st("h1",           fontName="Helvetica-Bold",   fontSize=15, textColor=TEAL_DARK,
       leading=20, spaceBefore=14, spaceAfter=4)
    st("h2",           fontName="Helvetica-Bold",   fontSize=12, textColor=TEAL_MID,
       leading=16, spaceBefore=10, spaceAfter=3)
    st("body",         fontName="Helvetica",         fontSize=10, textColor=BLACK,
       leading=16, spaceAfter=5, alignment=TA_JUSTIFY)
    st("bullet",       fontName="Helvetica",         fontSize=10, textColor=BLACK,
       leading=15, leftIndent=14, spaceAfter=4)
    st("box_head",     fontName="Helvetica-Bold",   fontSize=10, textColor=TEAL_DARK,
       leading=14, spaceAfter=3)
    st("box_body",     fontName="Helvetica",         fontSize=10, textColor=BLACK,
       leading=14, alignment=TA_JUSTIFY)
    st("code",         fontName="Courier",           fontSize=9,  textColor=TEAL_DARK,
       leading=13, leftIndent=6, spaceAfter=2)
    st("caption",      fontName="Helvetica-Oblique", fontSize=8.5,
       textColor=GREY_DARK, leading=12, alignment=TA_CENTER)
    st("alert_high",   fontName="Helvetica-Bold",   fontSize=10, textColor=RED_DARK,
       leading=14)
    st("alert_amber",  fontName="Helvetica-Bold",   fontSize=10, textColor=AMBER,
       leading=14)
    st("gl_term",      fontName="Helvetica-Bold",   fontSize=10, textColor=GREEN_DARK,
       leading=13, spaceAfter=1)
    st("gl_def",       fontName="Helvetica",         fontSize=10, textColor=BLACK,
       leading=13, leftIndent=10, spaceAfter=8)
    return s


# ── Helpers ───────────────────────────────────────────────────────────────────
def banner(para, bg, pad_t=12, pad_b=12):
    t = Table([[para]], colWidths=[14*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), bg),
        ("LEFTPADDING",  (0,0),(-1,-1), 26),
        ("RIGHTPADDING", (0,0),(-1,-1), 26),
        ("TOPPADDING",   (0,0),(-1,-1), pad_t),
        ("BOTTOMPADDING",(0,0),(-1,-1), pad_b),
    ]))
    return t


def box(title, paras, bg, border, s):
    inner = ([Paragraph(title, s["box_head"])] if title else []) + paras
    t = Table([[inner]], colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), bg),
        ("BOX",          (0,0),(-1,-1), 1.2, border),
        ("LEFTPADDING",  (0,0),(-1,-1), 11),
        ("RIGHTPADDING", (0,0),(-1,-1), 11),
        ("TOPPADDING",   (0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
    ]))
    return t


def leg_table(rows, s):
    """Legislation overview table."""
    th = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=9.5,
                        textColor=WHITE, leading=13)
    tc = ParagraphStyle("tc", fontName="Helvetica", fontSize=9.5,
                        textColor=BLACK, leading=13)
    tf = ParagraphStyle("tf", fontName="Helvetica-Bold", fontSize=9.5,
                        textColor=TEAL_DARK, leading=13)
    data = []
    for i, row in enumerate(rows):
        if i == 0:
            data.append([Paragraph(c, th) for c in row])
        else:
            data.append([
                Paragraph(row[0], tf),
                Paragraph(row[1], tc),
                Paragraph(row[2], tc),
                Paragraph(row[3], tc),
            ])
    t = Table(data, colWidths=[3.2*cm, 3.0*cm, 3.8*cm, 4.0*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(-1,0),  PURPLE_DARK),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [WHITE, PURPLE_LIGHT]),
        ("BOX",            (0,0),(-1,-1), 0.8, GREY_MID),
        ("INNERGRID",      (0,0),(-1,-1), 0.4, GREY_MID),
        ("LEFTPADDING",    (0,0),(-1,-1), 6),
        ("RIGHTPADDING",   (0,0),(-1,-1), 6),
        ("TOPPADDING",     (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 5),
        ("VALIGN",         (0,0),(-1,-1), "TOP"),
    ]))
    return t


def species_table(rows, s):
    """Protected species reference table."""
    th = ParagraphStyle("sth", fontName="Helvetica-Bold", fontSize=9,
                        textColor=WHITE, leading=12)
    tc = ParagraphStyle("stc", fontName="Helvetica", fontSize=9,
                        textColor=BLACK, leading=12)
    ti = ParagraphStyle("sti", fontName="Helvetica-Oblique", fontSize=9,
                        textColor=BLACK, leading=12)
    th_red  = ParagraphStyle("thr", fontName="Helvetica-Bold", fontSize=9,
                             textColor=RED_DARK, leading=12)
    th_amb  = ParagraphStyle("tha", fontName="Helvetica-Bold", fontSize=9,
                             textColor=AMBER, leading=12)
    data = []
    row_bgs = []
    for i, (sp, common, leg, level) in enumerate(rows):
        if sp == "HEADER":
            data.append([Paragraph(c, th) for c in [common, leg, level, ""]])
            row_bgs.append(("BACKGROUND", (0,i),(-1,i), TEAL_DARK))
        else:
            al_style = th_red if level == "HIGH" else (th_amb if level == "MEDIUM" else tc)
            data.append([
                Paragraph(f"<i>{sp}</i>", tc),
                Paragraph(common, tc),
                Paragraph(leg, tc),
                Paragraph(level, al_style),
            ])
            bg = RED_LIGHT if level == "HIGH" else (AMBER_LIGHT if level == "MEDIUM" else GREY_LIGHT)
            row_bgs.append(("BACKGROUND", (0,i),(-1,i), bg))
    t = Table(data, colWidths=[4.5*cm, 4.0*cm, 3.2*cm, 2.3*cm])
    t.setStyle(TableStyle([
        ("BOX",         (0,0),(-1,-1), 0.8, GREY_MID),
        ("INNERGRID",   (0,0),(-1,-1), 0.4, GREY_MID),
        ("LEFTPADDING", (0,0),(-1,-1), 5),
        ("RIGHTPADDING",(0,0),(-1,-1), 5),
        ("TOPPADDING",  (0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("VALIGN",      (0,0),(-1,-1), "TOP"),
    ] + row_bgs))
    return t


# ── Document ──────────────────────────────────────────────────────────────────
def build(s):
    story = []

    # ── COVER ─────────────────────────────────────────────────────────────────
    story.append(banner(Paragraph("MODULE 04", s["module_label"]),
                        TEAL_DARK, pad_t=28, pad_b=6))
    story.append(banner(
        Paragraph("Protected Species &amp; UK Environmental Law", s["title_main"]),
        TEAL_MID, pad_t=14, pad_b=14))
    story.append(banner(
        Paragraph("eDNA Bioinformatics Learning Series  ·  Yaw Baah", s["title_sub"]),
        GREEN_DARK, pad_t=7, pad_b=7))
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph(
        "Phase 3 of the pipeline adds something no previous phase did: "
        "<b>legal consequence</b>. "
        "When a sequence matches a protected species, the pipeline raises an alert "
        "that can affect planning decisions, development permissions, and field survey "
        "requirements. This module explains the UK legislation behind that alert, "
        "which species are covered, how the detection logic works, and — critically — "
        "what the pipeline can and cannot confirm on its own.",
        s["body"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(box("What you will learn", [Paragraph(
        "1. Why protected species matter — the legal stakes  "
        "&nbsp; 2. The four UK legislation frameworks  "
        "&nbsp; 3. The 20 species in the pipeline and why they were chosen  "
        "&nbsp; 4. CONFIRMED vs POSSIBLE alerts — the detection logic  "
        "&nbsp; 5. The Great Crested Newt — a real eDNA survey case study  "
        "&nbsp; 6. How to read the alert section in the PDF report  "
        "&nbsp; 7. What eDNA can and cannot tell you  "
        "&nbsp; 8. Glossary",
        s["box_body"])],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s))

    # ── 1. WHY IT MATTERS ─────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("1.  Why Protected Species Matter — The Legal Stakes", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Most biodiversity data is scientifically interesting but legally neutral. "
        "Protected species data is different — it has direct legal consequences "
        "for landowners, developers, and the professionals advising them.",
        s["body"]))
    story.append(Spacer(1, 0.15*cm))

    for b in [
        "<b>Planning law:</b> UK planning guidance requires surveys for protected "
        "species before development can proceed on sites where they may be present. "
        "A missed Great Crested Newt detection that surfaces later can halt a "
        "construction project and result in significant legal liability.",
        "<b>Criminal offence:</b> Deliberately disturbing, injuring, or killing a "
        "European Protected Species (EPS) is a criminal offence under the "
        "Conservation of Habitats and Species Regulations 2017. "
        "Penalties include unlimited fines and up to six months imprisonment.",
        "<b>Mitigation licences:</b> Development that cannot avoid impacting an "
        "EPS site requires a licence from Natural England (England), NatureScot "
        "(Scotland), or Natural Resources Wales. Without one, works cannot proceed.",
        "<b>eDNA as evidence:</b> Environment Agency and Natural England have "
        "published guidance accepting eDNA survey results as valid evidence for "
        "protected species presence/absence, provided methodology meets standards.",
    ]:
        story.append(Paragraph(f"&#8226; {b}", s["bullet"]))

    story.append(Spacer(1, 0.2*cm))
    story.append(box(
        "The commercial implication for this pipeline",
        [Paragraph(
            "An ecology consultancy running eDNA surveys needs every result "
            "reviewed by a qualified ecologist before submission to a regulator. "
            "What Phase 3 does is ensure that <b>nothing gets missed</b> — the "
            "alert fires automatically, it is printed in red at the front of the "
            "report, and the disclaimer makes clear that expert review is required. "
            "Automated detection + human review = defensible, traceable process.",
            s["box_body"])],
        bg=AMBER_LIGHT, border=AMBER, s=s))

    # ── 2. THE FOUR LEGISLATION FRAMEWORKS ───────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("2.  The Four UK Legislation Frameworks", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "UK protected species law is spread across four main frameworks. "
        "The pipeline uses a short code for each in the alert output and "
        "in the PDF report.",
        s["body"]))
    story.append(Spacer(1, 0.15*cm))

    story.append(leg_table([
        ["Code", "Full name", "Covers", "Key point"],
        ["EPS",
         "European Protected Species\n(Habitats Regs 2017)",
         "Animals and plants of EU-level conservation concern",
         "Strongest protection. Criminal offence to harm, disturb, or damage habitat."],
        ["WCA",
         "Wildlife and Countryside\nAct 1981",
         "UK-specific animals (Sch. 5) and plants (Sch. 8)",
         "Schedule 5 = protected animals. Schedule 6 = methods of killing restricted."],
        ["S41",
         "Section 41 — NERC\nAct 2006",
         "Species of Principal Importance in England",
         "No criminal penalties but must be considered in planning and land management decisions."],
        ["BAP",
         "UK Biodiversity Action\nPlan Priority Species",
         "Species identified as most threatened / declining",
         "Policy-level protection. Informs conservation priorities and funding."],
    ], s))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "In practice, many species appear under multiple frameworks — "
        "the Great Crested Newt is both EPS and WCA Schedule 5, "
        "giving it the strongest possible protection. "
        "The pipeline's alert level reflects the highest applicable category.",
        s["body"]))

    # ── 3. THE 20 SPECIES ─────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("3.  The 20 Species in the Pipeline", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "These species were chosen because they are <b>detectable by eDNA in "
        "aquatic or riparian environments</b> and have protected status under "
        "UK law. The list is a starting point — a production system should be "
        "reviewed and extended by a qualified ecologist.",
        s["body"]))
    story.append(Spacer(1, 0.15*cm))

    story.append(species_table([
        ("HEADER", "Species", "Legislation", "Alert"),
        ("Triturus cristatus",       "Great Crested Newt",         "EPS / WCA Sch.5", "HIGH"),
        ("Lutra lutra",              "Otter",                      "EPS / WCA Sch.5", "HIGH"),
        ("Austropotamobius pallipes","White-clawed Crayfish",       "EPS / WCA Sch.5", "HIGH"),
        ("Margaritifera margaritifera","Freshwater Pearl Mussel",   "EPS / WCA Sch.5", "HIGH"),
        ("Lampetra planeri",         "Brook Lamprey",               "EPS",             "HIGH"),
        ("Lampetra fluviatilis",     "River Lamprey",               "EPS",             "HIGH"),
        ("Petromyzon marinus",       "Sea Lamprey",                 "EPS",             "HIGH"),
        ("Alosa alosa",              "Allis Shad",                  "EPS",             "HIGH"),
        ("Alosa fallax",             "Twaite Shad",                 "EPS",             "HIGH"),
        ("Luronium natans",          "Floating Water-plantain",     "EPS",             "HIGH"),
        ("Coenagrion mercuriale",    "Southern Damselfly",          "EPS",             "HIGH"),
        ("Vertigo moulinsiana",      "Desmoulin's Whorl Snail",     "EPS",             "HIGH"),
        ("Myotis daubentonii",       "Daubenton's Bat",             "EPS",             "HIGH"),
        ("Coregonus lavaretus",      "Vendace",                     "WCA Sch.5",       "HIGH"),
        ("Hydrophilus piceus",       "Great Silver Water Beetle",   "WCA Sch.5",       "MEDIUM"),
        ("Arvicola amphibius",       "Water Vole",                  "WCA Sch.5",       "HIGH"),
        ("Salmo salar",              "Atlantic Salmon",             "WCA",             "MEDIUM"),
        ("Anguilla anguilla",        "European Eel",                "S41",             "MEDIUM"),
        ("Thymallus thymallus",      "Grayling",                    "S41",             "MEDIUM"),
        ("Neomys fodiens",           "Water Shrew",                 "WCA Sch.6",       "LOW"),
    ], s))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        "RED rows = HIGH alert (EPS or WCA Schedule 5). "
        "AMBER rows = MEDIUM alert (WCA / S41). "
        "These colours match exactly what appears in the PDF report.",
        s["caption"]))

    # ── 4. CONFIRMED vs POSSIBLE ──────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4.  CONFIRMED vs POSSIBLE — The Detection Logic", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "The pipeline assigns one of three flags to every top-hit sequence. "
        "Understanding the difference between CONFIRMED and POSSIBLE is critical "
        "for interpreting what an alert actually means.",
        s["body"]))
    story.append(Spacer(1, 0.2*cm))

    # CONFIRMED box
    story.append(box(
        "CONFIRMED — exact species match",
        [Paragraph(
            "The resolved species name (after LCA) matches a protected species "
            "exactly, and the identity score was ≥ 97% (species-level threshold).<br/><br/>"
            "<b>Example:</b> resolved_species = 'Triturus cristatus', identity = 98.4% "
            "→ CONFIRMED, HIGH alert.<br/><br/>"
            "<b>What this means:</b> The sequence is consistent with the presence of "
            "this species in the sample. This does not legally confirm the species is "
            "present — eDNA can persist in water for days to weeks and may have "
            "travelled from elsewhere. A qualified ecologist must evaluate the result "
            "in context before it can be submitted as evidence.",
            s["box_body"])],
        bg=RED_LIGHT, border=RED_DARK, s=s))
    story.append(Spacer(1, 0.15*cm))

    # POSSIBLE box
    story.append(box(
        "POSSIBLE — genus-level match to a protected genus",
        [Paragraph(
            "The resolved species is at genus level only (e.g. 'Triturus sp.') "
            "because LCA could not confirm a single species, AND that genus contains "
            "at least one protected species.<br/><br/>"
            "<b>Example:</b> resolved_species = 'Triturus sp.' (three hits at 93–91% "
            "disagreeing on species) → POSSIBLE alert.<br/><br/>"
            "<b>What this means:</b> A species within this genus may be present but "
            "cannot be confirmed from this sequence alone. Further targeted survey "
            "(conventional eDNA using species-specific primers, or physical survey) "
            "is recommended before the site can be cleared.",
            s["box_body"])],
        bg=AMBER_LIGHT, border=AMBER, s=s))
    story.append(Spacer(1, 0.15*cm))

    story.append(box(
        "Why the LCA step is especially important here",
        [Paragraph(
            "Without LCA, a sequence with a 98% top hit to Triturus cristatus but "
            "three further hits at 96–94% to non-protected Triturus species would "
            "be reported as a CONFIRMED Great Crested Newt detection. "
            "With LCA applied, the honest answer is 'Triturus sp.' — a POSSIBLE "
            "alert that flags the genus without overclaiming the species. "
            "This is the correct scientific and legal position. "
            "Overclaiming protected species presence has its own legal consequences.",
            s["box_body"])],
        bg=GREEN_LIGHT, border=GREEN_DARK, s=s))

    # ── 5. CASE STUDY: GCN ───────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("5.  Case Study — Great Crested Newt", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "The Great Crested Newt (<i>Triturus cristatus</i>) is the most surveyed "
        "protected species in the UK by eDNA methods. It is the primary commercial "
        "use case that drove Natural England to publish formal eDNA survey guidance "
        "in 2014. Understanding it gives you a concrete anchor for everything "
        "covered in this module.",
        s["body"]))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("Why eDNA works well for GCN:", s["h2"]))
    for b in [
        "Great Crested Newts shed DNA continuously through skin, faeces, and eggs "
        "while in the water (March–June breeding season). Detection rates in "
        "eDNA surveys match or exceed traditional torch surveys.",
        "They are aquatic for only part of the year — eDNA sampling during the "
        "breeding season gives the highest detection probability.",
        "The 12S rRNA and 16S rRNA markers used for vertebrate eDNA work well "
        "for newts. SILVA 138 SSU or NCBI nt are appropriate databases.",
        "A single positive eDNA detection is sufficient evidence of presence "
        "under Natural England's standard methodology guidance.",
    ]:
        story.append(Paragraph(f"&#8226; {b}", s["bullet"]))

    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph("The survey workflow that feeds into this pipeline:", s["h2"]))

    steps = [
        ("1", "Sample collection",
         "Water samples taken from ≥4 points around a pond margin during "
         "March–June. Filter through a membrane to capture DNA. Freeze "
         "immediately to preserve DNA integrity."),
        ("2", "DNA extraction",
         "Laboratory extraction from the filter membrane. "
         "Negative controls (blank filters) run alongside to detect "
         "contamination. DNA quantified by qPCR or fluorometry."),
        ("3", "Amplification",
         "PCR using GCN-specific primers (or universal vertebrate primers). "
         "Results in FASTQ files from Illumina sequencing."),
        ("4", "This pipeline",
         "FASTA → BLAST → LCA → protected species check → PDF report. "
         "If Triturus cristatus is detected at ≥97% identity → CONFIRMED alert "
         "fires in red on the report cover."),
        ("5", "Ecologist review",
         "A qualified ecologist reviews the eDNA result alongside habitat "
         "assessment, survey effort, and seasonal context before submitting "
         "to Natural England as evidence."),
    ]
    for num, title, desc in steps:
        num_style = ParagraphStyle("ns", fontName="Helvetica-Bold", fontSize=11,
                                   textColor=WHITE, leading=14, alignment=TA_CENTER)
        title_style = ParagraphStyle("ts", fontName="Helvetica-Bold", fontSize=10,
                                     textColor=TEAL_DARK, leading=14)
        desc_style = ParagraphStyle("ds", fontName="Helvetica", fontSize=10,
                                    textColor=BLACK, leading=14)
        row = Table([[
            Paragraph(num, num_style),
            [Paragraph(title, title_style), Paragraph(desc, desc_style)],
        ]], colWidths=[1.0*cm, 13.0*cm])
        row.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(0,0), TEAL_MID),
            ("BACKGROUND",   (1,0),(1,0), GREY_LIGHT),
            ("BOX",          (0,0),(-1,-1), 0.8, GREY_MID),
            ("LEFTPADDING",  (0,0),(-1,-1), 8),
            ("RIGHTPADDING", (0,0),(-1,-1), 10),
            ("TOPPADDING",   (0,0),(-1,-1), 6),
            ("BOTTOMPADDING",(0,0),(-1,-1), 6),
            ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ]))
        story.append(row)
        story.append(Spacer(1, 0.1*cm))

    # ── 6. READING THE ALERT SECTION ─────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("6.  Reading the Alert Section in the PDF Report", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "When the pipeline detects a protected species, a dedicated alert section "
        "is inserted between the cover page and the executive summary — the first "
        "content any reader sees after opening the report.",
        s["body"]))
    story.append(Spacer(1, 0.15*cm))

    story.append(Paragraph("The alert section contains:", s["h2"]))
    story.append(Paragraph(
        "<b>Red banner</b> — appears when CONFIRMED detections are present. "
        "Signals immediate attention required.", s["bullet"]))
    story.append(Paragraph(
        "<b>Amber banner</b> — appears when only POSSIBLE detections are present. "
        "Flags for follow-up investigation.", s["bullet"]))
    story.append(Paragraph(
        "<b>Confirmed detections table</b> — species name, common name, "
        "legislation code, alert level, and the query sequence IDs that triggered "
        "the alert. Every row is traceable back to a specific sequence.", s["bullet"]))
    story.append(Paragraph(
        "<b>Possible detections box</b> — genus name, which protected species "
        "belong to that genus, and which query IDs matched at genus level.", s["bullet"]))
    story.append(Paragraph(
        "<b>Disclaimer</b> — bold text stating that detections require review "
        "by a qualified ecologist before regulatory submission. This protects "
        "both the analyst and the client.", s["bullet"]))
    story.append(Spacer(1, 0.2*cm))

    story.append(box(
        "In the pipeline code — src/protected.py",
        [Paragraph(
            "check_protected(df) adds protected_flag and protection_info columns "
            "to the hit table after LCA resolution.<br/>"
            "get_alerts(df) aggregates these into the structured dict that "
            "generate_report() uses to render the alert section.<br/>"
            "pipeline.py logs a WARNING to the terminal for every CONFIRMED "
            "detection so alerts are visible even without opening the PDF.",
            s["box_body"])],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s))

    # ── 7. WHAT eDNA CANNOT TELL YOU ─────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("7.  What eDNA Can and Cannot Tell You", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Understanding the limitations of eDNA is as important as understanding "
        "its capabilities. Misrepresenting what a positive detection means — in "
        "either direction — has real consequences.",
        s["body"]))
    story.append(Spacer(1, 0.15*cm))

    th2 = ParagraphStyle("th2", fontName="Helvetica-Bold", fontSize=9.5,
                         textColor=WHITE, leading=13)
    tc2 = ParagraphStyle("tc2", fontName="Helvetica", fontSize=9.5,
                         textColor=BLACK, leading=13)
    can_data = [
        [Paragraph("eDNA CAN tell you", th2),
         Paragraph("eDNA CANNOT tell you", th2)],
        [Paragraph("A species' DNA was present in the water sample", tc2),
         Paragraph("The species was physically present at the exact sample point", tc2)],
        [Paragraph("Whether to investigate further for a given species", tc2),
         Paragraph("How many individuals are present (population size)", tc2)],
        [Paragraph("Absence is likely if multiple samples are negative (high sensitivity)", tc2),
         Paragraph("Absence is certain — low DNA concentrations can cause false negatives", tc2)],
        [Paragraph("Which species assemblage was present over days to weeks", tc2),
         Paragraph("The species was present on the day of sampling specifically", tc2)],
        [Paragraph("A reproducible, auditable result tied to a specific database version", tc2),
         Paragraph("The health, age, or condition of individuals", tc2)],
    ]
    can_t = Table(can_data, colWidths=[7.0*cm, 7.0*cm])
    can_t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(0,0), GREEN_DARK),
        ("BACKGROUND",     (1,0),(1,0), RED_DARK),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [WHITE, GREY_LIGHT]),
        ("BOX",            (0,0),(-1,-1), 0.8, GREY_MID),
        ("INNERGRID",      (0,0),(-1,-1), 0.4, GREY_MID),
        ("LEFTPADDING",    (0,0),(-1,-1), 7),
        ("RIGHTPADDING",   (0,0),(-1,-1), 7),
        ("TOPPADDING",     (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 5),
        ("VALIGN",         (0,0),(-1,-1), "TOP"),
    ]))
    story.append(can_t)
    story.append(Spacer(1, 0.2*cm))
    story.append(box(
        "The correct interpretation of a CONFIRMED detection",
        [Paragraph(
            "A CONFIRMED detection means: <i>the sequence data is consistent "
            "with the presence of this species in or near this water body during "
            "the sampling period.</i> "
            "It does not mean the species is definitely there. "
            "It does mean the site cannot be cleared without further investigation. "
            "That is the legally and scientifically defensible position.",
            s["box_body"])],
        bg=GREEN_LIGHT, border=GREEN_DARK, s=s))

    # ── 8. GLOSSARY ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("8.  Glossary", s["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL_DARK))
    story.append(Spacer(1, 0.2*cm))

    glossary = [
        ("EPS", "European Protected Species. Species protected under the Conservation "
         "of Habitats and Species Regulations 2017 (Habitats Directive transposition). "
         "Highest level of legal protection in UK law."),
        ("WCA Schedule 5", "Schedule 5 of the Wildlife and Countryside Act 1981. "
         "Lists animals it is illegal to intentionally kill, injure, or take."),
        ("Section 41", "Section 41 of the Natural Environment and Rural Communities "
         "(NERC) Act 2006. Lists Species of Principal Importance for biodiversity "
         "conservation in England. Considered in planning decisions."),
        ("Natural England", "UK government body responsible for protecting and "
         "improving England's natural environment. Issues EPS mitigation licences "
         "and publishes eDNA survey guidance."),
        ("Habitat Regulations Assessment",
         "A legal process required when a development may affect a European "
         "Protected Site. Often triggered by EPS detections."),
        ("CONFIRMED alert", "The pipeline's term for a direct species-level match "
         "(≥97% identity) between a sequence and a protected species in the "
         "reference list. Requires ecologist review before regulatory submission."),
        ("POSSIBLE alert", "A genus-level match where the genus contains at least "
         "one protected species but species identity could not be confirmed. "
         "Triggers follow-up survey recommendation."),
        ("Mitigation licence", "A licence from Natural England permitting works "
         "that would otherwise breach EPS protection, subject to conditions "
         "including species surveys, mitigation measures, and monitoring."),
        ("12S / 16S rRNA", "Ribosomal RNA marker genes commonly used for vertebrate "
         "and bacterial eDNA detection respectively. The 12S marker is standard "
         "for Great Crested Newt eDNA surveys."),
        ("False negative", "When a species is present but eDNA is not detected. "
         "Can occur due to low DNA concentration, degradation, or sampling outside "
         "the optimal season. Multiple samples reduce this risk."),
    ]
    for term, defn in glossary:
        story.append(Paragraph(term, s["gl_term"]))
        story.append(Paragraph(defn, s["gl_def"]))

    story.append(box("Key Takeaways", [Paragraph(
        "&#8226; Protected species detection is the feature that gives this pipeline "
        "commercial and legal relevance.<br/>"
        "&#8226; EPS species carry the strongest protection — criminal law applies.<br/>"
        "&#8226; CONFIRMED = species-level match at ≥97%. POSSIBLE = genus-level only.<br/>"
        "&#8226; LCA prevents overclaiming — it is scientifically and legally safer "
        "to say Triturus sp. than to incorrectly confirm T. cristatus.<br/>"
        "&#8226; eDNA confirms DNA presence, not species presence. Ecologist review "
        "is mandatory before regulatory submission.<br/>"
        "&#8226; The species list in src/protected.py must be reviewed by a qualified "
        "ecologist before using this pipeline for a real survey.",
        s["box_body"])],
        bg=BLUE_LIGHT, border=TEAL_MID, s=s))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Next: Module 05 — Curated Databases &amp; Multi-marker Surveys",
        s["caption"]))

    return story


def main():
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2.2*cm,  bottomMargin=2.2*cm,
    )
    doc.build(build(make_styles()))
    print(f"PDF saved: {OUTPUT.resolve()}")


if __name__ == "__main__":
    main()
