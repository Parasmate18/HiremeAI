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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
  --bg: #090D18; --panel: #111827; --panel2: #151E30; --line: #263248;
  --text: #F3F6FF; --muted: #9AA8C1; --accent: #8B7CFF; --cyan: #53D6E8;
  --good: #43D9A3; --danger: #FF7D91;
}
html, body, .stApp, [data-testid="stMarkdownContainer"] {
  font-family: 'DM Sans', sans-serif; color: var(--text);
}
.stApp { background: radial-gradient(ellipse at 10% 0%, #182044 0%, #090D18 48%); }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1400px; padding-top: 2rem; padding-bottom: 3rem; }
h1,h2,h3,h4,.wordmark,.section-title,.xp-role,.stButton button,.stTabs [role="tab"] {
  font-family: 'Space Grotesk', sans-serif;
}
h1,h2,h3 { color: var(--text); letter-spacing: -.035em; }
p, li { color: #C7D0E1; }
[data-testid="stSidebar"] { background: #0D1322; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] > div { padding-top: 1.5rem; }
.wordmark { font-size: 1.8rem; font-weight: 700; letter-spacing: -.06em; color: #fff; margin-bottom: .35rem; }
.wordmark:after { content: "."; color: var(--accent); }
.status { display:flex; align-items:center; gap:.5rem; font-size:.85rem; color:var(--muted); margin: .6rem 0 2rem; }
.status::before { content:""; width:8px; height:8px; border-radius:50%; background:var(--danger); box-shadow:0 0 12px #ff7d9180; }
.status.on { color:var(--good); } .status.on::before { background:var(--good); box-shadow:0 0 12px #43d9a380; }
.status.off { color:var(--danger); }
[data-testid="stFileUploader"] { background:#111827; border:1px dashed #35435C; border-radius:14px; padding:.6rem; }
.stButton button, .stDownloadButton button {
  border-radius: 10px; border:1px solid #35415A; background:#182237; color:#F3F6FF;
  font-weight:600; min-height:2.65rem; transition:all .18s ease;
}
.stButton button:hover, .stDownloadButton button:hover { border-color:var(--accent); color:white; background:#25274A; }
[data-testid="stBaseButton-primary"] { background:linear-gradient(110deg,#7868F6,#9C70FF)!important; color:white!important; border:0!important; box-shadow:0 8px 24px #8b7cff30; }
[data-testid="stBaseButton-primary"]:hover { filter:brightness(1.1); }
.stTabs [data-baseweb="tab-list"] { gap:.6rem; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { background:transparent; border-radius:10px 10px 0 0; padding:.8rem 1.2rem; }
.stTabs [data-baseweb="tab-highlight"] { background:var(--accent); height:3px; }
.stTabs [role="tab"] { font-size:1rem; font-weight:600; color:var(--muted); }
.stTabs [role="tab"][aria-selected="true"] { color:#fff; }
.hero { padding: 2.2rem 0 1.4rem; }
.eyebrow { display:inline-block; border:1px solid #5146A8; background:#25204B; color:#C9C2FF; border-radius:999px; padding:.4rem .8rem; font:600 .78rem 'DM Sans',sans-serif; letter-spacing:.08em; text-transform:uppercase; margin-bottom:1.25rem; }
.hero h1 { font-size:clamp(2.5rem,5vw,4.5rem); line-height:1.04; font-weight:700; max-width:850px; margin:0 0 1rem; }
.gradient-text { background:linear-gradient(90deg,#A99EFF,#5BDCED); -webkit-background-clip:text; background-clip:text; color:transparent; }
.hero p { font-size:1.12rem; line-height:1.7; color:var(--muted); max-width:680px; }
.steps { display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-top:2rem; }
.steps > div { background:linear-gradient(145deg,#151E30,#101725); border:1px solid var(--line); border-radius:16px; padding:1.4rem; min-height:145px; }
.step-number { color:var(--accent); font:700 .8rem 'Space Grotesk',sans-serif; letter-spacing:.12em; }
.steps strong { display:block; font:600 1.12rem 'Space Grotesk',sans-serif; color:#fff; margin:.65rem 0 .4rem; }
.steps span { color:var(--muted); line-height:1.55; font-size:.94rem; }
.sheet { background:linear-gradient(135deg,#151E30,#101725); border:1px solid var(--line); border-radius:20px; padding:2.2rem; box-shadow:0 18px 60px #00000025; margin:1rem 0 1.8rem; }
.name { font-size:clamp(2.2rem,4vw,3.4rem); font-weight:700; line-height:1.05; margin:0; }
.contact { display:flex; flex-wrap:wrap; gap:.5rem 1.2rem; margin-top:1rem; color:var(--muted); font-size:.95rem; }
.summary { font-size:1.08rem; margin:1.2rem 0 0; color:#C7D0E1; }
.skills { display:flex; flex-wrap:wrap; gap:.6rem; margin-top:1.4rem; }
.hl { font-size:.9rem; font-weight:600; color:#DAD6FF; padding:.45rem .75rem; background:#29264E; border:1px solid #49417E; border-radius:999px; }
.section-title { font-size:1.35rem; font-weight:700; color:#fff; margin:2rem 0 .8rem; }
.xp { display:grid; grid-template-columns:190px 1fr; gap:1.5rem; padding:1.4rem 0; border-top:1px solid var(--line); }
.xp-when { color:var(--muted); padding-top:.25rem; font-size:.9rem; }
.xp-role { font-size:1.2rem; font-weight:700; color:#fff; }
.xp-company { color:var(--cyan); font-weight:600; margin:.3rem 0 .7rem; }
.xp-body p { margin:0 0 .8rem; line-height:1.7; }
.tag { display:inline-block; font-size:.82rem; color:#C5D2E8; background:#1A263A; border:1px solid #33435B; border-radius:7px; padding:.25rem .55rem; margin:0 .35rem .35rem 0; }
.trio { display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-top:2rem; }
.trio > div { background:#111827; border:1px solid var(--line); border-radius:15px; padding:1.25rem; }
.trio h3 { font-size:1.05rem; padding-bottom:.8rem; margin:0 0 .8rem; border-bottom:1px solid var(--line); }
.trio ul { margin:0; padding-left:1.1rem; line-height:1.65; }
.trio li { margin-bottom:.5rem; }
.empty { color:var(--muted); font-style:italic; }
[data-testid="stChatMessage"] { background:#121B2B; border:1px solid var(--line); border-radius:15px; padding:1rem; }
[data-testid="stChatInput"] { border-color:#3B4560!important; background:#111827!important; border-radius:14px!important; }
[data-testid="stChatInput"] textarea { color:#fff!important; }
[data-testid="stAlert"] { border-radius:12px; }
div[data-testid="stCaptionContainer"] p { color:var(--muted); }
@media (max-width: 820px) {
  .sheet { padding:1.3rem; } .steps,.trio { grid-template-columns:1fr; }
  .xp { grid-template-columns:1fr; gap:.3rem; } .hero { padding-top:1rem; }
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
      <div class="eyebrow">✦ AI-powered recruiting workspace</div>
      <h1>Meet the candidate<br>before the <span class="gradient-text">call.</span></h1>
      <p>Turn any resume into a structured candidate profile. Explore experience, uncover skills, and ask questions with answers grounded in the actual resume.</p>
    </section>
    <div class="steps">
      <div><div class="step-number">01 / UPLOAD</div><strong>Bring in a resume</strong><span>Upload a text-based PDF securely from the sidebar to get started.</span></div>
      <div><div class="step-number">02 / ANALYZE</div><strong>Build the profile</strong><span>Organize skills, experience, projects, education and certifications.</span></div>
      <div><div class="step-number">03 / INTERVIEW</div><strong>Ask better questions</strong><span>Get fast, resume-grounded answers before the interview begins.</span></div>
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
