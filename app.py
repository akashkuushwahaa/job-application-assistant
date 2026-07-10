"""
Job Application Assistant — Streamlit UI
------------------------------------------
A simple web interface: upload your resume once, paste a job posting,
click generate, and get a match score, cover letter, and resume bullet
suggestions — all logged to a tracker you can view and download.

Requires:
    pip install streamlit openai pdfplumber python-docx pandas

Set your key first:
    export OPENAI_API_KEY="sk-..."

Run:
    streamlit run app.py
"""

import os
import json
import csv
from datetime import date
from io import BytesIO

import streamlit as st
import pandas as pd
import pdfplumber
from openai import OpenAI

MODEL = "gpt-4o"
TRACKER_FILE = "applications_tracker.csv"

st.set_page_config(page_title="Job Application Assistant", page_icon="📝", layout="wide")


# ---------- Core logic (same as job_application_assistant.py) ----------

def get_client():
    api_key = st.session_state.get("api_key") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def extract_resume_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    data = uploaded_file.read()
    if name.endswith(".pdf"):
        with pdfplumber.open(BytesIO(data)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif name.endswith(".docx"):
        from docx import Document
        doc = Document(BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        return data.decode("utf-8", errors="ignore")


def analyze_match(client, resume_text, job_text) -> dict:
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


def generate_cover_letter(client, resume_text, job_text, analysis) -> str:
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


def suggest_bullets(client, resume_text, job_text) -> list:
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


def log_application(company, role, analysis):
    file_exists = os.path.isfile(TRACKER_FILE)
    with open(TRACKER_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "company", "role", "match_score", "status", "notes"])
        writer.writerow([
            date.today().isoformat(), company, role,
            analysis["match_score"], "drafted", analysis.get("notes", ""),
        ])


# ---------- UI ----------

st.title("📝 Job Application Assistant")
st.caption("Upload your resume once, paste a job posting, and get a match score, tailored cover letter, and resume bullet suggestions.")

with st.sidebar:
    st.header("Settings")
    key_input = st.text_input("OpenAI API Key", type="password",
                               value=os.environ.get("OPENAI_API_KEY", ""),
                               help="Or set the OPENAI_API_KEY environment variable instead.")
    if key_input:
        st.session_state["api_key"] = key_input

    st.divider()
    st.header("Tracker")
    if os.path.isfile(TRACKER_FILE):
        df = pd.read_csv(TRACKER_FILE)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download tracker CSV", df.to_csv(index=False), TRACKER_FILE, "text/csv")
    else:
        st.info("No applications logged yet.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Your resume")
    resume_file = st.file_uploader("Upload resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])

with col2:
    st.subheader("2. Job posting")
    company = st.text_input("Company name")
    role = st.text_input("Role title")
    job_text = st.text_area("Paste the job posting text", height=220)

generate = st.button("Generate application materials", type="primary", use_container_width=True)

if generate:
    client = get_client()
    if not client:
        st.error("Enter your OpenAI API key in the sidebar first.")
    elif not resume_file:
        st.error("Upload a resume.")
    elif not job_text.strip():
        st.error("Paste the job posting text.")
    else:
        with st.spinner("Reading resume..."):
            resume_text = extract_resume_text(resume_file)

        with st.spinner("Analyzing match..."):
            analysis = analyze_match(client, resume_text, job_text)

        score = analysis["match_score"]
        st.subheader("Match analysis")
        m1, m2, m3 = st.columns(3)
        m1.metric("Match score", f"{score}/100")
        m2.metric("Seniority fit", analysis.get("seniority_fit", "—"))
        m3.metric("Missing skills", len(analysis.get("missing_skills", [])))

        if score < 40:
            st.warning("Match score is low — consider whether this role is worth pursuing before applying.")

        st.write(analysis.get("notes", ""))

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Matched skills**")
            for s in analysis.get("matched_skills", []):
                st.markdown(f"- {s}")
        with c2:
            st.markdown("**Missing skills**")
            for s in analysis.get("missing_skills", []):
                st.markdown(f"- {s}")

        with st.spinner("Drafting cover letter..."):
            cover_letter = generate_cover_letter(client, resume_text, job_text, analysis)

        st.subheader("Cover letter")
        st.text_area("Editable draft", cover_letter, height=280, key="cover_letter_output")
        st.download_button("Download cover letter (.txt)", cover_letter, "cover_letter.txt")

        with st.spinner("Suggesting resume bullet rewrites..."):
            bullets = suggest_bullets(client, resume_text, job_text)

        st.subheader("Suggested resume bullets")
        for b in bullets:
            st.markdown(f"- {b}")

        log_application(company or "Unknown", role or "Unknown", analysis)
        st.success(f"Logged to {TRACKER_FILE}. Refresh the sidebar tracker to see it.")
