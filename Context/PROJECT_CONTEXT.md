# Job Application Workspace — Complete Project Context

> Canonical context snapshot for writing reports, presentations, abstracts, proposals,
> README files, demonstrations, case studies, and other project documents.
>
> Last verified against the repository: **5 September 2026**.
>
> This file describes the current implementation. Where older internship materials differ
> from the code, the current implementation documented here takes precedence.
>
> [The 5 September project review](PROJECT_REVIEW.md) records what changed on that date and
> why, and lists the remaining improvement priorities. This file states the resulting
> behaviour; the review is the change log behind it.

## 1. Project identity

### Current product name

**Job Application Workspace**

### Alternative name used in academic material

**Job Application Assistant — An AI-Powered Resume & Job-Posting Matching Tool**

Use “Job Application Workspace” when describing the current application or UI. “Job
Application Assistant” is acceptable in internship and academic documents because that is
the name used in the existing report and presentation.

### One-sentence description

The Job Application Workspace is a personal Python application that compares a candidate’s
resume with a job posting, generates evidence-grounded application materials, prepares the
candidate for interviews, and tracks the application lifecycle in a SQLite database by
default, or in Postgres when one is configured.

### Short abstract

Preparing a tailored job application requires candidates to interpret a job description,
evaluate their fit, adapt their resume, write a cover letter, anticipate interview questions,
and track follow-up activity. The Job Application Workspace combines these tasks in one
application. A user supplies a PDF, DOCX, or UTF-8 text resume together with a
job posting and basic role details. The application sends the extracted resume text and job
posting to an OpenAI model through the Responses API and requests a strictly validated,
structured result. It produces a transparent fit estimate, requirement-level evidence,
matched and missing skills, a grounded cover letter, resume-bullet suggestions linked to
their source evidence, and role-specific interview questions. The generated workspace is
stored in the configured database and can be searched, edited, exported, and moved through a
recorded status history. The system is decision support rather than an objective ATS scorer, does not
auto-submit applications, and instructs the model never to invent candidate facts.

## 2. Academic attribution

The project-specific internship presentation identifies the following details:

- Prepared by: **Kushwaha Akash**
- Enrollment number: **240673142004**
- Guide: **Ms. Khyati Patel**
- Branch: **Computer Science and Engineering (Artificial Intelligence and Machine Learning)**
- Institution: **SAL Institute of Technology and Engineering Research**, Ahmedabad, Gujarat
- University affiliation: **Gujarat Technological University (GTU)**
- Academic year used by the report template: **2026–2027**

The existing Word report still contains placeholders for the candidate name, department,
internal/external guides, company, and internship dates. Do not invent those missing values.
Before producing a formal submission, confirm the required spelling, capitalization,
internship organization, dates, and signatures with the student.

## 3. Problem statement

Job applications are repetitive and fragmented. For every opening, a candidate must read a
job posting, compare its requirements with their resume, decide whether the role is a useful
fit, tailor written materials, prepare for likely questions, and remember the application’s
current state. Doing this manually across many opportunities is slow, inconsistent, and hard
to track. Generic AI writing tools can introduce another risk: polished but unsupported
claims about experience, skills, employers, education, or metrics.

This project addresses the problem with a single workspace that joins evidence-led analysis,
grounded drafting, interview preparation, and application tracking while keeping the user in
control of every final decision.

## 4. Aim, objectives, and success criteria

### Aim

Reduce the time and effort required to prepare tailored job applications without sacrificing
truthfulness, transparency, privacy, or human control.

### Objectives

1. Extract readable text from PDF, DOCX, and UTF-8 TXT resumes.
2. Compare resume evidence with a job posting and produce a 0–100 fit estimate.
3. Separate must-have requirements from preferred requirements.
4. Show matched skills, missing skills, seniority fit, and requirement-level evidence.
5. Draft a professional cover letter using only facts present in the resume.
6. Suggest targeted resume-bullet rewrites and preserve the original supporting evidence.
7. Generate likely technical, behavioural, and role-specific interview questions with tips.
8. Persist job metadata, generated materials, model information, token usage, and status
   history in a local database.
9. Allow users to edit and export application materials and manage application statuses.
10. Provide both a browser interface and a command-line interface over one shared core.

### Success criteria reflected in the implementation

- Invalid inputs and common API failures produce safe, user-facing error messages.
- Model responses must satisfy strict Pydantic schemas before they are used or saved.
- Resume text is not stored in the database; only its filename and SHA-256 content hash are
  retained for version identification.
- The OpenAI generation request sets response storage to `false`.
- Generated claims remain reviewable and editable; nothing is submitted automatically.
- The same parsing, validation, generation, persistence, and export logic serves both UIs.
- Automated tests cover the most important parsing, validation, persistence, migration,
  export-security, document-export, and AI-orchestration behavior.

## 5. Intended users and usage model

The primary user is an individual job seeker using the application on their own computer.
It is designed for personal, local use, not as a public multi-tenant service.

Typical use cases include:

- deciding whether an opening is worth pursuing;
- understanding which requirements have direct resume evidence;
- identifying genuine gaps before applying;
- creating a first draft of a cover letter;
- adapting existing resume bullets without inventing achievements;
- preparing examples for likely interview questions;
- tracking applications from discovery through an offer, rejection, withdrawal, or archive;
- exporting a filtered application list for personal analysis or backup.

