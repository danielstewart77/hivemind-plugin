#!/usr/bin/env python3
"""PDF Resume Formatter

Reads a PDF resume, fixes formatting issues (like flattened bullet points),
and generates a new properly formatted PDF.

Usage:
    python pdf_formatter.py input.pdf output.pdf
    python pdf_formatter.py input.pdf output.pdf --no-fix-bullets
"""

import argparse
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import fitz  # PyMuPDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

# ── Constants ──────────────────────────────────────────────────────────────────

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.65 * inch

MONTHS_RE = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DATE_RANGE_RE = re.compile(
    rf"({MONTHS_RE})\s+\d{{4}}\s*[-–—]\s*(?:({MONTHS_RE})\s+\d{{4}}|Present)",
    re.IGNORECASE,
)
YEAR_RANGE_RE = re.compile(r"\d{4}\s*[-–—]\s*(?:\d{4}|Present)", re.IGNORECASE)

SECTION_HEADERS = {"SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS"}

# Colors
COLOR_NAME = HexColor("#1a1a1a")
COLOR_SECTION = HexColor("#2c3e50")
COLOR_TITLE = HexColor("#2c3e50")
COLOR_BODY = HexColor("#333333")
COLOR_MUTED = HexColor("#666666")
COLOR_RULE = HexColor("#2c3e50")
COLOR_LINK = HexColor("#2c3e50")


# ── Text Extraction ────────────────────────────────────────────────────────────


