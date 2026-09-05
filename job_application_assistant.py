"""Command-line interface for the Job Application Assistant."""

from __future__ import annotations

import argparse
import json
import sys

import core


def _configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def cmd_run(args: argparse.Namespace) -> int:
    try:
        resume_text = core.extract_resume_text_from_path(args.resume)
        job_text = core.load_job_posting(args.job)
        client = core.get_client()
        print("Analyzing fit and preparing application materials…")
        result = core.run_pipeline(
            client,
            resume_text,
            job_text,
            args.company,
            args.role,
            model=args.model,
            resume_name=args.resume,
            job_url=args.job_url,
            source=args.source,
            location=args.location,
        )
    except core.AssistantError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 1

    analysis = result["analysis"]
    print("\n--- FIT ANALYSIS ---")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    if analysis["match_score"] < 40:
        print("\nWarning: review the missing must-haves before applying.")

    print("\n--- COVER LETTER ---\n")
    print(result["cover_letter"])

    print("\n--- SUGGESTED RESUME BULLETS ---")
    for item in result["suggested_bullets"]:
        print(f"- {item['suggested_bullet']}")
        print(f"  Evidence: {item['original_evidence']}")

    print("\n--- LIKELY INTERVIEW QUESTIONS ---")
    for question in result["interview_questions"]:
        print(f"[{question['category']}] {question['question']}")
        print(f"  Tip: {question['tip']}")

    usage = result.get("usage", {})
    storage = "Postgres" if core.use_postgres() else core.DATABASE_FILE
    print(f"\nSaved as application {result['application_id']} in {storage}")
    print(f"Token usage: {usage.get('total_tokens', 0)} total")
    return 0


def cmd_show_tracker(args: argparse.Namespace) -> int:
    try:
        rows = core.list_applications(search=args.search, status=args.filter_status)
    except core.AssistantError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if not rows:
        print("No applications found.")
        return 0
    for row in rows:
        print(
            f"{row['id']}  {row['created_at'][:10]}  {row['company']} — {row['role']}  "
            f"[{row['status']}]  score={row.get('match_score', '—')}"
        )
    return 0


def cmd_show_application(application_id: str) -> int:
    try:
        item = core.get_application(application_id)
    except core.AssistantError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if not item:
        print("Application not found.", file=sys.stderr)
        return 1
    item.pop("job_text", None)
    print(json.dumps(item, indent=2, ensure_ascii=False))
    return 0


def cmd_set_status(application_id: str, status: str, note: str) -> int:
    try:
        core.update_status(application_id, status, note)
    except core.AssistantError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Application status updated to {status}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare truthful job-application materials and track applications.",
    )
    parser.add_argument("-r", "--resume", help="Path to a PDF, DOCX, or UTF-8 TXT resume")
    parser.add_argument("-j", "--job", help="Job text or a path to a TXT/Markdown file")
    parser.add_argument("-c", "--company", help="Company name")
    parser.add_argument("-R", "--role", help="Role title")
    parser.add_argument("--job-url", default="", help="Original job posting URL")
    parser.add_argument("--source", default="", help="Where the opportunity was found")
    parser.add_argument("--location", default="", help="Role location or work arrangement")
    parser.add_argument("-m", "--model", default=None, help=f"OpenAI model (default: {core.DEFAULT_MODEL})")
    parser.add_argument("--show-tracker", action="store_true", help="List saved applications")
    parser.add_argument("--search", default="", help="Search company, role, or notes")
    parser.add_argument("--filter-status", choices=core.STATUSES, default="", help="Filter the tracker")
    parser.add_argument("--show", metavar="APPLICATION_ID", help="Show one saved application")
    parser.add_argument("--set-status", nargs=2, metavar=("APPLICATION_ID", "STATUS"), help="Update an application status")
    parser.add_argument("--status-note", default="", help="Optional note for --set-status")
    return parser


def main() -> int:
    _configure_console()
    parser = build_parser()
    args = parser.parse_args()
    if args.show_tracker:
        return cmd_show_tracker(args)
    if args.show:
        return cmd_show_application(args.show)
    if args.set_status:
        application_id, status = args.set_status
        if status not in core.STATUSES:
            parser.error(f"status must be one of: {', '.join(core.STATUSES)}")
        return cmd_set_status(application_id, status, args.status_note)
    if not all([args.resume, args.job, args.company, args.role]):
        parser.error("--resume, --job, --company, and --role are required for analysis")
    return cmd_run(args)


if __name__ == "__main__":
    raise SystemExit(main())