## 6. Scope and non-goals

### In scope

- Local resume parsing for PDF, DOCX, and UTF-8 TXT files
- Job-posting text supplied directly or, in the CLI, through a TXT/Markdown file
- OpenAI-based structured analysis and drafting
- Evidence-led fit analysis
- Cover-letter generation and editing
- Resume-bullet suggestions and editing
- Interview-question generation
- SQLite application tracking and status history
- Search, filtering, dashboard counts, CSV export, TXT export, and DOCX cover-letter export
- Streamlit web UI and argparse-based CLI
- One-time import of a legacy CSV tracker

### Explicitly out of scope

- Automatically applying to jobs or interacting with employer websites
- Making hiring decisions or claiming to reproduce a proprietary ATS score
- Guaranteeing interviews, offers, or hiring outcomes
- Fabricating missing experience or qualifications
- OCR for image-only or scanned PDF resumes
- Fetching or scraping a job posting from its URL
- Editing the source resume file directly
- User accounts, cloud synchronization, multi-user isolation, or public SaaS deployment
- Encrypted document storage or enterprise compliance controls
- PDF cover-letter export in the current implementation
- Support for AI providers other than OpenAI

## 7. Current feature set

### Resume intake

- Accepts `.pdf`, `.docx`, and `.txt` resumes.
- Enforces a configurable maximum uploaded-file size; the default is 5 MiB.
- Limits PDF resumes to 25 pages by default.
- Rejects unsupported, empty, corrupt, oversized, unreadable, and image-only resumes with a
  clear message.
- Reads DOCX paragraphs, tables, headers, and footers.
- Checks the total uncompressed DOCX archive size against a fixed 25 MiB safety limit.
- Requires TXT resumes to use UTF-8, with optional byte-order mark support.
- Normalizes NULs, line endings, repeated horizontal whitespace, blank lines, and surrounding
  whitespace.
- Limits normalized resume text to 60,000 characters by default.

### Job and role intake

- Requires company and role, each no longer than 200 normalized characters.
- Accepts a complete pasted job description up to 60,000 characters by default.
- The CLI can interpret a short job argument as a path to a `.txt` or `.md` file.
- Accepts optional job URL, source, and location fields.
- Job URLs must have an `http` or `https` scheme and a network location.
- Source and location are normalized and truncated to 200 characters.
- The application stores the original job posting for later reference.
- The URL is metadata only; the application does not download its contents.

### Fit analysis

- Produces a fit estimate from 0 to 100.
- Lists up to 30 matched skills and 30 missing skills, removing blank and duplicate items.
- Classifies seniority fit as `under`, `matched`, or `over`.
- Provides a concise summary note.
- Provides up to 20 requirement-level records containing:
  - the requirement;
  - its importance (`must-have` or `preferred`);
  - supporting resume evidence;
  - fit (`matched`, `partial`, or `missing`);
  - confidence from 0 to 100;
  - a recommended action.
- Shows a warning when the fit estimate is below 40.
- Treats the score as transparent decision support, not an objective or guaranteed ATS score.

### Generated application materials

- Generates a cover letter between 100 and 7,000 characters.
- Generates between one and five resume-bullet suggestions.
- Each suggestion contains exact original resume evidence, an editable rewritten bullet, and
  an explanation of why the rewrite helps.
- Generates between four and eight interview questions.
- Each question has a category (`technical`, `behavioural`, or `role-specific`) and a
  preparation tip.
- Uses one structured model response for the entire application bundle, which keeps the
  analysis and written materials consistent.

### Editing and export

- Allows the cover letter to be edited and explicitly saved.
- Allows suggested bullet text to be edited while keeping evidence and rationale read-only in
  the web interface.
- Revalidates edited structured artifacts before saving them.
- Downloads the current cover-letter edit as plain text or formatted DOCX.
- The DOCX export uses Aptos 11 pt body text, a centered bold 14 pt role/company heading,
  approximately 0.8-inch vertical and 0.9-inch horizontal margins, and paragraph spacing.
- Exports up to 2,000 application records to CSV.
- Protects CSV consumers from spreadsheet formula injection by prefixing dangerous leading
  characters such as `=`, `+`, `-`, `@`, tab, and carriage return.

### Application tracking

- Creates a UUID for every generated application workspace.
- Starts newly generated applications in `drafted` status.
- Supports these statuses:
  `saved`, `drafted`, `applied`, `assessment`, `interviewing`, `offer`, `rejected`,
  `withdrawn`, and `archived`.
- Records every meaningful status change with timestamp, previous status, new status, and an
  optional note.
- Supports application search across company, role, and notes.
- Supports exact status filtering.
- Displays total applications, applied applications, active interviews, and offers. “Active
  interviews” is the sum of `assessment` and `interviewing` records.
- Allows a user to reopen saved analyses and materials.
- Allows application deletion after an explicit confirmation in the web UI; cascading foreign
  keys remove its status history.

## 8. System architecture

The project uses a shared-core architecture:

