from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import google.generativeai as genai
import os, base64, io
import PyPDF2
import docx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/", response_class=HTMLResponse)
def root():
    return open("index.html").read() if os.path.exists("index.html") else HTMLResponse("<h1>PocketMind Running</h1>")

@app.get("/health")
def health():
    return {"status": "PocketMind server is running"}

@app.post("/chat")
async def chat(message: str = Form(...)):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(message)
    return {"reply": response.text}

@app.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    question: str = Form(default="Describe this image in detail.")
):
    contents = await file.read()
    encoded = base64.b64encode(contents).decode("utf-8")
    mime = file.content_type or "image/jpeg"
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([{"mime_type": mime, "data": encoded}, question])
    return {"reply": response.text}

@app.post("/analyze-document")
async def analyze_document(
    file: UploadFile = File(...),
    question: str = Form(default="Summarize this document.")
):
    contents = await file.read()
    text = ""
    if file.filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(io.BytesIO(contents))
        for page in reader.pages:
            text += page.extract_text() or ""
    elif file.filename.endswith(".docx"):
        doc = docx.Document(io.BytesIO(contents))
        text = "\n".join([p.text for p in doc.paragraphs])
    elif file.filename.endswith(".txt"):
        text = contents.decode("utf-8", errors="ignore")
    else:
        return {"reply": "Unsupported file type."}
    if not text.strip():
        return {"reply": "Could not extract text."}
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(f"Document:\n\n{text[:4000]}\n\nQuestion: {question}")
    return {"reply": response.text}
