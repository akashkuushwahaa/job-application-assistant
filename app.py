"""Streamlit interface for the Job Application Assistant."""

from __future__ import annotations

import os
import re

import pandas as pd
import streamlit as st

import core


st.set_page_config(
    page_title="Job Application Workspace",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return cleaned[:60] or "application"


def _application_id(result: dict) -> str:
    return str(result.get("application_id") or result.get("id") or "current")


def _is_hosted() -> bool:
    """True when running on a server rather than a developer machine."""
    return bool(os.environ.get("HOSTNAME") or os.environ.get("STREAMLIT_SERVER_HEADLESS"))


def _show_flash() -> None:
    message = st.session_state.pop("flash", None)
    if message:
        st.success(message)


def _render_storage_status() -> None:
    """Make the active storage engine visible.

    A hosted deployment that silently falls back to SQLite would lose every
    saved application on the next restart, so surface that rather than hide it.
    """
    if core.use_postgres():
        st.caption("Storage: hosted Postgres.")
    elif _is_hosted():
        st.warning(
            "DATABASE_URL is not set, so this deployment is writing to a temporary "
            "file that is erased when the app restarts. Saved applications will be "
            "lost. Set DATABASE_URL in the app secrets."
        )
    else:
        st.caption(f"Storage: local file ({core.DATABASE_FILE}).")


def render_settings() -> None:
    with st.sidebar:
        st.header("Settings")
        if core.has_server_api_key():
            st.session_state.pop("api_key", None)
            st.success("Server API key configured.")
            st.caption("The key remains on the server and is never placed in this page.")
        else:
            key = st.text_input(
                "OpenAI API key",
                type="password",
                value="",
                help="Used only for this local browser session. Prefer OPENAI_API_KEY.",
            )
            if key:
                st.session_state["api_key"] = key

        _render_storage_status()

        st.session_state["model"] = st.text_input(
            "Model",
            value=st.session_state.get("model", core.DEFAULT_MODEL),
            help="The model must support Structured Outputs in the Responses API.",
            max_chars=100,
        )

        st.divider()
        st.subheader("Privacy")
        st.caption(
            "Resume and job text are sent to OpenAI with response storage disabled. "
            "Resume text is processed in memory and is not saved locally. Generated "
            "materials and job details are stored in your local SQLite database."
        )
        st.caption(f"Database: {core.DATABASE_FILE}")


def render_analysis(analysis: dict) -> None:
    score = int(analysis.get("match_score", 0))
    metric_columns = st.columns(3)
    metric_columns[0].metric("Fit estimate", f"{score}/100")
    metric_columns[1].metric("Seniority fit", analysis.get("seniority_fit", "—"))
    metric_columns[2].metric("Missing skills", len(analysis.get("missing_skills", [])))

    if score < 40:
        st.warning("This appears to be a low-fit role. Review the missing must-haves before applying.")
    st.write(analysis.get("notes", "No summary was generated."))

    matched, missing = st.columns(2)
    with matched:
        st.subheader("Matched skills")
        skills = analysis.get("matched_skills", [])
        if skills:
            for skill in skills:
                st.markdown(f"- {skill}")
        else:
            st.caption("No explicit matches were identified.")
    with missing:
        st.subheader("Missing skills")
        skills = analysis.get("missing_skills", [])
        if skills:
            for skill in skills:
                st.markdown(f"- {skill}")
        else:
            st.caption("No explicit gaps were identified.")

    requirements = analysis.get("requirements", [])
    st.subheader("Requirement evidence")
    if requirements:
        table = pd.DataFrame(requirements)
        table = table.rename(
            columns={
                "requirement": "Requirement",
                "importance": "Importance",
                "evidence": "Resume evidence",
                "fit": "Fit",
                "confidence": "Confidence",
                "action": "Recommended action",
            }
        )
        st.dataframe(table, hide_index=True, use_container_width=True)
    else:
        st.info("This older application does not contain requirement-level evidence.")


def render_results(result: dict, *, prefix: str) -> None:
    application_id = _application_id(result)
    company = result.get("company", "Company")
    role = result.get("role", "Role")
    st.subheader(f"{role} at {company}")

    status_key = f"{prefix}_status_{application_id}"
    current_status = result.get("status", "drafted")
    if status_key not in st.session_state:
        st.session_state[status_key] = (
            current_status if current_status in core.STATUSES else "drafted"
        )
    status_col, action_col = st.columns([3, 1])
    with status_col:
        selected_status = st.selectbox(
            "Application status",
            core.STATUSES,
            key=status_key,
        )
    with action_col:
        st.write("")
        st.write("")
        if st.button("Save status", key=f"{prefix}_save_status_{application_id}"):
            try:
                core.update_status(application_id, selected_status)
                result["status"] = selected_status
                st.success("Status saved.")
            except core.AssistantError as exc:
                st.error(str(exc))

    analysis_tab, letter_tab, bullets_tab, interview_tab, details_tab = st.tabs(
        ["Fit analysis", "Cover letter", "Resume bullets", "Interview prep", "Details"]
    )

    with analysis_tab:
        render_analysis(result.get("analysis", {}))

    with letter_tab:
        letter_key = f"{prefix}_letter_{application_id}"
        if letter_key not in st.session_state:
            st.session_state[letter_key] = result.get("cover_letter", "")
        edited_letter = st.text_area(
            "Editable cover letter",
            key=letter_key,
            height=360,
            help="Your edits are saved only when you choose Save cover letter.",
        )
        save_col, txt_col, docx_col = st.columns([2, 1, 1])
        with save_col:
            if st.button("Save cover letter", key=f"{prefix}_save_letter_{application_id}"):
                try:
                    core.update_artifacts(application_id, cover_letter=edited_letter)
                    result["cover_letter"] = edited_letter
                    st.success("Cover letter saved.")
                except core.AssistantError as exc:
                    st.error(str(exc))
        filename = f"{_slug(company)}-{_slug(role)}-cover-letter"
        with txt_col:
            st.download_button(
                "Download TXT",
                edited_letter,
                f"{filename}.txt",
                mime="text/plain",
                key=f"{prefix}_txt_{application_id}",
            )
        with docx_col:
            try:
                docx_data = core.build_cover_letter_docx(edited_letter, company, role)
                st.download_button(
                    "Download DOCX",
                    docx_data,
                    f"{filename}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"{prefix}_docx_{application_id}",
                )
            except core.AssistantError as exc:
                st.error(str(exc))

    with bullets_tab:
        bullets = result.get("suggested_bullets", [])
        if bullets:
            bullet_frame = pd.DataFrame(bullets)
            edited_frame = st.data_editor(
                bullet_frame,
                hide_index=True,
                use_container_width=True,
                disabled=["original_evidence", "reason"],
                column_config={
                    "original_evidence": st.column_config.TextColumn("Original resume evidence"),
                    "suggested_bullet": st.column_config.TextColumn(
                        "Editable suggested bullet", width="large", required=True
                    ),
                    "reason": st.column_config.TextColumn("Why this helps"),
                },
                key=f"{prefix}_bullets_{application_id}",
            )
            if st.button("Save resume bullets", key=f"{prefix}_save_bullets_{application_id}"):
                try:
                    edited_bullets = edited_frame.to_dict(orient="records")
                    core.update_artifacts(application_id, suggested_bullets=edited_bullets)
                    result["suggested_bullets"] = edited_bullets
                    st.success("Resume bullets saved.")
                except core.AssistantError as exc:
                    st.error(str(exc))
        else:
            st.info("No supported bullet rewrites were generated.")

    with interview_tab:
        questions = result.get("interview_questions", [])
        if questions:
            for index, question in enumerate(questions, start=1):
                st.markdown(
                    f"**{index}. {question.get('question', '')}**  \n"
                    f"Category: {question.get('category', 'role-specific')}"
                )
                st.caption(question.get("tip", ""))
        else:
            st.info("No interview questions are available for this application.")

    with details_tab:
        details = {
            "Application ID": application_id,
            "Status": result.get("status", "drafted"),
            "Job URL": result.get("job_url", "") or "Not provided",
            "Source": result.get("source", "") or "Not provided",
            "Location": result.get("location", "") or "Not provided",
            "Resume file": result.get("resume_name", "") or "Not stored",
            "Model": result.get("model", core.DEFAULT_MODEL),
            "Input tokens": result.get("input_tokens", result.get("usage", {}).get("input_tokens", 0)),
            "Output tokens": result.get("output_tokens", result.get("usage", {}).get("output_tokens", 0)),
        }
        st.dataframe(
            pd.DataFrame(details.items(), columns=["Field", "Value"]),
            hide_index=True,
            use_container_width=True,
        )
        job_text = result.get("job_text", "")
        if job_text:
            with st.expander("Original job posting"):
                st.text(job_text)
        history = core.get_status_history(application_id)
        if history:
            st.subheader("Status history")
            st.dataframe(pd.DataFrame(history), hide_index=True, use_container_width=True)


def render_new_application() -> None:
    st.header("Prepare an application")
    st.write(
        "Upload a resume and add a job description. The analysis shows the evidence "
        "behind its fit estimate and saves the resulting workspace locally."
    )

    with st.form("new_application_form", clear_on_submit=False):
        identity_columns = st.columns(2)
        company = identity_columns[0].text_input("Company *", max_chars=200)
        role = identity_columns[1].text_input("Role title *", max_chars=200)

        detail_columns = st.columns(3)
        job_url = detail_columns[0].text_input(
            "Job URL", placeholder="https://company.example/jobs/123", max_chars=2_000
        )
        source = detail_columns[1].text_input(
            "Source", placeholder="LinkedIn, referral, careers page", max_chars=200
        )
        location = detail_columns[2].text_input(
            "Location", placeholder="Remote, Bengaluru, London", max_chars=200
        )

        resume = st.file_uploader(
            "Resume *",
            type=["pdf", "docx", "txt"],
            help=f"PDF, DOCX, or UTF-8 TXT up to {core.MAX_FILE_BYTES // 1024 // 1024} MB.",
        )
        job_text = st.text_area(
            "Job posting *",
            height=260,
            max_chars=core.MAX_JOB_CHARS,
            placeholder="Paste the complete responsibilities and requirements here.",
        )
        consent = st.checkbox(
            "I understand that the resume and job posting will be sent to OpenAI for analysis."
        )
        submitted = st.form_submit_button(
            "Analyze and create workspace", type="primary", use_container_width=True
        )

    if submitted:
        errors = []
        if not company.strip():
            errors.append("Enter the company name.")
        if not role.strip():
            errors.append("Enter the role title.")
        if resume is None:
            errors.append("Upload a resume.")
        if not job_text.strip():
            errors.append("Paste the job posting.")
        if not consent:
            errors.append("Confirm the data-processing notice before continuing.")
        if errors:
            for error in errors:
                st.error(error)
        else:
            try:
                with st.spinner("Reading the resume, evaluating fit, and drafting materials…"):
                    resume_bytes = resume.getvalue()
                    resume_text = core.extract_resume_text(resume_bytes, resume.name)
                    client = core.get_client(st.session_state.get("api_key"))
                    result = core.run_pipeline(
                        client,
                        resume_text,
                        job_text,
                        company,
                        role,
                        model=st.session_state.get("model"),
                        resume_name=resume.name,
                        job_url=job_url,
                        source=source,
                        location=location,
                    )
                st.session_state["current_result"] = (
                    core.get_application(result["application_id"]) or result
                )
                st.session_state["flash"] = "Application workspace created and saved."
                st.rerun()
            except core.AssistantError as exc:
                st.error(str(exc))

    current = st.session_state.get("current_result")
    if current:
        st.divider()
        render_results(current, prefix="new")


def render_application_library() -> None:
    st.header("Applications")
    try:
        stats = core.dashboard_stats()
        metric_columns = st.columns(4)
        metric_columns[0].metric("Total", stats["total"])
        metric_columns[1].metric("Applied", stats["applied"])
        metric_columns[2].metric("Active interviews", stats["active_interviews"])
        metric_columns[3].metric("Offers", stats["offers"])

        filter_columns = st.columns([3, 2])
        search = filter_columns[0].text_input(
            "Search applications", placeholder="Company, role, or note"
        )
        status_choice = filter_columns[1].selectbox(
            "Filter by status", ["All", *core.STATUSES]
        )
        applications = core.list_applications(
            search=search,
            status="" if status_choice == "All" else status_choice,
        )
    except core.AssistantError as exc:
        st.error(str(exc))
        return

    if not applications:
        if search or status_choice != "All":
            st.info("No applications match these filters. Clear a filter to see more.")
        else:
            st.info("No applications yet. Create your first workspace in New analysis.")
        return

    rows = [
        {
            "id": item["id"],
            "date": item["created_at"][:10],
            "company": item["company"],
            "role": item["role"],
            "match_score": item.get("match_score"),
            "status": item["status"],
        }
        for item in applications
    ]
    original = pd.DataFrame(rows)
    edited = st.data_editor(
        original,
        hide_index=True,
        use_container_width=True,
        disabled=["id", "date", "company", "role", "match_score"],
        column_config={
            "id": None,
            "status": st.column_config.SelectboxColumn(
                "Status", options=core.STATUSES, required=True
            ),
        },
        key="application_library_editor",
    )
    action_columns = st.columns([2, 1])
    with action_columns[0]:
        if st.button("Save status changes"):
            try:
                original_by_id = {row["id"]: row["status"] for row in rows}
                changed = 0
                for row in edited.to_dict(orient="records"):
                    if row["status"] != original_by_id[row["id"]]:
                        core.update_status(row["id"], row["status"])
                        changed += 1
                st.success(f"Saved {changed} status change{'s' if changed != 1 else ''}.")
            except core.AssistantError as exc:
                st.error(str(exc))
    with action_columns[1]:
        st.download_button(
            "Export filtered CSV",
            core.export_applications_csv(applications),
            "job-applications.csv",
            mime="text/csv",
        )

    labels = {
        item["id"]: f"{item['company']} — {item['role']} ({item['created_at'][:10]})"
        for item in applications
    }
    selected_id = st.selectbox(
        "Open an application",
        list(labels),
        format_func=lambda value: labels[value],
    )
    selected = core.get_application(selected_id)
    if selected:
        st.divider()
        render_results(selected, prefix="library")
        with st.expander("Delete this application"):
            st.warning("Deletion removes the saved materials and status history from this device.")
            confirmed = st.checkbox(
                "I understand this cannot be undone.", key=f"delete_confirm_{selected_id}"
            )
            if st.button(
                "Delete application",
                disabled=not confirmed,
                key=f"delete_{selected_id}",
            ):
                try:
                    core.delete_application(selected_id)
                    if _application_id(st.session_state.get("current_result", {})) == selected_id:
                        st.session_state.pop("current_result", None)
                    st.session_state["flash"] = "Application deleted."
                    st.rerun()
                except core.AssistantError as exc:
                    st.error(str(exc))


render_settings()
st.title("Job Application Workspace")
st.caption("Evidence-led application preparation, truthful drafts, and a tracker you control.")
_show_flash()

try:
    core.init_database()
except core.AssistantError as exc:
    st.error(str(exc))
    st.stop()

new_tab, applications_tab = st.tabs(["New analysis", "Applications"])
with new_tab:
    render_new_application()
with applications_tab:
    render_application_library()