```text
                    +---------------------------+
                    |          User             |
                    +-------------+-------------+
                                  |
                      +-----------+-----------+
                      |                       |
              +-------v-------+       +-------v-------+
              | Streamlit UI  |       |      CLI      |
              |    app.py     |       | job_application|
              |               |       | _assistant.py  |
              +-------+-------+       +-------+--------+
                      |                       |
                      +-----------+-----------+
                                  |
                         +--------v--------+
                         |     core.py     |
                         | parsing         |
                         | validation      |
                         | AI generation   |
                         | persistence     |
                         | exports         |
                         +---+----------+--+
                             |          |
                    +--------v--+    +--v-------------------+
                    | OpenAI API |    | SQLite file, or      |
                    | Responses  |    | Postgres via         |
                    | API        |    | DATABASE_URL         |
                    |            |    | + optional legacy    |
                    |            |    | CSV import (SQLite)  |
                    +-----------+    +----------------------+
```

The front ends are deliberately thin. Business logic lives in `core.py`, so parsing,
validation, prompts, persistence, and exports have one source of truth.

### End-to-end processing flow

1. The user supplies company, role, job posting, resume, and optional metadata.
2. The web UI requires explicit confirmation that resume and job text will be sent to OpenAI.
3. The resume file is validated, parsed, normalized, and limited in memory.
4. Company, role, job text, URL, source, location, and model name are validated.
5. The shared core constructs a JSON payload containing the task, company, role, resume text,
   and job posting.
6. The OpenAI Responses API is called with system grounding instructions, the selected model,
   the `ApplicationBundle` structured-output schema, storage disabled, and a configurable
   timeout.
7. Pydantic validates the parsed response and rejects unexpected fields or invalid lengths,
   categories, counts, and scores.
8. The application saves the job metadata, validated output, model, token usage, resume
   filename, and resume hash to the configured database. Raw resume text is not saved.
9. A creation event records the initial `drafted` status.
10. The result is displayed by the UI or printed by the CLI. Later edits and status changes
    update the database, and saves refresh the other views and the dashboard counts.

Storage is initialized before the OpenAI request, so an unusable database configuration fails
before a paid request is spent rather than after.

## 9. Source-file responsibilities

### `core.py`

The shared engine and authoritative business-logic module. It contains:

- environment-backed constants and limits;
- safe user-facing `AssistantError` exceptions;
- strict Pydantic response models;
- the model system instructions;
- text normalization and field validation;
- OpenAI client creation;
- PDF, DOCX, and TXT resume parsing;
- CLI job-posting loading;
- structured OpenAI generation and token-usage extraction;
- storage-engine selection between SQLite and Postgres, schema initialization, pooled
  connections, transactions, CRUD, status history, and dashboard counts;
- one-time legacy CSV migration;
- CSV export hardening;
- cover-letter DOCX construction;
- the end-to-end `run_pipeline` orchestration function.

Important public functions include `get_client`, `extract_resume_text`,
`extract_resume_text_from_path`, `load_job_posting`, `generate_application_bundle`,
`init_database`, `save_application`, `list_applications`, `get_application`,
`update_status`, `update_artifacts`, `delete_application`, `get_status_history`,
`dashboard_stats`, `export_applications_csv`, `build_cover_letter_docx`, and
`run_pipeline`.

### `app.py`

The Streamlit browser interface. It provides:

- page configuration and the settings sidebar;
- API-key and model configuration;
- privacy messaging;
- the “New analysis” input workflow with explicit consent;
- result tabs for fit analysis, cover letter, resume bullets, interview preparation, and
  details;
- editable/savable cover letters and resume bullets;
- TXT and DOCX cover-letter downloads;
- application-library metrics, search, status filters, inline status editing, and CSV export;
- reopening saved applications, inspecting status history, and confirmed deletion;
- Streamlit session-state handling for current results and flash messages.

### `job_application_assistant.py`

The argparse command-line interface. It can:

- run a new resume/job analysis and save it;
- list saved applications with optional search and status filter;
- show a saved application as JSON while omitting the full stored job text;
- update an application status with an optional note;
- print fit analysis, cover letter, bullet suggestions, interview questions, application ID,
  database path, and token usage.

### `tests/test_core.py`

Engine-level tests. They use disposable SQLite databases and mocked AI responses, and make no
live OpenAI calls. Each test pins `DATABASE_URL` to empty so a configured Postgres database is
never written to by the suite. Covered behavior includes:

- TXT normalization;
- unsupported resume-format rejection;
- DOCX paragraph and table extraction;
- structured-schema score validation;
- database create/read/update/delete behavior and status history;
- one-time legacy CSV migration and status normalization;
- CSV formula-injection protection, including whitespace-prefixed values;
- complete filtered CSV export beyond the UI display limit;
- cover-letter paragraph preservation through save, reload, and DOCX export;
- DOCX export of the current edited cover letter;
- structured Responses API use with provider-side storage disabled;
- rejection of unsafe/non-HTTP job URLs and malformed URL syntax;
- Postgres dialect translation of placeholders and case-insensitive search;
- mocked driver failures surfacing as `AssistantError` rather than raw exceptions.

### `tests/test_app.py`

Streamlit interaction tests built on `streamlit.testing.v1.AppTest`, which exercises app
behavior without a browser. They cover clearing the API-key field, saves refreshing other
views and dashboard counts, unsaved edits surviving unrelated reruns, and database failures
being displayed instead of crashing the page.

### `check_database.py`

