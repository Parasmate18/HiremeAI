"""
Hiremeai recruiter console.

Setup:
    pip install streamlit requests
    streamlit run app.py

Point it at a different API with HIREMEAI_API_URL (defaults to http://127.0.0.1:8000).
"""

import html
import json
import os
import textwrap

import requests
import streamlit as st

API_URL = os.getenv("HIREMEAI_API_URL", "http://127.0.0.1:8000").rstrip("/")
MAX_UPLOAD_MB = 5
SUGGESTIONS = [
    "What is their strongest skill?",
    "Walk me through the latest role",
    "Which project should I review?",
    "Do they hold any certifications?",
]
AVATARS = {"user": "🧑‍💼", "assistant": "📄"}

st.set_page_config(page_title="Hiremeai", page_icon="📄", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;600;700;800&family=Newsreader:ital,wght@0,400;0,500;1,400&display=swap');

:root {
  --ink: #0F2B3D;
  --paper: #F5F7F4;
  --sheet: #FFFFFF;
  --rule: #D6DED8;
  --text: #13222C;
  --muted: #5C6C74;
  --highlight: #F4C542;
  --teal: #1D7A6E;
  --danger: #B3261E;
}

html, body, .stApp, [data-testid="stMarkdownContainer"] {
  font-family: 'Newsreader', Georgia, serif;
  color: var(--text);
}
.stApp { background: var(--paper); }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1180px; padding-top: 2.5rem; padding-bottom: 4rem; }

h1, h2, h3, h4, .section-title, .xp-role, .hl, .wordmark, .steps strong,
.stButton button, .stTabs [role="tab"] {
  font-family: 'Bricolage Grotesque', system-ui, sans-serif;
}
h1, h2, h3 { color: var(--ink); letter-spacing: -0.02em; }

/* Sidebar */
[data-testid="stSidebar"] { background: #E9EEEA; border-right: 1px solid var(--rule); }
.wordmark { font-weight: 800; font-size: 1.7rem; color: var(--ink); letter-spacing: -0.03em; margin-bottom: .3rem; }
.status { display: flex; align-items: center; gap: .5rem; font-size: .92rem; color: var(--muted); margin-bottom: 1.6rem; }
.status::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--muted); }
.status.on { color: var(--teal); }
.status.on::before { background: var(--teal); }
.status.off { color: var(--danger); }
.status.off::before { background: var(--danger); }

