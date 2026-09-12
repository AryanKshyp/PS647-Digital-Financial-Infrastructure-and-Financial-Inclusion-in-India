#!/usr/bin/env python3
"""
Insert the digital-literacy-and-income chapter into the group report as Chapter 5,
Hypothesis 3.

Writes a NEW file; the original .docx is never modified in place.

Scope, deliberately narrow:
  - §1.4      fill the Hypothesis 3 statement box (currently a placeholder)
  - Table 2.2 append the new source rows
  - §2.7      append the data limitations that belong to the new series
  - §2.8      replace the "To be completed" note with the real sentence
  - Chapter 5 fill §5.1-5.5, currently all placeholders
  - Appendix A append the decision log for the new decisions

Nothing belonging to Hypothesis 1 (Chapter 3) is touched. Every insertion either fills a
placeholder the template left open or appends to the end of an existing table.
"""
import copy
import sys
from pathlib import Path

import docx
from docx.shared import Inches, Pt
from docx.oxml.ns import qn

ROOT_DIR = Path(__file__).resolve().parent.parent
SHARED = ROOT_DIR.parent
OUT = ROOT_DIR / "output"
SRC = SHARED.parent / "Digital_Financial_Infrastructure_Report.docx"
DST = SHARED.parent / "Digital_Financial_Infrastructure_Report_with_Chapter5.docx"

TEMPLATE_TABLE = 3          # Table 2.2 -- borrowed for tblPr on every new table
CAPTION_PT = 10


# ----------------------------------------------------------------- low-level helpers
# Every insert helper accepts a Paragraph, a Table, or a raw XML element as its anchor, and
# returns the object it created. Chaining the return value is what keeps paragraphs from being
# inserted *before* a table that was just placed after the same anchor.
_PARENT = [None]


def _el(ref):
    if hasattr(ref, "_p"):
        return ref._p
    if hasattr(ref, "_tbl"):
        return ref._tbl
    return ref


def para_after(ref, text="", style="normal", italic=False, bold_prefix=None, size=None):
    """Insert a paragraph immediately after `ref` (paragraph, table or element)."""
    anchor = _el(ref)
    new = copy.deepcopy(_PARENT[1] if len(_PARENT) > 1 else None)
    if new is None:
        new = anchor.makeelement(qn("w:p"), {})
    else:
        for child in list(new):
            if child.tag != qn("w:pPr"):
                new.remove(child)
    anchor.addnext(new)
    p = docx.text.paragraph.Paragraph(new, _PARENT[0])
    try:
        p.style = style
    except KeyError:
        pass
    if bold_prefix:
        r = p.add_run(bold_prefix)
        r.bold = True
        if size:
            r.font.size = Pt(size)
    if text:
        r = p.add_run(text)
        r.italic = italic
        if size:
            r.font.size = Pt(size)
    return p


def heading3_after(ref, text):
    p = para_after(ref, text, style="Heading 3")
    return p


def clear_paragraph(p):
    for r in list(p.runs):
        r._element.getparent().remove(r._element)


def table_after(ref, doc, data, header=True, widths=None):
    """Build a table matching the document's existing table formatting, placed after `ref`."""
    tmpl = doc.tables[TEMPLATE_TABLE]
    rows, cols = len(data), len(data[0])
    tbl = doc.add_table(rows=rows, cols=cols)
    # adopt the template's table properties (style, borders, width, look)
    new_pr = copy.deepcopy(tmpl._tbl.tblPr)
    tbl._tbl.replace(tbl._tbl.tblPr, new_pr)
    for ri, row in enumerate(data):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            if header and ri == 0:
                run.bold = True
            run.font.size = Pt(9)
            if widths:
                cell.width = Inches(widths[ci])
        if header and ri == 0:
            for ci in range(cols):
                tcPr = tbl.cell(0, ci)._tc.get_or_add_tcPr()
                shd = tcPr.makeelement(qn("w:shd"), {qn("w:val"): "clear", qn("w:fill"): "e7e6e6"})
                tcPr.append(shd)
    _el(ref).addnext(tbl._tbl)
    return tbl


def figure_after(ref, doc, img, caption, width=6.2):
    """Insert an image paragraph plus an italic caption, matching the Chapter 3 pattern."""
    pic_p = para_after(ref)
    pic_p.add_run().add_picture(str(img), width=Inches(width))
    cap = para_after(pic_p, caption, italic=True, size=CAPTION_PT)
    return cap


def boxed(ref, doc, title, body_lines):
    """A one-cell shaded box, the form the report uses for hypotheses and decision rules."""
    tbl = table_after(ref, doc, [[""]], header=False)
    cell = tbl.cell(0, 0)
    cell.text = ""
    p0 = cell.paragraphs[0]
    r = p0.add_run(title)
    r.bold = True
    for line in body_lines:
        p = cell.add_paragraph()
        p.add_run(line)
    return tbl


def find_para(doc, needle, start=0):
    for i in range(start, len(doc.paragraphs)):
        if needle in doc.paragraphs[i].text:
            return doc.paragraphs[i]
    sys.exit(f"FATAL: anchor not found: {needle!r}")


def chapter_start(doc, heading):
    """Index of a chapter heading. Chapters 4 and 5 carry IDENTICAL placeholder text, so every
    Chapter 5 lookup must start below this line or it silently rewrites Chapter 4 instead."""
    for i, q in enumerate(doc.paragraphs):
        if q.style.name == "Heading 1" and q.text.strip() == heading:
            return i
    sys.exit(f"FATAL: chapter heading not found: {heading!r}")


def find_in_ch5(doc, needle):
    return find_para(doc, needle, start=chapter_start(doc, "Chapter 5"))


def fill_box(tbl, row, title, statement):
    cell = tbl.rows[row].cells[0]
    for p in cell.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    clear_paragraph(cell.paragraphs[0])
    r = cell.paragraphs[0].add_run(title)
    r.bold = True
    p = cell.add_paragraph()
    p.add_run(statement)


