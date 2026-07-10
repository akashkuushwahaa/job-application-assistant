"""
Job Application Assistant
--------------------------
Parses a resume + job posting, scores the match, drafts a tailored
cover letter, suggests resume bullet rewrites, and logs the result
to a CSV tracker.

Requires:
    pip install openai pdfplumber python-docx

Set your key first:
    export OPENAI_API_KEY="sk-..."
"""

import os
import json
import csv
from datetime import date

import pdfplumber
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from environment
MODEL = "gpt-4o"   # swap for a cheaper model (e.g. gpt-4o-mini) if you want faster/cheaper runs

TRACKER_FILE = "applications_tracker.csv"


# ---------- Step 1: Parsing ----------

def extract_resume_text(path: str) -> str:
    """Extract plain text from a PDF resume."""
    if path.lower().endswith(".pdf"):
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif path.lower().endswith(".docx"):
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        # assume plain text file
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


def load_job_posting(text_or_path: str) -> str:
    """Accepts either raw pasted text or a path to a text file."""
    if os.path.isfile(text_or_path):
        with open(text_or_path, "r", encoding="utf-8") as f:
            return f.read()
    return text_or_path


# ---------- Step 2: Match analysis ----------

def analyze_match(resume_text: str, job_text: str) -> dict:
    prompt = f"""You are an expert technical recruiter. Compare the resume against the job posting.

RESUME:
{resume_text}

JOB POSTING:
{job_text}

Return ONLY valid JSON (no markdown, no commentary) with this exact shape:
{{
  "match_score": <integer 0-100>,
  "matched_skills": [<strings>],
  "missing_skills": [<strings>],
  "seniority_fit": "<under | matched | over>",
  "notes": "<1-2 sentence summary of overall fit>"
}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


# ---------- Step 3: Cover letter generation ----------

def generate_cover_letter(resume_text: str, job_text: str, analysis: dict) -> str:
    prompt = f"""Write a tailored, professional cover letter for this job application.

STRICT RULES:
- Only reference experience, skills, and achievements that actually appear in the resume below.
- Do NOT invent metrics, job titles, companies, or accomplishments.
- If a required skill from the job posting is missing from the resume, do not claim it — omit it or address transferable experience instead.
- Keep it to 3-4 short paragraphs, no generic filler ("I am writing to express my interest...").
- Mirror some of the job posting's own terminology where it genuinely matches the resume.

RESUME:
{resume_text}

JOB POSTING:
{job_text}

MATCH ANALYSIS (for your reference, do not repeat verbatim):
{json.dumps(analysis)}

Write only the cover letter body text."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()


# ---------- Step 4: Resume bullet suggestions ----------

def suggest_bullets(resume_text: str, job_text: str, analysis: dict) -> list:
    prompt = f"""Suggest 2-3 rewritten resume bullet points that better mirror this job posting's
language, using ONLY achievements already present in the resume (rephrase, don't invent).

RESUME:
{resume_text}

JOB POSTING:
{job_text}

Return ONLY valid JSON: {{"suggested_bullets": [<strings>]}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)["suggested_bullets"]


# ---------- Step 5: Tracker logging ----------

def log_application(company: str, role: str, analysis: dict):
    file_exists = os.path.isfile(TRACKER_FILE)
    with open(TRACKER_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "company", "role", "match_score", "status", "notes"])
        writer.writerow([
            date.today().isoformat(),
            company,
            role,
            analysis["match_score"],
            "drafted",
            analysis.get("notes", ""),
        ])


# ---------- Orchestration ----------

def run(resume_path: str, job_text_or_path: str, company: str, role: str):
    resume_text = extract_resume_text(resume_path)
    job_text = load_job_posting(job_text_or_path)

    print("Analyzing match...")
    analysis = analyze_match(resume_text, job_text)
    print(json.dumps(analysis, indent=2))

    if analysis["match_score"] < 40:
        print("\n⚠️  Match score is low — consider whether this role is worth pursuing before drafting.")

    print("\nGenerating cover letter...")
    cover_letter = generate_cover_letter(resume_text, job_text, analysis)
    print("\n--- COVER LETTER ---\n")
    print(cover_letter)

    print("\nSuggesting resume bullet rewrites...")
    bullets = suggest_bullets(resume_text, job_text, analysis)
    print("\n--- SUGGESTED BULLETS ---")
    for b in bullets:
        print(f"- {b}")

    log_application(company, role, analysis)
    print(f"\nLogged to {TRACKER_FILE}")

    return {
        "analysis": analysis,
        "cover_letter": cover_letter,
        "suggested_bullets": bullets,
    }


if __name__ == "__main__":
    # Example usage — replace with real paths/values, or wire this up to argparse/CLI input
    result = run(
        resume_path="resume.pdf",
        job_text_or_path="job_posting.txt",  # or paste the job text directly as a string
        company="Acme Corp",
        role="Backend Engineer",
    )