def extract_styled_lines(pdf_path):
    """Extract text from PDF with style information (bold, size)."""
    doc = fitz.open(str(pdf_path))
    lines = []

    for page in doc:
        page_dict = page.get_text("dict", sort=True)
        for block in page_dict["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                spans = line["spans"]
                if not spans:
                    continue

                text = "".join(s["text"] for s in spans)
                if not text.strip():
                    continue

                is_bold = any(
                    "Bold" in s["font"] or "bold" in s["font"].lower()
                    for s in spans
                )
                max_size = max(s["size"] for s in spans)

                lines.append({
                    "text": text.strip(),
                    "bold": is_bold,
                    "size": round(max_size, 1),
                })

    doc.close()
    return lines


# ── Resume Parsing ─────────────────────────────────────────────────────────────


def find_date_range(text):
    """Find a date range in text. Returns (match_str, start, end) or None."""
    m = DATE_RANGE_RE.search(text)
    if m:
        return m.group(0), m.start(), m.end()
    m = YEAR_RANGE_RE.search(text)
    if m:
        return m.group(0), m.start(), m.end()
    return None


def parse_resume(lines):
    """Parse styled lines into a structured resume dictionary."""
    resume = {
        "name": "",
        "contact": [],
        "sections": [],
    }

    if not lines:
        return resume

    # Name is the first line (largest font)
    resume["name"] = lines[0]["text"]

    # Find section header positions
    section_indices = []
    for i, line in enumerate(lines):
        if line["text"].upper().strip() in SECTION_HEADERS:
            section_indices.append((i, line["text"].upper().strip()))

    # Contact info: everything between name and first section
    first_section_idx = section_indices[0][0] if section_indices else len(lines)
    for i in range(1, first_section_idx):
        text = lines[i]["text"].strip()
        if text and text.upper() not in SECTION_HEADERS:
            resume["contact"].append(text)

    # Process each section
    for sec_num, (sec_idx, sec_name) in enumerate(section_indices):
        if sec_num + 1 < len(section_indices):
            next_sec_idx = section_indices[sec_num + 1][0]
        else:
            next_sec_idx = len(lines)

        section_lines = lines[sec_idx + 1 : next_sec_idx]

        if sec_name == "SUMMARY":
            text = " ".join(l["text"] for l in section_lines)
            resume["sections"].append({"type": "summary", "text": text})

        elif sec_name == "EXPERIENCE":
            jobs = parse_experience(section_lines)
            resume["sections"].append({"type": "experience", "jobs": jobs})

        elif sec_name == "EDUCATION":
            education = parse_education(section_lines)
            resume["sections"].append({"type": "education", "entries": education})

        elif sec_name == "SKILLS":
            skills = parse_skills(section_lines)
            resume["sections"].append({"type": "skills", "items": skills})

    return resume


MONTH_YEAR_RE = re.compile(
    rf"^({MONTHS_RE}\s+\d{{4}})\s*[-–—]?\s*$", re.IGNORECASE
)
SINGLE_YEAR_RE = re.compile(r"^\d{4}$")
PRESENT_RE = re.compile(r"^Present$", re.IGNORECASE)
# Matches "August 2017 - November" (date range missing the ending year)
PARTIAL_RANGE_RE = re.compile(
    rf"^({MONTHS_RE}\s+\d{{4}})\s*[-–—]\s*({MONTHS_RE})\s*$", re.IGNORECASE
)


def _is_partial_date(text):
    """Check if text looks like a partial date fragment."""
    return bool(
        MONTH_YEAR_RE.match(text)
        or SINGLE_YEAR_RE.match(text)
        or PRESENT_RE.match(text)
        or PARTIAL_RANGE_RE.match(text)
    )


def _extract_company_and_dates(candidate_lines):
    """
    From the first few lines after a job title, identify which are
    company name vs. date fragments (handling out-of-order extraction
    and dates split across pages).

    Returns (company, dates, desc_start_index).
    """
    limit = min(len(candidate_lines), 5)
    window = candidate_lines[:limit]

    # ── Pass 1: look for a complete date range on a single line ──
    for i, line in enumerate(window):
        text = line["text"].strip()
        date_info = find_date_range(text)
        if date_info:
            date_str, start, _ = date_info
            company_part = text[:start].strip()
            company = company_part
            # If company wasn't on the same line, check earlier lines
            if not company:
                for j in range(i):
                    if not _is_partial_date(window[j]["text"].strip()):
                        company = window[j]["text"].strip()
                        break
            return company, date_str, i + 1

    # ── Pass 2: try to combine partial date fragments ──
    partial_indices = []
    for i, line in enumerate(window):
        text = line["text"].strip()
        if _is_partial_date(text):
            partial_indices.append(i)

    if len(partial_indices) >= 2:
        texts = [window[j]["text"].strip() for j in partial_indices]

        # Case A: "August 2017 - November" + "2022" → append year
        partial_match = PARTIAL_RANGE_RE.match(texts[0])
        if partial_match and (
            SINGLE_YEAR_RE.match(texts[1]) or PRESENT_RE.match(texts[1])
        ):
            combined = texts[0].rstrip() + " " + texts[1]
        else:
            # Case B: "September 2011 -" + "December 2012" → strip dash, join
            parts = [t.rstrip("-–— ") for t in texts]
            combined = parts[0] + " - " + parts[1]

        date_info = find_date_range(combined)
        if date_info:
            dates = date_info[0]
        else:
            dates = combined  # best effort

        # Company is the first non-date line in the window
        company = ""
        last_partial = max(partial_indices)
        for i in range(last_partial + 1):
            if i not in partial_indices:
                company = window[i]["text"].strip()
                break
        return company, dates, last_partial + 1

    if len(partial_indices) == 1:
        idx = partial_indices[0]
        dates = window[idx]["text"].strip().rstrip("-–— ")
        company = ""
        for i in range(limit):
            if i != idx and not _is_partial_date(window[i]["text"].strip()):
                company = window[i]["text"].strip()
                break
        return company, dates, idx + 1

    # ── Pass 3: no dates found – first line is company ──
    if window:
        return window[0]["text"].strip(), "", 1
    return "", "", 0


def parse_experience(lines):
    """Parse experience section into structured job entries."""
    # First pass: locate all job-title indices (bold, non-date lines)
    title_indices = []
    for i, line in enumerate(lines):
        if line["bold"] and not find_date_range(line["text"].strip()):
            title_indices.append(i)

    jobs = []
    for t, title_idx in enumerate(title_indices):
        title = lines[title_idx]["text"].strip()

        # Lines between this title and the next
        end_idx = title_indices[t + 1] if t + 1 < len(title_indices) else len(lines)
        candidate_lines = lines[title_idx + 1 : end_idx]

        company, dates, desc_start = _extract_company_and_dates(candidate_lines)

        desc_parts = [l["text"].strip() for l in candidate_lines[desc_start:]]

        # Join lines, handling word-break hyphens (e.g., "agent-\ntool" → "agent-tool")
        joined = []
        for part in desc_parts:
            if joined and joined[-1].endswith("-") and part and part[0].islower():
                # Word-break hyphen: concat directly (keep the hyphen)
                joined[-1] = joined[-1] + part
            else:
                joined.append(part)

        jobs.append({
            "title": title,
            "company": company,
            "dates": dates,
            "description": " ".join(joined),
        })

    return jobs


def parse_education(lines):
    """Parse education section into entries."""
    entries = []
    current = None

    for line in lines:
        text = line["text"].strip()
        if not text:
            continue
        # Skip footer content
        if text.lower().startswith("email") or text.lower().startswith("address"):
            continue

        if line["bold"]:
            if current:
                entries.append(current)
            # Check if date is on the same line
            date_info = find_date_range(text)
            yr = YEAR_RANGE_RE.search(text)
            if date_info:
                school = text[: date_info[1]].strip()
                current = {"school": school, "degree": "", "dates": date_info[0]}
            elif yr:
                school = text[: yr.start()].strip()
                current = {"school": school, "degree": "", "dates": yr.group(0)}
            else:
                current = {"school": text, "degree": "", "dates": ""}

        elif current:
            date_info = find_date_range(text)
            yr = YEAR_RANGE_RE.search(text)
            if date_info:
                current["dates"] = date_info[0]
            elif yr:
                current["dates"] = yr.group(0)
            else:
                current["degree"] = (
                    current["degree"] + " " + text if current["degree"] else text
                )

    if current:
        entries.append(current)
    return entries


def parse_skills(lines):
    """Parse skills section into a flat list."""
    skills = []
    for line in lines:
        text = line["text"].strip()
        if not text:
            continue
        if text.lower().startswith("email") or text.lower().startswith("address"):
            continue
        text = re.sub(r"^[•·\-*]\s*", "", text)
        if text:
            skills.append(text)
    return skills


# ── Bullet Restoration ─────────────────────────────────────────────────────────


def protect_date_ranges(text):
    """Replace dashes in date ranges with a placeholder to avoid splitting."""
    placeholder = "\u3008DATE_DASH\u3009"

    def replacer(match):
        return match.group(0).replace("-", placeholder).replace("–", placeholder)

    protected = DATE_RANGE_RE.sub(replacer, text)
    return protected, placeholder


def unprotect_date_ranges(text, placeholder):
    """Restore dashes in date ranges from placeholder."""
    return text.replace(placeholder, "-")


def restore_bullets(text):
    """
    Split flattened text (where ' - ' was a bullet delimiter) into
    an intro paragraph and a list of bullet strings.
    """
    if not text:
        return {"intro": "", "bullets": []}

    # Quick check: does the text contain bullet-style dashes at all?
    protected, placeholder = protect_date_ranges(text)
    if " - " not in protected and not protected.lstrip().startswith("- "):
        return {"intro": text, "bullets": []}

    stripped = protected.strip()

    # Case 1: text starts with a bullet ("- Foo - Bar - Baz")
    if stripped.startswith("- "):
        intro = ""
        bullet_text = stripped[2:]  # skip leading "- "
    else:
        # Case 2: intro text then bullets after ": - " or ". - "
        colon_bullet = re.search(r"([:.])\s+- ", protected)
        if colon_bullet:
            intro = unprotect_date_ranges(
                protected[: colon_bullet.start() + 1].strip(), placeholder
            )
            bullet_text = protected[colon_bullet.end() :]
        else:
            # Case 3: first occurrence of " - " splits intro from bullets
            first_dash = protected.find(" - ")
            if first_dash > 0:
                intro = unprotect_date_ranges(
                    protected[:first_dash].strip(), placeholder
                )
                bullet_text = protected[first_dash + 3 :]
            else:
                return {"intro": unprotect_date_ranges(text, placeholder), "bullets": []}

    # Split remaining text on " - " to get individual bullets
    raw_bullets = re.split(r"\s*- ", bullet_text)
    bullets = []
    for b in raw_bullets:
        b = unprotect_date_ranges(b.strip(), placeholder)
        if b:
            bullets.append(b)

    if intro:
        intro = unprotect_date_ranges(intro, placeholder)

    return {"intro": intro, "bullets": bullets}


# ── PDF Generation ─────────────────────────────────────────────────────────────


def esc(text):
    """Escape XML special characters for reportlab Paragraph markup."""
    return xml_escape(str(text))


def create_styles():
    """Build the paragraph style dictionary for the resume."""
    return {
        "name": ParagraphStyle(
            "Name",
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=COLOR_NAME,
            spaceAfter=4,
        ),
        "contact": ParagraphStyle(
            "Contact",
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=COLOR_MUTED,
            spaceAfter=2,
        ),
        "section_header": ParagraphStyle(
            "SectionHeader",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=COLOR_SECTION,
            spaceBefore=14,
            spaceAfter=6,
        ),
        "job_title": ParagraphStyle(
            "JobTitle",
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=COLOR_TITLE,
            spaceBefore=10,
            spaceAfter=1,
        ),
        "company": ParagraphStyle(
            "Company",
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=COLOR_MUTED,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=9.5,
            leading=12.5,
            textColor=COLOR_BODY,
            alignment=TA_JUSTIFY,
            spaceAfter=2,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontName="Helvetica",
            fontSize=9.5,
            leading=12.5,
            textColor=COLOR_BODY,
            alignment=TA_JUSTIFY,
            leftIndent=18,
            firstLineIndent=0,
            spaceAfter=3,
            bulletIndent=6,
            bulletFontName="Helvetica",
            bulletFontSize=9.5,
        ),
        "skill_item": ParagraphStyle(
            "SkillItem",
            fontName="Helvetica",
            fontSize=9.5,
            leading=12.5,
            textColor=COLOR_BODY,
            leftIndent=18,
            bulletIndent=6,
            spaceAfter=2,
        ),
        "edu_school": ParagraphStyle(
            "EduSchool",
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=COLOR_TITLE,
            spaceBefore=6,
            spaceAfter=1,
        ),
        "edu_degree": ParagraphStyle(
            "EduDegree",
            fontName="Helvetica-Oblique",
            fontSize=10,
            leading=13,
            textColor=COLOR_BODY,
            spaceAfter=2,
        ),
    }


def format_contact_line(contact_items):
    """Join contact items into one line with clickable links."""
    formatted = []
    for item in contact_items:
        item = item.strip().strip("|").strip()
        if not item:
            continue
        if "@" in item and "http" not in item:
            safe = esc(item)
            formatted.append(
                f'<a href="mailto:{safe}" color="#2c3e50">{safe}</a>'
            )
        elif item.startswith("http"):
            safe = esc(item)
            formatted.append(f'<a href="{safe}" color="#2c3e50">{safe}</a>')
        else:
            formatted.append(esc(item))
    return "  |  ".join(formatted)


def build_company_date_row(company, dates, styles, available_width):
    """Create a table row with company on the left and dates on the right."""
    company_para = Paragraph(esc(company), styles["company"])
    date_style = ParagraphStyle(
        "DateRight", parent=styles["company"], alignment=TA_RIGHT
    )
    date_para = Paragraph(esc(dates), date_style)

    t = Table(
        [[company_para, date_para]],
        colWidths=[available_width * 0.65, available_width * 0.35],
    )
    t.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])
    )
    return t


