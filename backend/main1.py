import io
import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from groq import Groq
from pydantic import BaseModel, Field, ValidationError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("GROQ_API_KEY missing hai bhai!")

client = Groq(api_key=my_api_key)
model = "openai/gpt-oss-120b"

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

app = FastAPI(title="Hiremeai")


# Resume data models
class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: str | None = None
    description: str | None = None
    skills_used: list[str] = []


class Resume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience_years: float | None = None
    skills: list[str] = []
    experiences: list[Experience] = []
    education: list[str] = []
    projects: list[str] = []
    certifications: list[str] = []


class ChatRequest(BaseModel):
    question: str


class AskRequest(BaseModel):
    resume_id: str
    question: str = Field(min_length=1, max_length=500)


resume_schema = Resume.model_json_schema()

# In-memory store keeps the demo simple. Use Redis or Postgres in production.
resume_store: dict[str, Resume] = {}


# Extract text from a PDF path or any file-like object
def read_pdf(source):
    reader = PdfReader(source)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


# Parse resume into JSON format
def parse_resume(resume_text):
    system_prompt = f"""
    You are an expert resume parser.

    Extract information from the resume based on its meaning,
    not only exact section headings.

    Return ONLY valid JSON matching this schema:
    {resume_schema}

    Rules:
    1. Do not invent information.
    2. If a value is unavailable, return null.
    3. If a list has no information, return an empty list.
    4. Include internships inside experiences.
    5. Extract skills from the entire resume.
    """

    user_prompt = f"""
    Parse the following resume:
    {resume_text}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response_format = {"type": "json_object"}

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format=response_format
    )

    raw_output = response.choices[0].message.content
    data = json.loads(raw_output)
    resume = Resume(**data)

    return resume


# HR interview assistant
def ask_candidate(question: str, resume: Resume):
    system_prompt = f"""
    You are an AI assistant representing a job candidate.

    Below is everything you should know about the candidate:

    {resume.model_dump_json(indent=2)}

    Rules:
    1. Answer only using this information.
    2. Never hallucinate.
    3. If information is unavailable, say:
    "I don't have enough information to answer that."
    4. Be professional.
    5. Answer as if HR is interviewing this candidate.
    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
    )

    return response.choices[0].message.content


@app.get("/")
def home():
    return {
        "message": "Hiremeai is running!"
    }


@app.post("/upload")
def upload_resume(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF resume.")

    contents = file.file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="This file is over 5 MB.")

    try:
        text = read_pdf(io.BytesIO(contents))
    except PdfReadError:
        raise HTTPException(status_code=400, detail="This PDF couldn't be opened. Try exporting it again.")

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text found. Scanned PDFs aren't supported yet.",
        )

    try:
        resume = parse_resume(text)
    except (json.JSONDecodeError, ValidationError):
        raise HTTPException(status_code=502, detail="Couldn't structure this resume. Please try again.")

    resume_id = uuid.uuid4().hex
    resume_store[resume_id] = resume

    return {"resume_id": resume_id, "resume": resume.model_dump()}


@app.post("/ask")
def ask(request: AskRequest):
    resume = resume_store.get(request.resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume session expired. Upload the resume again.")

    return {"answer": ask_candidate(request.question, resume)}


# Legacy endpoint: answers from myresume.pdf. Kept so existing clients still work.
@app.post("/chat")
def chat(request: ChatRequest):
    resume_text = read_pdf(
        Path(__file__).resolve().parent / "myresume.pdf"
    )

    resume = parse_resume(resume_text)
    answer = ask_candidate(request.question, resume)

    return {
        "answer": answer
    }