# ----------------------------------------------------------------- content
HYP3 = ("The positive effect of digital financial infrastructure on financial inclusion is "
        "stronger in states with higher levels of digital literacy, and stronger in states with "
        "higher incomes. Digital literacy and income act as complements to infrastructure rather "
        "than as substitutes for it.")

RQ3 = ("Research question. Do digital literacy and income moderate the relationship between "
       "digital financial infrastructure and financial inclusion in India?")

FIGS = OUT


def main() -> int:
    if not SRC.exists():
        sys.exit(f"FATAL: source report not found at {SRC}")
    doc = docx.Document(str(SRC))
    _PARENT[0] = doc
    # a clean "normal" paragraph to clone, so inserted paragraphs inherit body formatting
    tmpl = next(q for q in doc.paragraphs if q.style.name == "normal" and q.text.strip())
    blank = copy.deepcopy(tmpl._p)
    for child in list(blank):
        if child.tag != qn("w:pPr"):
            blank.remove(child)
    _PARENT.append(blank)
    print(f"  opened {SRC.name}")

    # ---------------------------------------------------------------- §1.4
    box14 = doc.tables[1]
    fill_box(box14, 1, "Hypothesis 3 (Chapter 5)", HYP3)
    # The statement boxes sit BELOW this note in the template, so the note is replaced in place
    # and the rationale goes after the boxes -- otherwise Hypothesis 3 is explained before it is
    # stated.
    p = find_para(doc, "To be completed: State Hypotheses 2 and 3 in the same format")
    clear_paragraph(p)
    p.add_run("To be completed: State Hypothesis 2 in the same format and develop it in "
              "Chapter 4.")
    p = para_after(box14,
                   "Rationale. Opening an account asks nothing of the holder beyond identity "
              "documents; a bank can be given a target and audited against it. Using an account "
              "asks the holder to operate the channel through which it is used. Infrastructure "
              "therefore relaxes the access constraint wherever it is built, but relaxes the "
              "usage constraint only where the ability to use it already exists. Income is "
              "the rival explanation and is tested alongside, because the two are correlated and "
              "either can be mistaken for the other.")
    para_after(p, "Expected: a positive interaction between infrastructure and each of the two "
                  "moderators. If either is genuinely a complement to infrastructure rather than "
                  "a marker of general development, the interaction should be larger on usage "
                  "outcomes than on access outcomes, and the difference should be "
                  "distinguishable from zero.")
    print("  §1.4 filled")

    # ---------------------------------------------------------------- Table 2.2
    t22 = doc.tables[TEMPLATE_TABLE]
    new_rows = [
        ("Digital literacy", "NFHS-5 (2019-21), IIPS",
         "State fact sheets, indicators 18 and 19: women and men who have ever used the internet",
         "Moderator"),
        ("Mobile-phone ownership", "NFHS-4 (2015-16), IIPS",
         "State fact sheets, indicator 123, women owning a mobile phone they themselves use",
         "Moderator, pre-window"),
        ("ICT skills", "NSS 75th round (2017-18), MoSPI",
         "Tables 13 and 14, persons aged 5+ able to operate a computer or use the internet; "
         "22 major states", "Moderator, robustness"),
        ("Household consumption", "HCES 2022-23, MoSPI",
         "Fact Sheet, Statement 8, average MPCE by State/UT, rural and urban",
         "Moderator, robustness"),
        ("Education and inclusion baselines", "NFHS-5 and NFHS-4, IIPS",
         "Indicators 1, 16 and 17 (schooling); indicator 122 (women's own bank account)",
         "Placebo controls"),
        ("General literacy", "Census of India 2011", "State literacy rate", "Placebo control"),
    ]
    for r in new_rows:
        row = t22.add_row()
        for ci, val in enumerate(r):
            cell = row.cells[ci]
            cell.text = ""
            run = cell.paragraphs[0].add_run(val)
            run.font.size = Pt(9)
    print(f"  Table 2.2: {len(new_rows)} rows appended (now {len(t22.rows) - 1} series)")

    # ---------------------------------------------------------------- §2.7
    anchor = find_para(doc, "Universe and basis of the credit-account series (D8)")
    blocks = [
        ("Coverage of the pre-window ICT measure (D20). ",
         "The published NSS 75th round state tables cover 22 major states only; every "
         "north-eastern state and small union territory is absent. Using that series as the "
         "primary moderator would have dropped 11 of 33 states and removed most of the upper "
         "tail of the digital-literacy distribution, so it is reported as a robustness measure "
         "at n = 22 and the primary moderator is taken from NFHS-5, which covers all 33. Where "
         "both exist they correlate 0.87 on computer ability and 0.90 on internet ability, so "
         "the substitution is between two measurements of the same quantity rather than between "
         "two quantities."),
        ("The survey values were verified, not assumed. ",
         "The NFHS-5 figures were taken from a compiled mirror whose author flags it as not "
         "extensively cross-checked, and were tested against eight independently published fact "
         "sheet figures before use; all eight matched exactly. The check runs on every build and "
         "aborts on any mismatch."),
        ("Urbanisation is derived, not published. ",
         "No verifiable machine-readable Census 2011 state urbanisation table was obtained, so "
         "the urban share used as a placebo control is derived from the NFHS-5 urban, rural and "
         "total decomposition. It tracks Census 2011 closely where both are known (Delhi 98.2 "
         "against 97.5, Kerala 48.6 against 47.7, Maharashtra 46.7 against 45.2) but it is a "
         "survey-sample quantity and is labelled as such. It is never used as a headline "
         "variable. Census 2011 literacy, used in the same role, conflates Andhra Pradesh and "
         "Telangana, which did not exist separately in 2011."),
        ("Two income measures, and they are not interchangeable (D25). ",
         "Per-capita NSDP is a production measure: output books to the state where a firm is "
         "registered, the same attribution problem recorded above for deposits held at branch "
         "location. MPCE from HCES 2022-23 is household consumption collected from households. "
         "The two correlate 0.844, and Chapter 5 shows that the choice between them changes the "
         "result, so both are reported. MPCE is published separately for rural and urban areas "
         "and the two are combined at each state's derived urban share."),
    ]
    ref = anchor
    for bold, body in blocks:
        ref = para_after(ref, body, bold_prefix=bold)
    print(f"  §2.7: {len(blocks)} paragraphs appended")

    # ---------------------------------------------------------------- §2.8
    p = find_para(doc, "To be completed: If Hypotheses 2 and 3 use series beyond the eight above")
    clear_paragraph(p)
    p.add_run("Chapter 5 uses the same nine series and adds six state-level cross-sections that "
              "carry no time dimension: digital literacy and general education from NFHS-5, their "
              "2015-16 counterparts from NFHS-4, ICT skills from the NSS 75th round, household "
              "consumption from HCES 2022-23, and Census 2011 literacy. None enters as a "
              "time-varying regressor. Each is one number per state, interacted with the digital "
              "payment measure already described in Section 2.6, and each is harmonised onto the "
              "same 33 units by the rules in Section 2.4.")
    print("  §2.8 filled")

    # ---------------------------------------------------------------- Chapter 5 title
    TITLE = "Hypothesis 3: Digital Literacy and Income as Complements"
    hits = 0
    for para in doc.paragraphs:
        if "Hypothesis 3: [Title to be supplied]" not in para.text:
            continue
        # The contents entry is prefixed with the chapter number ("5  Hypothesis 3: ..."),
        # so replace the placeholder substring rather than the whole paragraph.
        prefix = para.text.split("Hypothesis 3: [Title to be supplied]")[0]
        clear_paragraph(para)
        para.add_run(prefix + TITLE)
        hits += 1
    print(f"  Chapter 5 title set in {hits} places (heading and contents)")

    build_chapter5(doc)
    build_appendix(doc)

    doc.save(str(DST))
    print(f"\n  wrote {DST}")
    print(f"  paragraphs {len(doc.paragraphs)}, tables {len(doc.tables)}, "
          f"images {len(doc.inline_shapes)}")
    return 0


