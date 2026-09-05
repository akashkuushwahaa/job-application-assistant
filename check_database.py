"""Verify that the configured database works end to end.

Run this once after setting DATABASE_URL (locally or as a Streamlit secret) to
confirm the hosted Postgres schema, writes, reads, and deletes all work:

    python check_database.py

It creates one throwaway application, reads it back, and deletes it again.
"""

from __future__ import annotations

import sys

import core


def _sample_bundle() -> core.ApplicationBundle:
    return core.ApplicationBundle(
        analysis={
            "match_score": 71,
            "matched_skills": ["Python"],
            "missing_skills": ["Kubernetes"],
            "seniority_fit": "matched",
            "notes": "Connectivity check only.",
            "requirements": [
                {
                    "requirement": "Write Python",
                    "importance": "must-have",
                    "evidence": "Wrote Python services.",
                    "fit": "matched",
                    "confidence": 90,
                    "action": "Mention the Python services.",
                }
            ],
        },
        cover_letter=(
            "This row was created by check_database.py to verify database connectivity. "
            "It is deleted again before the script finishes.\n\n"
            "If you are reading this in the application list, the cleanup step did not run."
        ),
        suggested_bullets=[
            {
                "original_evidence": "Wrote Python services.",
                "suggested_bullet": "Shipped Python services to production.",
                "reason": "Connectivity check only.",
            }
        ],
        interview_questions=[
            {
                "question": f"Connectivity check question {number}?",
                "category": "technical",
                "tip": "Not a real question.",
            }
            for number in range(1, 5)
        ],
    )


def main() -> int:
    engine = "Postgres" if core.use_postgres() else f"SQLite ({core.DATABASE_FILE})"
    print(f"Engine:  {engine}")
    if core.use_postgres():
        # Never print the URL itself; it carries the password.
        host = core.DATABASE_URL.split("@")[-1].split("/")[0]
        print(f"Host:    {host}")

    application_id = ""
    try:
        core.init_database()
        print("Schema:  ok")

        before = len(core.list_applications())
        application_id = core.save_application(
            company="Connectivity Check",
            role="Temporary Row",
            job_text="Temporary row written by check_database.py.",
            bundle=_sample_bundle(),
            model=core.DEFAULT_MODEL,
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        )
        print(f"Insert:  ok ({application_id})")

        saved = core.get_application(application_id)
        assert saved is not None and saved["company"] == "Connectivity Check"
        print("Read:    ok")

        core.update_status(application_id, "applied", "Connectivity check")
        history = core.get_status_history(application_id)
        assert len(history) == 2, f"expected 2 history rows, got {len(history)}"
        print("Update:  ok (status history cascade works)")

        matches = core.list_applications(search="connectivity check")
        assert any(item["id"] == application_id for item in matches), "case-insensitive search failed"
        print("Search:  ok (case-insensitive)")

        core.delete_application(application_id)
        application_id = ""
        assert len(core.list_applications()) == before
        print("Delete:  ok")
    except Exception as exc:  # noqa: BLE001
        print(f"\nFAILED: {type(exc).__name__}: {exc}")
        if application_id:
            try:
                core.delete_application(application_id)
                print(f"Cleaned up leftover row {application_id}.")
            except Exception:  # noqa: BLE001
                print(f"Could not clean up row {application_id}; delete it manually.")
        return 1

    if core.use_postgres():
        print("\nAll checks passed. Postgres persistence is working.")
    else:
        print(
            "\nAll checks passed, but this tested the LOCAL SQLITE FILE.\n"
            "DATABASE_URL is not set, so nothing about the hosted database was\n"
            "verified. Set DATABASE_URL and run this again before deploying."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