A standalone connectivity check. It runs one insert, read, status update, search, and delete
against whichever engine is configured, then reports the result and removes its own row. It
names the active engine explicitly and states plainly when a passing run only exercised the
local SQLite file, so a hosted database is never assumed to have been verified.

### Configuration and dependency files

- `requirements.txt`: runtime Python dependencies.
- `requirements-dev.txt`: runtime requirements plus pytest and Ruff.
- `pyproject.toml`: pytest discovery/options and Ruff configuration.
- `.env.example`: safe configuration template; the real `.env` is private.
- `.gitignore`: excludes secrets, virtual environments, caches, local databases, tracker
  data, resumes, and generated PDF/DOCX material.
- `.gitattributes`: normalizes line endings, using LF for project text formats.
- `README.md`: concise user-facing setup, usage, architecture, privacy, migration, and
  development instructions.

### `Documents/`

Contains project-specific and sample academic material:

- `Internship_Report_Job_Application_Assistant.docx`: an internship-report draft with many
  identity/company placeholders and some descriptions of an older implementation.
- `Internship_Presentation_Job_Application_Assistant.pptx`: a project-specific presentation
  containing academic attribution and an overview of the earlier version.
- `Sample Internship Report CE_CSE_CSE-AIML_ICT.docx` and `.pdf`: institutional samples;
  use them only for structure and formatting, not project facts.
- `Sample ppt for Internship Presentation.pptx`: a presentation-format sample; do not treat
  its content as project facts.

Local `.env`, `applications_tracker.csv`, and `job_applications.db` files may exist in a
working copy but are private/generated data and are intentionally ignored by Git. Their
contents are not part of the canonical project description.

## 10. AI generation contract

### Provider and API

- Provider: OpenAI
- API style: Responses API structured parsing through `client.responses.parse`
- Default model: `gpt-4o`, overridable through `OPENAI_MODEL` or the UI/CLI
- Client retries: two
- Default request timeout: 90 seconds
- Response storage: disabled for the request with `store=False`

The chosen model must support Structured Outputs in the Responses API. Model names are
restricted to 1–100 characters: an alphanumeric first character followed only by
alphanumeric characters, `.`, `_`, `:`, or `-`.

### Model instructions and integrity policy

The system instructions define the resume and job posting as untrusted source data and tell
the model not to follow instructions embedded in either document. They require the model to:

- use only facts and achievements present in the resume;
- never invent experience, metrics, employers, titles, education, or skills;
- quote exact source evidence for every rewritten resume bullet;
- mark absent job requirements as partial or missing instead of implying experience;
- treat the score as a transparent fit estimate rather than an objective ATS score;
- distinguish must-have from preferred requirements;
- use concise, specific, professional language without generic filler.

### Structured output schema

The top-level `ApplicationBundle` forbids unknown fields and contains:

```text
ApplicationBundle
├── analysis: MatchAnalysis
│   ├── match_score: integer, 0..100
│   ├── matched_skills: list, maximum 30
│   ├── missing_skills: list, maximum 30
│   ├── seniority_fit: under | matched | over
│   ├── notes: 1..1200 characters
│   └── requirements: list, maximum 20
│       ├── requirement: 1..300 characters
│       ├── importance: must-have | preferred
│       ├── evidence: 1..600 characters
│       ├── fit: matched | partial | missing
│       ├── confidence: integer, 0..100
│       └── action: 1..400 characters
├── cover_letter: 100..7000 characters
├── suggested_bullets: 1..5 items
│   ├── original_evidence: 1..700 characters
│   ├── suggested_bullet: 1..700 characters
│   └── reason: 1..400 characters
└── interview_questions: 4..8 items
    ├── question: 1..500 characters
    ├── category: technical | behavioural | role-specific
    └── tip: 1..700 characters
```

All string fields are stripped of surrounding whitespace. Unexpected model fields are
rejected.

## 11. Data model and persistence

### Storage approach

The storage engine is selected by `DATABASE_URL`. When it is unset the application uses a
local SQLite database, defaulting to `job_applications.db`; when it holds a connection string
the application uses Postgres instead. Both engines share the same table definitions, and the
schema is created once per process for each configured target.

SQLite initialization enables foreign keys, a 10-second busy timeout, and write-ahead logging
(WAL). Connections use transactions and are explicitly closed so file handles are released
correctly on Windows.

Postgres uses a small pooled connection set, closed at interpreter exit. Server-side prepared
statements are disabled because managed poolers running PgBouncer cannot carry them across
pooled connections. Call sites are written once in SQLite-flavoured SQL; a connection wrapper
rewrites placeholders to `%s` and `LIKE` to `ILIKE` so search stays case-insensitive on both
engines. The only structural difference between the two schemas is the `application_events`
primary key, which is `AUTOINCREMENT` on SQLite and a generated identity column on Postgres.

Hosted deployment requires Postgres. A platform with an ephemeral filesystem, such as
Streamlit Community Cloud, discards a SQLite file on every restart, which would silently lose
every saved application. The sidebar names the active engine so this cannot pass unnoticed.

### `metadata` table

Stores one-time internal flags as key/value text, currently including the timestamped
`legacy_csv_migrated` marker.

### `applications` table

Each record contains:

- UUID `id`;
- UTC ISO-8601 `created_at` and `updated_at` timestamps;
- company and role;
- job URL, source, and location;
- resume filename and SHA-256 resume-text hash;
- complete job-posting text;
- status;
- match score, seniority fit, and analysis notes;
- full analysis JSON;
- cover letter;
- bullet-suggestion JSON;
- interview-question JSON;
- selected model;
- input, output, and total token counts.

Indexes support status filtering and newest-first creation-date listing.

### `application_events` table

Records status history with an integer ID, application UUID, UTC occurrence time, previous
status, new status, and note. It has a foreign key to `applications` with cascading deletion.

### Resume privacy detail

The raw resume text is used in memory for analysis and hashing but is not inserted into the
database. The saved filename and content hash allow the user to identify which resume version
was used without retaining the resume body locally in this application.

### Legacy CSV migration

On the first database initialization, the application checks for the configured legacy
`applications_tracker.csv` file. If present, each row is imported once. A date in
`YYYY-MM-DD` form becomes a midnight UTC timestamp; missing or invalid dates use the current
UTC time. The old `interview` status is converted to `interviewing`; unknown statuses become
`drafted`; invalid match scores become null. Each import receives a new UUID and a status
event marked “Imported from CSV.” The source CSV is left untouched, and a metadata flag
prevents repeated migration.

## 12. Web-interface behavior

### Settings sidebar

- If `OPENAI_API_KEY` exists on the server, the UI reports that it is configured and does not
  copy it to browser session state.
- Otherwise, a password input accepts an API key for the current local browser session.
- A model text input defaults to the configured model.
- Privacy captions explain that resume and job text are sent to OpenAI, response storage is
  disabled, resume text is not saved to the database, and generated content/job details are
  stored in the configured database. The caption names whether that is hosted Postgres or the
  local SQLite file, and the SQLite path is shown only in the local case.
- A storage caption names the active engine, and a warning appears if a server is running on
  SQLite, where the filesystem may not persist across restarts.

### New analysis tab

The form collects company, role, optional job URL/source/location, resume, and job posting.
The user must tick a consent checkbox before generation. On success, the new application is
saved, loaded into session state, and displayed in the result workspace.

### Result workspace

The result header identifies the role and company and offers status selection. Five tabs show:

1. **Fit analysis** — score, seniority fit, gap count, warning for scores below 40, summary,
   matched/missing skills, and requirement-evidence table.
2. **Cover letter** — editable text, explicit save action, and TXT/DOCX downloads.
3. **Resume bullets** — editable suggested bullets with locked source evidence and rationale.
4. **Interview prep** — numbered questions, categories, and preparation tips.
5. **Details** — application ID, status, metadata, model, token counts, original job posting,
   and status history.

### Applications tab

Shows dashboard metrics, text search, status filtering, an editable status table, CSV export,
saved-application selection, full result reopening, and confirmed deletion.

## 13. Command-line interface

### Run a new analysis

```bash
python job_application_assistant.py \
  --resume resume.pdf \
  --job job-posting.txt \
  --company "Acme Corp" \
  --role "Backend Engineer" \
  --job-url "https://example.com/jobs/123" \
  --source "Referral" \
  --location "Remote"
```

Required analysis options are `--resume`, `--job`, `--company`, and `--role`. The `--job`
argument may be literal job text or a path to a TXT/Markdown file. `--model` overrides the
default model.

### Manage saved applications

```bash
python job_application_assistant.py --show-tracker
python job_application_assistant.py --show-tracker --search "Acme"
python job_application_assistant.py --show-tracker --filter-status interviewing
python job_application_assistant.py --show APPLICATION_ID
python job_application_assistant.py --set-status APPLICATION_ID applied
python job_application_assistant.py --set-status APPLICATION_ID interviewing \
  --status-note "Technical interview scheduled"
```

The CLI returns exit code 0 for success and 1 for handled application errors.

## 14. Configuration

Create `.env` from `.env.example`. Never commit the real file.

| Variable | Default | Purpose |
|---|---:|---|
| `OPENAI_API_KEY` | none | Required OpenAI credential; may instead be entered in the local UI session |
| `OPENAI_MODEL` | `gpt-4o` | Default Structured-Outputs-capable model |
| `DATABASE_URL` | none | Postgres connection string; when set it replaces SQLite. Required for hosted deployment |
| `DATABASE_FILE` | `job_applications.db` | Local SQLite database path, used when `DATABASE_URL` is unset |
| `TRACKER_FILE` | `applications_tracker.csv` | Legacy CSV source used for one-time import |
| `MAX_FILE_BYTES` | `5242880` | Maximum resume/job-file size in bytes |
| `MAX_PDF_PAGES` | `25` | Maximum number of PDF resume pages |
| `MAX_RESUME_CHARS` | `60000` | Maximum normalized resume length |
| `MAX_JOB_CHARS` | `60000` | Maximum normalized job-posting length |
| `OPENAI_TIMEOUT_SECONDS` | `90` | OpenAI request timeout in seconds |

The 25 MiB maximum expanded DOCX size is a code constant rather than an environment setting.

## 15. Technology stack and dependencies

### Runtime