/* Buttons */
.stButton button { border-radius: 3px; border: 1px solid var(--ink); background: var(--sheet); color: var(--ink); font-weight: 600; }
.stButton button:hover { border-color: var(--teal); color: var(--teal); }
[data-testid="stBaseButton-primary"] { background: var(--ink); color: #FFFFFF; border-color: var(--ink); }
[data-testid="stBaseButton-primary"]:hover { background: var(--teal); border-color: var(--teal); color: #FFFFFF; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 2rem; border-bottom: 1px solid var(--rule); }
.stTabs [data-baseweb="tab-highlight"] { background: var(--teal); }
.stTabs [role="tab"] { font-size: 1.05rem; font-weight: 600; color: var(--muted); }
.stTabs [role="tab"][aria-selected="true"] { color: var(--ink); }

/* Landing */
.hero h1 { font-size: clamp(2.6rem, 5.4vw, 4.6rem); line-height: 1.02; font-weight: 700; max-width: 14ch; margin: 0 0 1.1rem; }
.hero p { font-size: 1.22rem; line-height: 1.6; color: var(--muted); max-width: 46ch; margin: 0; }
.steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; margin-top: 3.2rem; border-top: 2px solid var(--ink); }
.steps > div { padding-top: 1rem; }
.steps strong { display: block; font-size: 1.2rem; color: var(--ink); margin-bottom: .3rem; }
.steps span { color: var(--muted); line-height: 1.5; }

/* Candidate sheet: skills are marked the way a recruiter highlights a resume */
.sheet { background: var(--sheet); border: 1px solid var(--rule); border-radius: 4px; padding: 2.4rem 2.6rem; box-shadow: 0 22px 44px -32px rgba(15, 43, 61, .45); margin-bottom: 1.8rem; }
.name { font-size: clamp(2.4rem, 4.8vw, 3.7rem); font-weight: 700; line-height: 1.02; margin: 0; }
.contact { display: flex; flex-wrap: wrap; gap: .4rem 1.6rem; margin-top: .9rem; color: var(--muted); }
.summary { font-size: 1.18rem; margin: 1.3rem 0 0; max-width: 58ch; }
.skills { display: flex; flex-wrap: wrap; gap: .7rem 1.2rem; margin-top: 1.5rem; }
.hl {
  font-size: 1.02rem; font-weight: 600; color: var(--ink); padding: 0 .2rem;
  background-image: linear-gradient(var(--highlight), var(--highlight));
  background-repeat: no-repeat;
  background-position: 0 88%;
  background-size: 0% 45%;
  animation: sweep .8s cubic-bezier(.2, .7, .2, 1) forwards;
  animation-delay: calc(var(--i, 0) * 70ms);
}
@keyframes sweep { to { background-size: 100% 45%; } }
@media (prefers-reduced-motion: reduce) { .hl { animation: none; background-size: 100% 45%; } }

/* Profile */
.section-title { font-size: 1.4rem; font-weight: 700; color: var(--ink); margin: 2.2rem 0 .8rem; }
.xp { display: grid; grid-template-columns: 200px 1fr; gap: 1.8rem; padding: 1.3rem 0; border-top: 1px solid var(--rule); }
.xp-when { color: var(--muted); padding-top: .25rem; }
.xp-role { font-size: 1.3rem; font-weight: 700; color: var(--ink); }
.xp-company { color: var(--teal); font-weight: 500; margin: .15rem 0 .6rem; }
.xp-body p { margin: 0 0 .8rem; line-height: 1.6; max-width: 64ch; }
.tag { display: inline-block; font-size: .9rem; color: var(--muted); border: 1px solid var(--rule); border-radius: 2px; padding: .1rem .5rem; margin: 0 .35rem .35rem 0; }
.trio { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2.2rem; margin-top: 2.4rem; }
.trio h3 { font-size: 1.1rem; padding-bottom: .5rem; margin: 0 0 .7rem; border-bottom: 2px solid var(--ink); }
.trio ul { margin: 0; padding-left: 1.1rem; line-height: 1.55; }
.trio li { margin-bottom: .55rem; }
.empty { color: var(--muted); font-style: italic; margin: 0; }

@media (max-width: 820px) {
  .sheet { padding: 1.5rem; }
  .steps, .trio { grid-template-columns: 1fr; }
  .xp { grid-template-columns: 1fr; gap: .3rem; }
}
</style>
"""


class ApiError(Exception):
    """The API is unreachable or returned an error."""


def esc(value) -> str:
    """Escape resume text before it goes into HTML. Resume content is untrusted."""
    if value in (None, ""):
        return ""
    return html.escape(str(value)).replace("\n", "<br>")


def render_html(markup: str) -> None:
    st.markdown(textwrap.dedent(markup).strip(), unsafe_allow_html=True)


@st.cache_data(ttl=30, show_spinner=False)
def api_is_online() -> bool:
    try:
        return requests.get(f"{API_URL}/", timeout=2).ok
    except requests.RequestException:
        return False


def api_post(path: str, **kwargs) -> dict:
    try:
        response = requests.post(f"{API_URL}{path}", timeout=180, **kwargs)
    except requests.ConnectionError:
        raise ApiError("Can't reach the Hiremeai API. Start the server and try again.")
    except requests.Timeout:
        raise ApiError("The API took too long to respond. Try again in a moment.")

    if response.ok:
        return response.json()

    detail = None
    try:
        body = response.json()
        detail = body.get("detail") if isinstance(body, dict) else None
    except ValueError:
        pass
    raise ApiError(detail if isinstance(detail, str) else "The server hit an error. Try again.")


def reset_session() -> None:
    st.session_state.resume = None
    st.session_state.resume_id = None
    st.session_state.messages = []
    st.session_state.parse_error = None


def parse_uploaded_resume(uploaded) -> None:
    st.session_state.parse_error = None
    try:
        with st.spinner("Reading the resume and building the profile..."):
            payload = api_post(
                "/upload",
                files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
            )
    except ApiError as exc:
        st.session_state.parse_error = str(exc)
        return

    st.session_state.resume = payload["resume"]
    st.session_state.resume_id = payload["resume_id"]
    st.session_state.messages = []
    st.toast("Profile ready.")


def answer_question(prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=AVATARS["user"]):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        try:
            with st.spinner("Checking the resume..."):
                answer = api_post(
                    "/ask",
                    json={"resume_id": st.session_state.resume_id, "question": prompt},
                )["answer"]
        except ApiError as exc:
            answer = f"I couldn't get an answer. {exc}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})


def render_sidebar(online: bool) -> None:
    with st.sidebar:
        st.markdown('<div class="wordmark">Hiremeai</div>', unsafe_allow_html=True)
        status = "API connected" if online else "API offline"
        state = "on" if online else "off"
        st.markdown(f'<div class="status {state}">{status}</div>', unsafe_allow_html=True)

        st.subheader("Resume")
        uploaded = st.file_uploader(
            "Upload a PDF",
            type=["pdf"],
            help=f"Text-based PDFs up to {MAX_UPLOAD_MB} MB.",
        )
        too_large = uploaded is not None and uploaded.size > MAX_UPLOAD_MB * 1024 * 1024
        if too_large:
            st.error(f"That file is over {MAX_UPLOAD_MB} MB. Try a smaller PDF.")

        if st.button(
            "Parse resume",
            type="primary",
            use_container_width=True,
            disabled=uploaded is None or too_large or not online,
        ):
            parse_uploaded_resume(uploaded)

        if not online:
            st.caption("Start the FastAPI server to enable parsing.")

        if st.session_state.resume is not None and st.button("Clear candidate", use_container_width=True):
            reset_session()


def render_landing() -> None:
    render_html("""
    <section class="hero">
      <h1>Meet the candidate before the call.</h1>
      <p>Upload a resume and question an AI representative of the candidate. Every answer comes only from what the resume says.</p>
    </section>
    <div class="steps">
      <div><strong>Upload</strong><span>Add a text-based PDF resume from the sidebar.</span></div>
      <div><strong>Parse</strong><span>Hiremeai structures skills, roles, projects and education.</span></div>
      <div><strong>Interview</strong><span>Ask questions and get answers grounded in the resume.</span></div>
    </div>
    """)


def experience_row(exp: dict) -> str:
    when = esc(exp.get("duration")) or "Dates not stated"
    role = esc(exp.get("role")) or "Role not stated"
    company = esc(exp.get("company"))
    description = esc(exp.get("description"))
    description_html = f"<p>{description}</p>" if description else ""
    tags = "".join(f'<span class="tag">{esc(skill)}</span>' for skill in (exp.get("skills_used") or []))
    return (
        f'<div class="xp"><div class="xp-when">{when}</div><div class="xp-body">'
        f'<div class="xp-role">{role}</div><div class="xp-company">{company}</div>'
        f"{description_html}<div>{tags}</div></div></div>"
    )


def bullet_list(items) -> str:
    cleaned = [esc(item) for item in (items or []) if item]
    if not cleaned:
        return '<p class="empty">Nothing listed.</p>'
    return "<ul>" + "".join(f"<li>{item}</li>" for item in cleaned) + "</ul>"


def render_profile(resume: dict, experiences: list) -> None:
    st.download_button(
        "Download profile JSON",
        data=json.dumps(resume, indent=2),
        file_name="candidate-profile.json",
        mime="application/json",
    )

    rows = "".join(experience_row(exp) for exp in experiences) or '<p class="empty">No experience listed.</p>'
    render_html(f'<div class="section-title">Experience</div>{rows}')

    render_html(
        '<div class="trio">'
        f"<div><h3>Education</h3>{bullet_list(resume.get('education'))}</div>"
        f"<div><h3>Projects</h3>{bullet_list(resume.get('projects'))}</div>"
        f"<div><h3>Certifications</h3>{bullet_list(resume.get('certifications'))}</div>"
        "</div>"
    )


def render_interview() -> None:
    columns = st.columns(len(SUGGESTIONS))
    clicked = None
    for column, question in zip(columns, SUGGESTIONS):
        if column.button(question, key=f"suggest-{question}", use_container_width=True):
            clicked = question

    if not st.session_state.messages:
        st.caption("Answers come only from the resume. If it doesn't say, Hiremeai says so.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=AVATARS[message["role"]]):
            st.markdown(message["content"])

    typed = st.chat_input("Ask about this candidate")
    prompt = clicked or typed
    if prompt:
        answer_question(prompt)


def render_candidate(resume: dict) -> None:
    experiences = resume.get("experiences") or []
    skills = resume.get("skills") or []
    years = resume.get("total_experience_years")

    if years is not None:
        summary = f"{years:g} years of experience"
        if experiences:
            summary += f" across {len(experiences)} roles"
    else:
        summary = "Years of experience not stated"
    summary += "."

    name = esc(resume.get("name")) or "Name not found"
    contact = "".join(
        f"<span>{esc(value)}</span>"
        for value in (resume.get("email"), resume.get("phone"))
        if value
    )
    skill_chips = "".join(
        f'<span class="hl" style="--i:{index}">{esc(skill)}</span>'
        for index, skill in enumerate(skills)
    ) or '<p class="empty">No skills found in this resume.</p>'

    render_html(f"""
    <div class="sheet">
      <h1 class="name">{name}</h1>
      <div class="contact">{contact}</div>
      <p class="summary">{summary}</p>
      <div class="skills">{skill_chips}</div>
    </div>
    """)

    profile_tab, interview_tab = st.tabs(["Profile", "Interview"])
    with profile_tab:
        render_profile(resume, experiences)
    with interview_tab:
        render_interview()


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

    defaults = {"resume": None, "resume_id": None, "messages": [], "parse_error": None}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    online = api_is_online()
    render_sidebar(online)

    if st.session_state.parse_error:
        st.error(st.session_state.parse_error)

    if st.session_state.resume is None:
        render_landing()
    else:
        render_candidate(st.session_state.resume)


main()