# ----------------------------------------------------------------- Chapter 5 body
def build_chapter5(doc):
    # ============================================================ 5.1
    box = next(t for t in doc.tables
               if len(t.rows) == 1 and t.rows[0].cells[0].text.strip().startswith("Hypothesis 3"))
    fill_box(box, 0, "Hypothesis 3", HYP3)
    p = find_in_ch5(doc, "Rationale. [The mechanism, not the expectation.]")
    clear_paragraph(p)
    p.add_run("Rationale. Chapter 3 established that UPI adoption raises credit accounts per "
              "adult more than it raises the rupees moving through them, and that the gap is "
              "significant. That is an average across 33 states, and the average conceals a "
              "question policy needs answered: the same national rollout reaches every state, so "
              "does it convert into inclusion at the same rate everywhere? The digital-divide "
              "literature says it should not. Opening an account asks nothing of the holder "
              "beyond identity documents, and banks can be pushed to open them. Using an account "
              "asks the holder to operate the channel. Infrastructure therefore relaxes the "
              "access constraint wherever it is built, and the usage constraint only where the "
              "ability to use it already exists. Digital literacy is therefore a candidate "
              "complement to infrastructure rather than a substitute for it.")
    p = para_after(p, RQ3)
    p = para_after(p, "Two complements are candidates, and they are each "
                      "other's principal confounder: digitally literate states are also richer "
                      "states. Estimated separately, a skills result can be income wearing a "
                      "costume and an income result can be skills wearing one. Entering both in "
                      "the same equation is not a convenience but the identification strategy, "
                      "and the comparison between them is the contribution.")
    p = para_after(p, "Expected: a positive interaction between infrastructure and each "
                      "moderator, and a larger interaction on usage outcomes than on access "
                      "outcomes. Opening an account is the margin least likely to reward a "
                      "complement, since it asks least of the account holder, so a moderator "
                      "that raises both margins equally is behaving like a development proxy "
                      "rather than like a complement. The two moderators enter together "
                      "throughout, each as the rival explanation for the other.")
    p = boxed(p, doc, "Decision rule, fixed before any result was seen (D18-D28)",
              ["Support requires the moderation to be specific to usage. A moderator that "
               "conditions access and usage alike is a general development gradient, not a "
               "complement to it, and is reported as such whatever its own p-value.",
               "The placebo test outranks the main estimates. If general education or "
               "urbanisation reproduce the digital-literacy interaction at similar magnitude and "
               "significance, the interaction is not separately identified and is reported as "
               "not identified.",
               "Where two measures of the same construct disagree, the one with the better "
               "construct validity governs, named in advance rather than chosen afterwards."])
    p = find_in_ch5(doc, "Expected: [The sign pattern that would constitute support.]")
    clear_paragraph(p)
    p.add_run("Three features of that rule matter below. It is directional in a way that can "
              "fail: a moderator that raises both margins equally counts against the hypothesis "
              "rather than for it. It subordinates the headline estimates to a falsification "
              "test, which is run first and reported whether or not it is favourable. And it "
              "fixes in advance which of two income measures governs if they disagree, which "
              "they do.")
    p = find_in_ch5(doc, "To be completed: Fix the decision rule before estimating, as D10 does")
    clear_paragraph(p)
    p.add_run("One further pre-commitment, recorded because the temptation to breach it arose "
              "later: the specification reported as the headline is the one fixed before the "
              "data were assembled. Section 5.4.5 finds a larger and equally significant "
              "estimate on a subset of the outcomes. It is reported as a decomposition of the "
              "headline, not promoted to replace it, for the same reason Section 3.6.2 refuses "
              "to present the digital result of Chapter 3 as a tested hypothesis.")

    # ============================================================ 5.2
    p = find_in_ch5(doc, "To be completed: Define the independent, dependent and control variables")
    clear_paragraph(p)
    p.add_run("The panel, the infrastructure measure and the outcomes are those of Chapter 3, "
              "Track 3, unchanged: 33 states over FY2019-FY2023, N = 165, with UPI measured as "
              "PhonePe registered users per adult. Every column carried across was asserted "
              "identical to the file behind Chapter 3, and the baseline specification here "
              "reproduces Table 3.7's coefficients to five decimal places. That is a check on "
              "the merge, not a result. What is new is the moderators and the way the outcomes "
              "are compared.")
    p = para_after(p, "Access is measured credit-only, following the rule fixed in Section 3.5.2: "
                      "deposit accounts are definitionally entangled with UPI registration, and "
                      "Section 5.4.5 shows that entanglement is not a hypothetical concern here.")
    p = heading3_after(p, "5.2.1  The moderators")
    p = para_after(p, "Digital literacy is the percentage of women in a state who have ever used "
                      "the internet, from NFHS-5 (2019-21). It is preferred to the NSS ICT "
                      "battery on coverage grounds alone (Section 2.7); the two correlate 0.87 "
                      "to 0.90 where both exist, which is reassurance that the substitution is "
                      "between measurements rather than between constructs. Resources are "
                      "measured two ways, per-capita NSDP and household consumption, for the "
                      "reason given in Section 2.7, and the disagreement between them turns out "
                      "to matter.")
    p = para_after(p, "Both moderators are one number per state and are standardised across the "
                      "33 states, so each coefficient reads as the change in the infrastructure "
                      "effect per standard deviation of the moderator. Making the income "
                      "moderator time-invariant is deliberate: the skills measure comes from a "
                      "single survey wave and cannot vary over time, and allowing income to vary "
                      "while skills could not would decide the comparison by that asymmetry "
                      "rather than by the data. Time-varying per-capita income remains in the "
                      "equation as a control, exactly as in Chapter 3.")
    p = heading3_after(p, "5.2.2  Specification")
    p = para_after(p, "The simple form interacts infrastructure with each moderator in turn and "
                      "then with both together, on each outcome separately:")
    p = para_after(p, "Y_it = α_i + λ_t + β₁ UPI_it + β₃ (UPI_it × DigLit_i) + β₄ (UPI_it × "
                      "Income_i) + γ′X_it + ε_it      (5.1)")
    p = para_after(p, "where X carries branches, ATMs and log per-capita income, and infrastructure "
                      "is mean-centred so that β₁ reads as the effect at average conversion "
                      "levels of both moderators rather than at an out-of-support zero. Standard errors are "
                      "clustered by state, as in Chapter 3.")
    p = para_after(p, "Equation (5.1) cannot answer the hypothesis, because it asks only whether "
                      "the effect is larger. The hypothesis is about which margin the effect "
                      "appears on, and that requires the outcomes in one equation. Each outcome "
                      "is standardised within itself and the three are stacked, giving 495 rows:")
    p = para_after(p, "Y_itk = β₁ UPI_it + β₂ (UPI_it × Intensive_k) + β₃ (UPI_it × DigLit_i) + "
                      "β₅ (UPI_it × DigLit_i × Intensive_k) + β₄ (UPI_it × Income_i) + "
                      "β₆ (UPI_it × Income_i × Intensive_k) + γ′X_it + μ_ik + λ_tk + ε_itk   (5.2)")
    p = para_after(p, "Intensive_k is zero for credit accounts per adult and one for the two "
                      "rupee outcomes. β₅ is the coefficient the hypothesis is about: it asks "
                      "whether digital literacy moves the effect between margins rather than "
                      "simply scaling it. β₆ asks the same of income. Because β₅ is a difference "
                      "between outcomes measured on the same state in the same year, any "
                      "confounder acting equally on both margins differences out of it; that is "
                      "the sense in which equation (5.2) is a sharper test than (5.1) rather "
                      "than merely a more complicated one.")
    p = para_after(p, "β₂ is Hypothesis 1's test, estimated here on the same stacked data. The "
                      "two hypotheses are adjacent coefficients in one equation rather than two "
                      "separate studies, and Section 5.4.3 reports them together.")
    p = para_after(p, "Two further points on the fixed effects. Every outcome carries its own "
                      "state effect and its own year effect, μ_ik and λ_tk, rather than sharing "
                      "one set across outcomes. That is a more demanding specification and it is "
                      "not a matter of taste: the restricted form is nested inside it and is "
                      "rejected, F(72, 375) = 89.2, p below 10⁻¹⁵, so the restricted form is "
                      "misspecified. With 33 clusters and 72 restrictions no cluster-robust "
                      "version of that test exists, so it is the classical F-test and it "
                      "licenses the fixed-effect structure, not the standard errors.")
    p = para_after(p, "Those standard errors carry their own qualification. Section 3.2.3 notes "
                      "that 33 clusters sit at the lower end of the range where cluster-robust "
                      "inference is reliable. Here the difficulty is sharper, because each "
                      "moderator is a single number per state, which is the case the asymptotics "
                      "handle worst. Every p-value reported in this chapter is therefore a wild "
                      "cluster bootstrap with the null imposed, 9,999 replications, rather than "
                      "a cluster-robust t-test.")

    # ============================================================ 5.3
    p = find_in_ch5(doc, "To be completed: Means, standard deviations and ranges")
    clear_paragraph(p)
    p.add_run("The diagnostic that governs Chapter 3 is run again here, and this time it passes. "
              "The question is whether the interaction terms have anything for the fixed effects "
              "to work with, and whether each moderator can be told apart from the "
              "infrastructure measure it modifies.")
    p = para_after(p, "Table 5.1: Diagnostics, against thresholds fixed before the moderator data "
                      "were assembled", italic=True, size=CAPTION_PT)
    t = table_after(p, doc, [
        ["", "Correlation with UPI adoption", "Within-state share of variation", "Verdict"],
        ["Digital literacy × UPI", "0.243", "65.9%", "PASS"],
        ["Income × UPI", "0.687", "70.8%", "PASS"],
        ["UPI users per adult (reference)", "n/a", "67.1%", "PASS"],
        ["Branches per lakh adults (reference)", "n/a", "6.5%", "FAIL"],
    ], widths=[2.3, 1.6, 1.5, 0.9])
    p = para_after(t,
                   "Digital literacy is very nearly orthogonal to UPI adoption, at 0.243, so the "
                   "collinearity that would have made the interaction unreadable is absent. "
                   "Income is closer at 0.687 but still inside the threshold fixed in advance. "
                   "Variance inflation factors on the two interaction terms are 2.2 and 2.6. The "
                   "last two rows are the contrast with Chapter 3: the physical regressors that "
                   "failed the gate there still fail it, and the terms this chapter relies on do "
                   "not.")
    p = para_after(p, "The two moderators must also be separable from each other, or the "
                      "comparison between them is undefined. They correlate 0.682 and disagree "
                      "by up to 23 rank positions out of 33: Telangana is 28th on digital "
                      "literacy and 5th on income, Manipur 15th and 30th. Seventeen of the 33 "
                      "states sit off the diagonal of the two tercile rankings, and those states "
                      "are what identifies the comparison.")
    p = figure_after(p, doc, FIGS / "report_fig5_1.png",
                     "Figure 5.1: Left: the two endowments across the 33 states, with the states "
                     "furthest from the fitted line labelled. They are correlated but far from "
                     "identical. Right: the two tercile rankings cross-tabulated. The 17 states "
                     "off the diagonal are what separates a skills explanation from an income "
                     "one; the corners are sparse, and claims about them are correspondingly "
                     "weak.")
    p = para_after(p, "One feature of the outcomes bears directly on the specification and is "
                      "reported before any estimate. Section 3.7 records that Usage is severely "
                      "right-skewed after the pooled normalisation. That compression is "
                      "inherited here and it is not uniform: 46.7 per cent of the credit-account "
                      "observations sit below 0.20, against 83.0 per cent for deposits per "
                      "capita and 86.1 per cent for credit per capita, with skew of 1.10 against "
                      "2.50 and 3.13. The two margins were therefore never being compared on "
                      "equivalent scales. Standardising each outcome within itself before "
                      "stacking, as equation (5.2) does, removes that problem; it is a repair of "
                      "a limitation Chapter 3 had to leave open rather than a convenience.")

    # ============================================================ 5.4
    p = find_in_ch5(doc, "To be completed: Main estimates, reported before they are interpreted")
    clear_paragraph(p)
    p.add_run("Results are reported in the order they were produced: the simple model first, "
              "then the test that separates the two hypotheses, then the falsification tests "
              "that decide whether either can be believed.")
    p = heading3_after(p, "5.4.1  The simple interaction model, and why it misleads")
    p = para_after(p, "Equation (5.1), both moderators entered together, with income measured "
                      "both ways. Bootstrap p-values throughout.")
    p = para_after(p, "Table 5.2: Interaction estimates from equation (5.1). Two-way fixed "
                      "effects, N = 165, wild cluster bootstrap p-values in parentheses",
                   italic=True, size=CAPTION_PT)
    p = table_after(p, doc, [
        ["Outcome", "UPI", "× digital literacy", "× income (NSDP)", "× income (MPCE)"],
        ["Credit accounts per adult", "+0.374 (0.017)", "−0.061 (0.104)", "+0.035 (0.391)",
         "+0.019 (0.625)"],
        ["Deposits ₹ per capita", "+0.132 (0.003)", "+0.056 (0.061)", "+0.045 (0.013)",
         "+0.056 (0.423)"],
        ["Credit ₹ per capita", "+0.044 (0.186)", "−0.029 (0.044)", "+0.053 (0.0002)",
         "+0.000 (0.998)"],
    ], widths=[1.7, 1.2, 1.3, 1.2, 1.2])
    p = para_after(p, "Read on the NSDP column alone, this table says resources moderate and "
                      "skills do not, which is the classical result that prices move demand for "
                      "financial services further than knowledge does. Two things undercut that "
                      "reading, and both are visible in the table itself.")
    p = para_after(p, "First, the skills interaction fails its own falsification test exactly "
                      "where it looks strongest. On deposits per capita, substituting urban "
                      "share for digital literacy produces a larger interaction, +0.065 against "
                      "+0.056. Under the rule fixed in Section 5.1, digital literacy is "
                      "therefore not separately identified on that outcome, whatever its own "
                      "p-value.")
    p = para_after(p, "Second, and more damaging, the income result does not survive the change "
                      "of measure.")
    p = heading3_after(p, "5.4.2  Which income is being measured")
    p = para_after(p, "Per-capita NSDP is a production measure: output books to the state where "
                      "a firm is registered. That is the same attribution problem Section 2.7 "
                      "records for deposits held at branch location, and it inflates the same "
                      "states. MPCE is household consumption, collected from households. For a "
                      "moderator standing in for household resources, MPCE is the better "
                      "construct and NSDP is the more convenient one, which is why the rule "
                      "governing a disagreement between them was fixed in advance rather than "
                      "after the fact.")
    p = figure_after(p, doc, FIGS / "report_fig5_4.png",
                     "Figure 5.2: The resources interaction under the two income measures, with "
                     "95 per cent confidence intervals and bootstrap p-values. The strongest "
                     "income coefficient in the chapter, p = 0.0002 on credit per capita, "
                     "becomes p = 0.998 when household consumption replaces state production. "
                     "Faded markers are not significant at 5 per cent.")
    p = para_after(p, "The interaction that carried the resources channel disappears entirely. "
                      "The honest reading is that the apparent support for an income mechanism "
                      "in Table 5.2 was riding on the measure with the known attribution "
                      "artefact, and it is reported as measure-specific rather than as a "
                      "finding.")
    p = heading3_after(p, "5.4.3  The test that separates the two hypotheses")
    p = para_after(p, "Equation (5.2), on 495 rows and 33 state clusters.")
    p = para_after(p, "Table 5.3: The stacked specification, equation (5.2). Wild cluster "
                      "bootstrap p-values, 9,999 replications", italic=True, size=CAPTION_PT)
    p = table_after(p, doc, [
        ["Coefficient", "Term", "Estimate", "p"],
        ["β₂", "UPI × intensive  (Hypothesis 1's test)", "−0.906", "0.081"],
        ["β₃", "UPI × digital literacy", "−0.345", "0.008"],
        ["β₅", "UPI × digital literacy × intensive", "+0.452", "0.0008"],
        ["β₄", "UPI × income", "+0.196", "0.223"],
        ["β₆", "UPI × income × intensive", "+0.013", "0.936"],
    ], widths=[0.8, 3.0, 1.2, 1.0])
    p = para_after(p, "Read before interpretation. β₅ is positive and precisely estimated: "
                      "digital literacy moves the infrastructure effect away from the extensive "
                      "margin and toward the intensive one. β₆ is indistinguishable from zero, "
                      "and remains so under household consumption (+0.039, p = 0.805) and under "
                      "every placebo substituted into the same slot, including women's own bank "
                      "account in 2015-16, which is baseline financial inclusion itself "
                      "(+0.247, p = 0.543). Income's failure to discriminate between margins is "
                      "a property of the channel and not an artefact of the proxy. β₂ reproduces "
                      "Hypothesis 1's pattern on the same data.")
    p = figure_after(p, doc, FIGS / "report_fig5_2.png",
                     "Figure 5.3: The effect of UPI adoption on each margin across the observed "
                     "range of digital literacy, from equation (5.2), with 95 per cent "
                     "confidence bands. The two lines have opposite slopes and converge: in the "
                     "least literate states infrastructure shows up as accounts, in the most "
                     "literate as balances. The difference between the slopes is β₅.")
    p = para_after(p, "The substantive statement is not that infrastructure works better in more "
                      "literate states. It is that it produces something different there. In the "
                      "least digitally literate states a unit of UPI adoption is worth roughly "
                      "1.9 standard deviations on account counts and 0.4 on rupees moved; in the "
                      "most literate, roughly 0.7 on both.")
    p = heading3_after(p, "5.4.4  The falsification test")
    p = para_after(p, "The obvious objection is that digital literacy is simply development, and "
                      "any development proxy would produce the same coefficient. That objection "
                      "is testable directly, by substituting each candidate into the moderator "
                      "slot one at a time and re-estimating equation (5.2). Under the rule in "
                      "Section 5.1 this test outranks Table 5.3.")
    p = figure_after(p, doc, FIGS / "report_fig5_3.png",
                     "Figure 5.4: β₅ with each moderator substituted in turn, with 95 per cent "
                     "confidence intervals and bootstrap p-values. Red marks measures of digital "
                     "skill, blue general human capital and urbanisation. Faded markers are "
                     "not significant at 5 per cent. Four of the placebos are drawn from the same "
                     "surveys, the same households and the same fieldwork years as the treatment.")
    p = para_after(p, "The table does three things. It rules out a generic development gradient: "
                      "schooling, ever having attended school, general literacy and urbanisation "
                      "all return nothing, and three of them come from the same NFHS-5 "
                      "questionnaire and the same households as the treatment, so no difference "
                      "in sampling, instrument or fieldwork can explain why one produces β₅ and "
                      "the others do not.")
    p = para_after(p, "It addresses reverse causality with a moderator that cannot be subject to "
                      "it. Women's mobile-phone ownership in 2015-16 is measured three and a "
                      "half years before the panel opens and before UPI's April 2016 launch, and "
                      "it produces β₅ = +0.550, p = 0.049, while its two counterparts from the "
                      "same survey round return nothing. A moderator measured before the "
                      "treatment existed cannot have been caused by the outcome.")
    p = para_after(p, "And it rules out the sharpest confound available, which concerns the "
                      "outcome rather than development: states that were already more banked in "
                      "2015-16 do not convert infrastructure differently. One result in Table "
                      "5.2 points the same way. On credit per capita the digital-literacy "
                      "interaction is negative and significant while the two schooling placebos "
                      "from the same instrument are positive and significant. Opposite signs, "
                      "same survey, same respondents: these are not the same construct.")
    p = heading3_after(p, "5.4.5  What the estimate rests on")
    p = para_after(p, "β₅ averages two intensive outcomes against one extensive outcome, so it is "
                      "worth asking which pairing carries it. Re-estimating equation (5.2) one "
                      "pair at a time gives +0.749 (p = 0.002) for credit accounts against "
                      "deposits per capita and +0.155 (p = 0.324) for credit accounts against "
                      "credit per capita. The reported figure is a dilution of the first rather "
                      "than a summary of two comparable estimates, and the decisive pair clears "
                      "its own placebo battery. The interpretive claim narrows accordingly: "
                      "digital literacy moves the effect toward deposit balances specifically, "
                      "not toward the intensive margin in general.")
    p = para_after(p, "Following the pre-commitment in Section 5.1, the larger estimate is not "
                      "promoted to the headline. It was found by decomposition after the fact, "
                      "and reporting it as the result would be the retro-fitting Section 3.6.2 "
                      "refuses elsewhere in this report.")
    p = figure_after(p, doc, FIGS / "report_fig5_5.png",
                     "Figure 5.5: Left: β₅ estimated one outcome pair at a time. The effect is "
                     "carried by deposits, and reverses when the entangled deposit-account "
                     "measure replaces credit accounts on the extensive side (grey). Right: the "
                     "distribution of β₅ across 33 refits, each dropping one state.")
    p = para_after(p, "The grey rows locate a robustness failure rather than hiding it. When the "
                      "entangled deposit-account indicator is used on the extensive side, β₅ "
                      "does not merely weaken; it turns negative and the income coefficient "
                      "becomes significant (+0.420, p = 0.014 and +0.576, p = 0.040). "
                      "Substituting the entangled measure replaces a skills result with an "
                      "income result, which is what an accounting relationship looks like: "
                      "registration requires a bank account, richer states register more, and "
                      "account counts follow mechanically. The credit-only rule of Section 3.5.2 "
                      "is doing real work, and this is the clearest evidence for it in the "
                      "report.")
    p = heading3_after(p, "5.4.6  Thresholds, with no functional form assumed")
    p = para_after(p, "The interaction in equation (5.2) assumes the returns to digital literacy are "
                      "linear. Grouping states into terciles drops that assumption.")
    p = figure_after(p, doc, FIGS / "report_fig5_6.png",
                     "Figure 5.6: Left: the effect of UPI adoption on each outcome, with states "
                     "grouped into thirds by digital literacy. Right: the difference between the "
                     "intensive and extensive effects by tercile. The gap is −1.06 in the least "
                     "literate third and −0.26 in the most literate, with the difference "
                     "significant at p = 0.021.")
    p = para_after(p, "The tercile pattern agrees with β₅ without assuming its shape, and it "
                      "sharpens the reading of Section 5.4.5: deposits rise monotonically across "
                      "the three groups while neither credit series does. The gap between the "
                      "two margins is wide where digital literacy is scarce and nearly closed where it "
                      "is not.")
    p = heading3_after(p, "5.4.7  Robustness")
    p = para_after(p, "Table 5.4: Robustness of β₅. Wild cluster bootstrap p-values",
                   italic=True, size=CAPTION_PT)
    p = table_after(p, doc, [
        ["Specification", "β₅", "p"],
        ["Reported estimate", "+0.452", "0.0008"],
        ["Digital literacy residualised on UPI adoption", "+0.358", "0.004"],
        ["Excluding Delhi 2023 and Chandigarh 2023 (Section 2.7)", "+0.427", "0.003"],
        ["Excluding the four small union territories", "+0.462", "0.045"],
        ["Excluding the three highest and three lowest literacy states", "+0.602", "0.013"],
        ["Deposit accounts added to the extensive side", "−0.070", "0.691"],
    ], widths=[3.6, 1.1, 1.1])
    p = para_after(p, "Dropping each state in turn and refitting 33 times gives a range of +0.382 "
                      "to +0.560, a worst p-value of 0.029, no sign flips and no refit that "
                      "loses significance. The contrast with Section 3.4.2 is the point: there, "
                      "two observations out of 198 reversed the sign of every ATM coefficient; "
                      "here, removing an entire state moves the estimate by at most a quarter "
                      "and never changes the conclusion. The final row is the failure diagnosed "
                      "in Section 5.4.5 and is reported as a failure.")

    # ============================================================ 5.5
    p = find_in_ch5(doc, "To be completed: Apply the pre-committed rule as written; state whether "
                       "the hypothesis is supported, partially supported or not supported, and "
                       "what the result does not license concluding. Then substantive, policy "
                       "and methodological implications, carrying the cross-cutting ones to "
                       "Chapter 6; then limitations, referencing rather than restating the "
                       "shared data limitations of Section 2.7.")
    clear_paragraph(p)
    p.add_run("The hypothesis claims that infrastructure works better where digital literacy is "
              "higher and where incomes are higher, and that the two act as complements to it. "
              "Both claims are assessed against the rule fixed in Section 5.1, which subordinates "
              "the estimates to the falsification test. The answer to the research question is "
              "yes for digital literacy and no for income, but not in the direction the claim "
              "anticipated, and the difference between the two is the finding.")
    p = boxed(p, doc, "Verdict on the pre-committed hypothesis",
              ["Not supported as stated for digital literacy, and supported in a different and "
               "more informative form. Infrastructure is not uniformly more effective where "
               "digital literacy is higher: the effect on account creation is if anything "
               "weaker there. What digital literacy changes is which margin the effect appears "
               "on, β₅ = +0.452, p = 0.0008, and no placebo reproduces it. Digital literacy is a "
               "complement at the usage margin and not at the access margin.",
               "Not supported for income. The moderation is significant on one income measure "
               "and absent on the better-constructed one, and under either measure income fails "
               "the test that separates a genuine complement from general prosperity. Income "
               "raises both margins together, which is what a level effect looks like.",
               "The claim is narrower than the coefficient. It concerns deposit balances "
               "specifically (Section 5.4.5), it is an association rather than a causal effect, "
               "and it does not hold when the entangled account measure is used."])
    p = para_after(p, "")
    p.add_run("What the result means substantively is a statement about measurement as much as "
              "about policy. The same national rollout, reaching two states equally, leaves one "
              "with more bank accounts and the other with more money held in them. Account "
              "counts are the indicator financial inclusion is scored on, internationally and in "
              "the schemes described in Section 1.2, and they will record the less digitally literate "
              "state as the larger success when what it has gained is the thinner outcome. The "
              "access-usage gap that motivates this report reappears inside the digital result, "
              "distributed by skill.")
    p = para_after(p, "The finding also bears on the mechanism proposed in Section 3.5.5, that "
                      "UPI moves credit accounts through payment history feeding cash-flow "
                      "underwriting. Digital literacy does not moderate that channel: the credit "
                      "pairing is null and the skills interaction on credit accounts is "
                      "negative. That is consistent with the proposed mechanism rather than "
                      "against it. If underwriting reads a borrower's payment trail "
                      "algorithmically, the borrower's own digital literacy is not the binding input. "
                      "Digital literacy matters where the user has to act, which is accumulating a "
                      "balance, and not where an algorithm acts on their behalf.")
    p = para_after(p, "For policy the implication is narrower than the framing in Section 1.1 "
                      "would suggest, and firmer for being narrower. Digital skilling is not "
                      "what makes infrastructure spending work: the main effect is positive "
                      "everywhere, and the least literate states record the largest gains in "
                      "account creation. Skilling determines whether those accounts are used. "
                      "That is a claim about sequencing at the usage margin specifically, and it "
                      "is defensible in a way that a general 'train people first' recommendation "
                      "would not be. The corresponding caution is that uniform national "
                      "infrastructure, evaluated on account counts, will appear to be closing "
                      "gaps at the moment it is widening them on the measure that matters.")
    p = para_after(p, "Limitations. The shared data limitations of Section 2.7 apply unchanged "
                      "and are not restated. Four are specific to this chapter. First and "
                      "binding, this chapter interacts a main effect that Section 3.6.2 "
                      "establishes as a within-state correlation between two co-trending series, "
                      "added after a pre-registered hypothesis failed; the interaction inherits "
                      "that, and no causal claim is available. β₅ is partially insulated, since "
                      "it is a difference between outcomes measured on the same state in the "
                      "same year and any confounder acting equally on both margins differences "
                      "out of it, but a confounder that moves the two margins differently and "
                      "correlates with digital literacy would still contaminate it. The placebo "
                      "battery is evidence against that; it is not proof.")
    p = para_after(p, "Second, the estimate rests on one outcome pairing rather than two "
                      "(Section 5.4.5) and reverses on the entangled account measure. Third, the "
                      "analysis is state-level and cannot show that individuals with more "
                      "digital literacy use their own accounts more; a district-level design was "
                      "examined and is not available, because the district fact sheets of the "
                      "source survey do not carry the internet-use item. Fourth, the moderator "
                      "is self-reported ever-use rather than tested skill, and the payment "
                      "measure remains one firm's rather than the market's, with market share "
                      "that varies by state; if that share is higher in more digitally literate "
                      "states, part of β₅ is measurement.")
    print("  Chapter 5 written")