- Python 3.10 or newer
- Streamlit 1.59 to below 2.0 — interactive browser UI
- OpenAI Python SDK 2.44 to below 3.0 — Responses API and Structured Outputs
- pdfplumber 0.11 to below 1.0 — PDF text extraction
- python-docx 1.2 to below 2.0 — DOCX parsing and cover-letter export
- pandas 2.2 to below 4.0 — editable/displayed tables in Streamlit
- python-dotenv 1.0 to below 2.0 — local environment loading
- Pydantic 2.8 to below 3.0 — strict structured-output and edit validation
- psycopg 3.2 to below 4.0 (binary extra) and psycopg-pool 3.2 to below 4.0 — Postgres driver
  and connection pooling, imported only when `DATABASE_URL` is set
- Python standard library components including argparse, atexit, contextlib, csv, hashlib,
  sqlite3, zipfile, pathlib, urllib, uuid, and datetime

### Development

- pytest 8.3 to below 10
- Ruff 0.9 to below 1
- `unittest` is also supported and is used directly by the test module.

### Tooling configuration

- pytest searches `tests/` and runs quietly by default.
- Ruff targets Python 3.10 with a 100-character line length.
- Enabled Ruff rule families: pycodestyle errors, Pyflakes, import sorting, pyupgrade,
  bugbear, and simplify.
- Ruff ignores E501 globally and S101 in tests. The S101 test ignore is retained even though
  the currently selected lint families do not explicitly include Bandit’s `S` rules.

## 16. Setup, run, and verification

### Environment setup