def generate_pdf(resume, output_path, fix_bullets=True):
    """Generate a formatted PDF from the parsed resume structure."""
    styles = create_styles()
    available_width = PAGE_WIDTH - MARGIN * 2

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN * 0.8,
        bottomMargin=MARGIN * 0.7,
    )

    story = []

    # ── Name ──
    story.append(Paragraph(esc(resume["name"]), styles["name"]))

    # ── Contact ──
    if resume["contact"]:
        contact_markup = format_contact_line(resume["contact"])
        story.append(Paragraph(contact_markup, styles["contact"]))

    # ── Horizontal rule ──
    story.append(Spacer(1, 4))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=COLOR_RULE,
            spaceAfter=4,
            spaceBefore=0,
        )
    )

    # ── Sections ──
    for section in resume["sections"]:

        # ── Summary ──
        if section["type"] == "summary":
            story.append(Paragraph("SUMMARY", styles["section_header"]))
            story.append(Paragraph(esc(section["text"]), styles["body"]))

        # ── Experience ──
        elif section["type"] == "experience":
            story.append(Paragraph("EXPERIENCE", styles["section_header"]))

            for job in section["jobs"]:
                # Job title
                story.append(Paragraph(esc(job["title"]), styles["job_title"]))

                # Company + dates
                if job["company"] and job["dates"]:
                    story.append(
                        build_company_date_row(
                            job["company"], job["dates"], styles, available_width
                        )
                    )
                elif job["company"]:
                    story.append(Paragraph(esc(job["company"]), styles["company"]))

                # Description (with optional bullet restoration)
                desc = job["description"]
                if not desc:
                    continue

                if fix_bullets:
                    parsed = restore_bullets(desc)
                    if parsed["intro"]:
                        story.append(Paragraph(esc(parsed["intro"]), styles["body"]))
                    for bullet in parsed["bullets"]:
                        story.append(
                            Paragraph(
                                f"<bullet>&bull;</bullet>{esc(bullet)}",
                                styles["bullet"],
                            )
                        )
                    # If no bullets were found, fall through to plain text
                    if not parsed["bullets"] and not parsed["intro"]:
                        story.append(Paragraph(esc(desc), styles["body"]))
                else:
                    story.append(Paragraph(esc(desc), styles["body"]))

        # ── Education ──
        elif section["type"] == "education":
            story.append(Paragraph("EDUCATION", styles["section_header"]))

            for entry in section["entries"]:
                if entry.get("dates"):
                    story.append(
                        build_company_date_row(
                            entry["school"],
                            entry["dates"],
                            styles,
                            available_width,
                        )
                    )
                else:
                    story.append(
                        Paragraph(esc(entry["school"]), styles["edu_school"])
                    )

                if entry.get("degree"):
                    story.append(
                        Paragraph(esc(entry["degree"]), styles["edu_degree"])
                    )

        # ── Skills ──
        elif section["type"] == "skills":
            story.append(Paragraph("SKILLS", styles["section_header"]))

            for skill in section["items"]:
                story.append(
                    Paragraph(
                        f"<bullet>&bull;</bullet>{esc(skill)}", styles["skill_item"]
                    )
                )

    doc.build(story)