# ----------------------------------------------------------------- Appendix A
def build_appendix(doc):
    p = find_para(doc, "To be completed: Append decisions taken for Hypotheses 2 and 3")
    clear_paragraph(p)
    p.add_run("The decisions taken for Chapter 5 continue the same numbering. Three are worth "
              "reading before the chapter rather than after it: D25, which fixed in advance "
              "which income measure would govern if the two disagreed, and they do; D26, which "
              "replaced a judgement about the fixed-effect structure with a test of it; and D27, "
              "which refused to promote a larger estimate found after the fact to the headline.")
    p = para_after(p, "Table A.2: Decision log, D18-D28", italic=True, size=CAPTION_PT)
    p = table_after(p, doc, [
        ["#", "Decision", "Rationale and consequence"],
        ["D18", "Run on the Track 3 panel unchanged",
         "Same 165 rows, outcomes, estimator and clustering as Chapter 3, so the baseline must "
         "reproduce Table 3.7 to five decimals. It does; that is a build check, not a result."],
        ["D19", "No district-level design",
         "District-level payment data exist, but the district fact sheets of the moderator survey "
         "do not carry the internet-use item, so there would be nothing to interact. Checked and "
         "rejected rather than overlooked."],
        ["D20", "NFHS-5 as the primary skills measure, NSS 75th as robustness",
         "The published NSS state tables cover 22 of 33 states and omit most of the upper tail. "
         "The two correlate 0.87 to 0.90 where both exist."],
        ["D21", "Moderators standardised; the income moderator held time-invariant",
         "The skills measure is a single survey wave. Letting income vary while skills could not "
         "would decide the comparison by that asymmetry rather than by the data."],
        ["D22", "Outcome-specific fixed effects",
         "Every outcome carries its own state and year effect. Superseded in part by D26."],
        ["D23", "Report the robustness failure rather than explain it away",
         "Adding the entangled account measure to the extensive side reverses the estimate. "
         "Reported, and diagnosed in Section 5.4.5."],
        ["D24", "All claims are heterogeneity claims, not causal ones",
         "The main effect being moderated is not causal, so the moderation cannot be. Fixed in "
         "advance so no result could be written up more strongly than the design allows."],
        ["D25", "MPCE added as the second income measure, and named in advance as the better one",
         "Per-capita NSDP is a production measure carrying the same attribution artefact as "
         "branch-located deposits. The two disagree, and the rule is applied as written: the "
         "income result is reported as measure-specific."],
        ["D26", "The fixed-effect structure is tested, not argued",
         "The restricted form is nested and rejected, F(72, 375) = 89.2. Converts a judgement "
         "call into a data requirement. Classical F-test; it licenses the fixed effects, not the "
         "standard errors."],
        ["D27", "The pre-specified headline is not replaced by the larger estimate",
         "Decomposition finds +0.749 on one outcome pairing against +0.452 reported. The larger "
         "figure was found after the fact and is reported as a decomposition, not promoted."],
        ["D28", "A strictly pre-window moderator added for reverse causality",
         "Mobile-phone ownership in 2015-16, before the payment system launched, with its "
         "same-round counterparts as controls. A weaker construct, used only for this check."],
    ], widths=[0.5, 2.0, 4.0])
    print("  Appendix A written")


if __name__ == "__main__":
    raise SystemExit(main())