```bash
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Activate on macOS/Linux:

```bash
source .venv/bin/activate
```

Install runtime dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then replace the example key with a real private OpenAI API
key. Leave `DATABASE_URL` unset to use the local SQLite file. To use Postgres, set it to a
connection string and confirm the connection before relying on it:

```bash
python check_database.py
```

The script names the engine it tested, so a passing run against SQLite is not mistaken for a
verified hosted database.

### Run the web application

```bash
python -m streamlit run app.py
```

### Run tests

```bash
python -m unittest discover -s tests -v
# or
python -m pytest
```

### Run linting

```bash
python -m ruff check .
```

Verification on 5 September 2026: **all 30 automated tests passed and Ruff reported no
issues**. The suite covers the engine and, through `streamlit.testing.v1.AppTest`, Streamlit
interaction behavior without a browser.

Postgres was verified separately by running `check_database.py` against a live hosted
database. The automated suite itself never touches a configured Postgres database; its
Postgres coverage is dialect translation and mocked driver failures, which does not establish
live backend compatibility. A disposable Postgres service in CI remains a follow-up item.

## 17. Privacy, security, safety, and responsible AI

### Privacy controls

- The web UI requires affirmative consent before sending resume and job text to OpenAI.
- The OpenAI request disables response storage, although provider-level API retention
  policies may still apply.
- Resume text is processed in memory and not stored in the application database.
- Server-configured API keys remain server-side and are not copied into page/session state.
- `.env`, databases, tracker CSV files, resumes, and generated document files are excluded
  from Git.

### Input and output safety

- File type, size, PDF page count, DOCX expanded size, encoding, extracted-text length, field
  length, URL scheme, and model-name format are validated.
- Resume and job text are explicitly treated as untrusted data in the model instructions,
  reducing prompt-injection risk from uploaded content.
- Structured outputs reject unknown fields and invalid values.
- CSV cells with formula-like prefixes are neutralized.
- Database queries use bound parameters for user values. The only dynamically constructed SQL
  fragments come from internal allowlisted update/search logic.
- The application exposes friendly errors for authentication rejection, rate limiting,
  timeout, connection failure, provider status errors, response validation failures, parsing
  problems, and database errors.

### Human control

- The model output is a draft and decision-support aid.
- Users can inspect evidence, edit materials, and choose whether to use them.
- The system never applies to a job, sends a cover letter, or changes an external account.
- Users should review every generated claim before submission.

### Deployment warning

The application can be hosted, and Postgres support exists so that hosted data survives
restarts, but nothing about hosting makes it multi-user. There is no login and no per-user
ownership check on any query, so everyone who can open a deployed instance shares one
database and sees the same applications. Configuring a server-side `OPENAI_API_KEY` also
hides the key field, so every visitor generates on that one credential.

A hosted instance therefore remains a personal deployment, and access should be restricted to
the owner. Turning it into a public multi-user service requires authentication, per-user
ownership enforced across all queries, encrypted storage, secret management, quotas and rate
controls, audit controls, and a deployment-specific privacy policy.

## 18. Error handling

The shared `AssistantError` type represents safe messages that can be shown in either UI.
Notable handled conditions include:

- missing/rejected API key;
- unsupported or corrupt resume;
- oversized file, PDF, or normalized text;
- unreadable scanned PDF requiring OCR;
- non-UTF-8 TXT resume;
- invalid company, role, URL, status, or model name;
- OpenAI authentication, rate-limit, timeout, connection, and status errors;
- missing or schema-invalid model output;
- database initialization, read, write, and edit failures on either engine, including a
  Postgres connection that cannot be reached and a database directory that cannot be created;
- invalid edited artifacts or nonexistent application IDs;
- legacy CSV read/migration failure, including non-UTF-8 tracker files.

Driver-level exceptions from SQLite and psycopg are converted into `AssistantError` so raw
database errors are never shown to the user, and the affected UI sections render the message
instead of crashing the page.

The OpenAI timeout message notes that user inputs are preserved for retrying in the active UI
session.

## 19. Current limitations

- A fit estimate is model-generated and may vary; it is not an objective measurement.
- The application depends on a valid OpenAI API key, network access, provider availability,
  and a model supporting the required Structured Outputs schema.
- A single structured request can be costly for long resumes and job descriptions, although
  token usage is recorded.
- Image-only PDF resumes are rejected because OCR is not implemented.
- PDF parsing quality depends on the PDF’s embedded text and layout.
- Job URLs are validated and stored but not fetched.
- The database is single-user. It can be hosted, but there is no login and no per-user
  ownership check, so everyone with access to a deployed instance shares the same records.
- Resume content is not retained, so reopening an old application shows generated content and
  the stored job posting but cannot reproduce the source resume text from the database.
- Only the cover letter has a document download; resume-bullet and interview-prep document
  exports are not implemented.
- Cover letters can be downloaded as TXT or DOCX, not PDF.
- There is no automated end-to-end browser test, performance/load test, accessibility audit,
  or live-API integration test in the repository. Streamlit behavior is covered by AppTest,
  which runs without a browser and so validates behavior rather than appearance.
- No automated test runs against a live Postgres database. Postgres coverage in the suite is
  dialect translation and mocked driver failures; live compatibility is checked manually with
  `check_database.py`.
- A complete CSV export loads all matching applications into memory, so a very large library
  will be slower and heavier to export than the paged UI suggests.
- Application deletion is permanent within the app and has no recycle bin.
- Search covers company, role, and notes, not every stored field.
- The application has no explicit database schema-version migration framework beyond the
  one-time legacy CSV import.

## 20. Future enhancement opportunities

Reasonable future work, clearly described as not yet implemented, includes:

The [5 September project review](PROJECT_REVIEW.md) ranks the six highest-priority items,
led by draft recovery after a save failure, backup and schema migrations, concurrency
hardening, Postgres coverage in CI, pagination for large libraries, and authentication before
any shared hosting. The list below is the broader backlog.

1. Add OCR for scanned resumes.
2. Add exact job-keyword extraction and highlight missing keywords with evidence-aware advice.
3. Support optional local/open-source or additional hosted model providers.
4. Add PDF export and unified export packages for letters, bullets, analysis, and interview
   preparation.
5. Add application analytics such as response rate, interview conversion, source
   effectiveness, and time-in-status.
6. Add reminders, follow-up dates, and calendar integration.
7. Add encrypted backups or user-controlled cloud synchronization.
8. Add authenticated multi-user architecture only with per-user isolation and a full privacy
   and security design.
9. Add database schema migrations, backup/restore, and recovery tooling.
10. Add automated browser, accessibility, integration, and property-based security tests.
11. Add optional job-description import from a URL with SSRF-safe fetching and explicit user
    consent.
12. Add version comparison so users can see how edits changed generated materials.

## 21. Historical-material corrections

The internship report and presentation describe an earlier version. When writing new
documents, apply these corrections:

| Older statement | Current verified implementation |
|---|---|
| Applications are stored in a CSV tracker. | A SQL database is the store: SQLite by default, Postgres when `DATABASE_URL` is set. CSV is used only for one-time legacy import and export. |
| Re-running a job upserts the same CSV row. | Each completed generation creates a new UUID application record; there is no job-based upsert/deduplication. |
| Status flow is `drafted → applied → interview → offer/rejected`. | Nine statuses exist: saved, drafted, applied, assessment, interviewing, offer, rejected, withdrawn, archived. |
| Interview prep produces 5–6 questions. | The validated schema requires 4–8 questions. |
| Match output is simple JSON that tolerates markdown fences. | The current OpenAI call uses strict Pydantic Structured Outputs via `responses.parse`. |
| DOCX/PDF download is future work. | TXT and formatted DOCX cover-letter downloads are implemented; PDF export is still future work. |
| A database, search, and analytics dashboard are future work. | SQLite, search, status filters, application counts, reopening, status history, and CSV export are implemented. |
| The pipeline is described as separate score/draft/bullets/questions model stages. | Parsing is separate, but the AI analysis and all generated materials come from one structured model request. |
| pandas/csv provide the application tracker. | pandas supports web tables/editors; SQLite implements the tracker; `csv` supports migration/export. |
| The AI model is fixed and cannot be changed. | The default is `gpt-4o`; any valid Structured-Outputs-capable model can be configured. |

These corrections matter because the current repository has already implemented several
items labeled as “future enhancement” in the older report.

## 22. Outcomes and learning

The project demonstrates how to turn an AI-writing concept into a safer, maintainable
application by combining model grounding with conventional software controls. Its important
engineering outcomes are:

- one shared core for two front ends;
- strict typed AI outputs instead of loosely parsed prose/JSON;
- evidence-linked resume suggestions;
- explicit prompt-injection boundaries for uploaded content;
- local transactional persistence with history;
- clear privacy boundaries around raw resume text;
- editable human-reviewed outputs rather than autonomous submission;
- defensive parsing, validation, and export handling;
- tests that exercise core behavior without spending API tokens.

Skills demonstrated by the project include Python application design, prompt engineering,
OpenAI Responses API integration, Pydantic data modeling, PDF/DOCX parsing, Streamlit UI
development, CLI design, SQLite schema and transaction management, migration logic, document
generation, privacy-aware design, secure CSV export, error handling, and automated testing.

Do not claim measured time savings, match accuracy, ATS improvements, absence of hallucination
across all inputs, user-study results, production usage, application counts, or hiring outcomes
unless separate evidence is supplied. The existing academic report’s statement that testing
produced “consistent” results is qualitative and should not be converted into a numerical
performance claim.

## 23. Suggested demonstration script

1. Start the Streamlit app and show the settings/privacy sidebar.
2. Enter company, role, source, location, and a valid job URL.
3. Upload a text-based PDF/DOCX/TXT resume and paste a complete job posting.
4. Point out the explicit consent checkbox before analysis.
5. Generate the workspace and explain that one validated model response produced all results.
6. Show the fit score as an estimate, then inspect matched skills, gaps, seniority fit, and the
   requirement-evidence table.
7. Open the cover-letter tab, make a small edit, save it, and download the current edit as
   DOCX.
8. Show a resume suggestion beside its locked original evidence.
9. Review interview questions and preparation tips.
10. Change the application status and inspect the recorded history.
11. Open the Applications tab, show metrics/search/filtering, and export filtered CSV.
12. Close by emphasizing that raw resume text is not stored and the tool never auto-applies.

## 24. Writing guidance for future documents

### Preferred framing

Use these phrases:

- “evidence-led fit estimate” instead of “accurate ATS score”;
- “AI-assisted draft” instead of “automatically perfect document”;
- “grounded in resume evidence” instead of “guaranteed hallucination-free”;
- “single-user personal workspace, optionally self-hosted” instead of “production SaaS
  platform”, since hosting adds persistence but not multi-tenancy;
- “supports application preparation and tracking” instead of “applies to jobs”;
- “response storage is disabled for generation requests” instead of “OpenAI stores no data”;
- “resume text is not persisted by the application” instead of “no personal data is stored,”
  because job data, generated materials, resume filename, and resume hash are stored in the
  configured database, which may be hosted rather than local.

### Facts that must remain consistent

- Current storage: SQLite by default, Postgres when `DATABASE_URL` is set
- Hosted deployment: requires Postgres, because an ephemeral filesystem discards SQLite
- Legacy data: optional one-time CSV import, applied to the local SQLite file only
- Interfaces: Streamlit web UI and command-line interface
- Resume formats: PDF, DOCX, UTF-8 TXT
- Job file formats in CLI: TXT and Markdown
- Default model: `gpt-4o`, configurable
- AI response method: one strict structured `ApplicationBundle`
- Fit score: 0–100 estimate, not an objective ATS score
- Low-fit warning threshold: below 40
- Interview questions: 4–8
- Resume-bullet suggestions: 1–5
- New application status: `drafted`
- Raw resume text: processed in memory, not saved to the database
- Saved resume identifiers: basename and SHA-256 hash
- Stored content: job details/text, generated artifacts, analysis, model, token usage, history
- OpenAI request storage: disabled
- Exports: cover-letter TXT/DOCX and application CSV
- Auto-submission: not implemented and intentionally outside scope
- Verified tests: 30 passing on 5 September 2026
- Verified lint status: Ruff reports no issues as of 5 September 2026
- Live Postgres: verified by `check_database.py`, not by the automated suite

### Citation/reference starting points for academic documents

The older report lists these relevant official/project references. Verify current URLs and
access dates before formal submission:

- OpenAI API documentation
- Streamlit documentation
- Python official documentation
- pdfplumber project documentation/repository
- python-docx documentation
- pandas documentation
- Pydantic documentation
- SQLite documentation

Do not cite the sample internship documents as technical evidence about this project.

## 25. Glossary

- **ATS:** Applicant Tracking System. In this project, ATS is contextual background only; the
  generated fit estimate does not reproduce a specific ATS algorithm.
- **LLM:** Large Language Model, used here for analysis and drafting.
- **Structured Outputs:** Model output constrained to a developer-provided schema and parsed
  into typed Pydantic objects.
- **Grounding:** Restricting generated claims to evidence contained in the supplied resume.
- **Requirement evidence:** A record connecting a job requirement with resume evidence, fit,
  confidence, and recommended action.
- **Local-first:** Application data is primarily stored on the user’s local machine rather
  than in an application-owned cloud service.
- **WAL:** SQLite write-ahead logging, used to improve database reliability/concurrency.
- **Formula injection:** The risk that spreadsheet software interprets exported text as a
  formula; the CSV exporter neutralizes common formula prefixes.
- **Resume hash:** A SHA-256 digest of normalized resume text used to identify the analyzed
  resume version without storing the text itself.

## 26. Canonical summary

The Job Application Workspace is a responsible-AI job-application preparation tool built in
Python, local-first by default and deployable against hosted Postgres. Its Streamlit and CLI
interfaces share `core.py`, which validates and parses resumes, makes one structured OpenAI
Responses API request, validates the result with Pydantic, stores the application workspace
and status history in SQLite or Postgres, and provides secure exports. It accepts PDF, DOCX, and UTF-8 TXT resumes; produces evidence-led fit analysis,
grounded cover letters, traceable resume-bullet rewrites, and interview preparation; and lets
the user edit, search, filter, export, and track applications. It is not an ATS, does not
guarantee hiring outcomes, does not store raw resume text in its database, and never submits
applications. The current implementation supersedes the earlier CSV-based version described
in the internship report and presentation.