# ── Main ───────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="PDF Resume Formatter – fix flattened bullets and reformat"
    )
    parser.add_argument("input", help="Path to the input PDF")
    parser.add_argument("output", help="Path for the output PDF")
    parser.add_argument(
        "--no-fix-bullets",
        action="store_true",
        help="Skip bullet-point restoration",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    if input_path.suffix.lower() != ".pdf":
        print(f"Error: not a PDF file: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading:  {input_path}")
    styled_lines = extract_styled_lines(input_path)

    if not styled_lines:
        print("Error: could not extract text from PDF", file=sys.stderr)
        sys.exit(1)

    resume = parse_resume(styled_lines)

    print(f"  Name: {resume['name']}")
    for section in resume["sections"]:
        if section["type"] == "experience":
            print(f"  Jobs found: {len(section['jobs'])}")
            for job in section["jobs"]:
                print(f"    • {job['title']} @ {job['company']}")

    fix_bullets = not args.no_fix_bullets
    print(f"Generating: {output_path}  (fix_bullets={fix_bullets})")
    generate_pdf(resume, output_path, fix_bullets=fix_bullets)

    # Report sizes
    in_size = input_path.stat().st_size
    out_size = output_path.stat().st_size
    print(f"Done!  {in_size:,} bytes → {out_size:,} bytes")


if __name__ == "__main__":
    main()
