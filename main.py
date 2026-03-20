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

HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>PocketMind</title><style>*{margin:0;padding:0;box-sizing:border-box}body{background:#0a0a0f;color:#f0f0f8;font-family:sans-serif;min-height:100vh}.header{padding:20px;background:rgba(10,10,15,0.95);border-bottom:1px solid #2a2a3a;display:flex;justify-content:space-between;align-items:center}.logo{font-size:22px;font-weight:800;background:linear-gradient(135deg,#7c6af7,#f76a8a);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.dot{width:8px;height:8px;border-radius:50%;background:#6af7c8;box-shadow:0 0 8px #6af7c8}.tabs{display:flex;gap:8px;padding:16px}.tab{padding:10px 18px;border-radius:100px;border:1px solid #2a2a3a;background:#12121a;color:#8888aa;font-size:13px;font-weight:600;cursor:pointer}.tab.active{background:#7c6af7;border-color:#7c6af7;color:white}.chat{padding:8px 16px;display:flex;flex-direction:column;gap:12px;min-height:60vh;padding-bottom:120px}.msg{max-width:88%;padding:12px 16px;border-radius:18px;font-size:14px;line-height:1.6}.msg.user{background:linear-gradient(135deg,#7c6af7,#5a4fd4);color:white;align-self:flex-end;border-bottom-right-radius:6px}.msg.ai{background:#1a1a26;border:1px solid #2a2a3a;align-self:flex-start;border-bottom-left-radius:6px}.msg.err{background:rgba(247,106,138,0.15);border:1px solid rgba(247,106,138,0.3);color:#f76a8a;align-self:center;text-align:center}.label{font-size:10px;color:#6af7c8;text-transform:uppercase;margin-bottom:6px}.bottom{position:fixed;bottom:0;left:0;right:0;padding:12px 16px 24px;background:rgba(10,10,15,0.97);border-top:1px solid #2a2a3a}.row{display:flex;gap:10px;align-items:flex-end}.attach{width:44px;height:44px;border-radius:12px;background:#1a1a26;border:1px solid #2a2a3a;color:#8888aa;font-size:20px;display:none;align-items:center;justify-content:center;cursor:pointer}.tinput{flex:1;background:#1a1a26;border:1px solid #2a2a3a;border-radius:14px;padding:12px 14px;color:#f0f0f8;font-size:14px;outline:none;resize:none;max-height:100px;line-height:1.5}.sendbtn{width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,#7c6af7,#f76a8a);border:none;color:white;font-size:18px;display:flex;align-items:center;justify-content:center;cursor:pointer}.sendbtn:disabled{opacity:0.4}.preview{margin:0 16px 8px;padding:12px;background:#1a1a26;border:1px dashed #7c6af7;border-radius:16px;display:none;align-items:center;gap:12px}.preview.show{display:flex}.pname{font-size:13px}.psize{font-size:11px;color:#8888aa}.prem{background:none;border:none;color:#8888aa;font-size:18px;cursor:pointer}.typing{display:flex;gap:4px;padding:14px 18px;background:#1a1a26;border:1px solid #2a2a3a;border-radius:18px;border-bottom-left-radius:6px;align-self:flex-start;width:fit-content}.dot2{width:7px;height:7px;border-radius:50%;background:#7c6af7;animation:t 1.2s infinite}.dot2:nth-child(2){animation-delay:.2s}.dot2:nth-child(3){animation-delay:.4s}@keyframes t{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-6px);opacity:1}}.welcome{padding:40px 16px;text-align:center}.wi{font-size:52px;display:block;margin-bottom:16px}.wt{font-size:22px;font-weight:800;background:linear-gradient(135deg,#7c6af7,#f76a8a);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.wp{color:#8888aa;font-size:14px;line-height:1.6;max-width:280px;margin:8px auto 24px}.qbtns{display:flex;flex-direction:column;gap:8px;max-width:300px;margin:0 auto}.qbtn{padding:12px 16px;background:#1a1a26;border:1px solid #2a2a3a;border-radius:12px;color:#f0f0f8;font-size:13px;cursor:pointer;text-align:left;display:flex;align-items:center;gap:10px}</style></head><body><div class="header"><span class="logo">PocketMind</span><div class="dot"></div></div><div class="tabs"><div class="tab active" onclick="setMode('chat')">💬 Chat</div><div class="tab" onclick="setMode('image')">🖼️ Image</div><div class="tab" onclick="setMode('document')">📄 Document</div></div><div class="preview" id="prev"><div id="pthumb"></div><div style="flex:1"><div class="pname" id="pname"></div><div class="psize" id="psize"></div></div><button class="prem" onclick="removeFile()">✕</button></div><div class="chat" id="chat"><div class="welcome"><span class="wi">🧠</span><div class="wt">Hello, Judah!</div><p class="wp">Your personal AI assistant. Chat, analyse images, or read your documents.</p><div class="qbtns"><button class="qbtn" onclick="quickAsk('What can you help me with?')">✨ What can you help me with?</button><button class="qbtn" onclick="setMode('image')">🖼️ Analyse a photo</button><button class="qbtn" onclick="setMode('document')">📄 Read a document</button></div></div></div><div class="bottom"><div class="row"><button class="attach" id="att" onclick="triggerUpload()">📎</button><textarea class="tinput" id="inp" placeholder="Ask anything..." rows="1" onkeydown="hk(event)" oninput="ar(this)"></textarea><button class="sendbtn" id="sb" onclick="send()">➤</button></div></div><input type="file" id="fi" style="display:none" onchange="hf(event)"/><script>
const S='/';
let mode='chat',file=null;
function setMode(m){mode=m;document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));event.target.classList.add('active');document.getElementById('att').style.display=m!=='chat'?'flex':'none';document.getElementById('inp').placeholder=m==='image'?'Ask about your image...':m==='document'?'Ask about your document...':'Ask anything...';removeFile();}
function triggerUpload(){const f=document.getElementById('fi');f.accept=mode==='image'?'image/*':'.pdf,.docx,.txt';f.click();}
function hf(e){const f=e.target.files[0];if(!f)return;file=f;document.getElementById('pname').textContent=f.name;document.getElementById('psize').textContent=(f.size/1024).toFixed(0)+' KB';document.getElementById('prev').classList.add('show');}
function removeFile(){file=null;document.getElementById('prev').classList.remove('show');document.getElementById('fi').value='';}
function hk(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}}
function ar(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,100)+'px';}
function quickAsk(q){document.getElementById('inp').value=q;send();}
function addMsg(text,type){const c=document.getElementById('chat');const w=c.querySelector('.welcome');if(w)w.remove();const d=document.createElement('div');d.className='msg '+type;if(type==='ai')d.innerHTML='<div class="label">PocketMind</div>'+esc(text).replace(/\\n/g,'<br>');else d.textContent=text;c.appendChild(d);d.scrollIntoView({behavior:'smooth',block:'end'});}
function esc(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function showTyping(){const c=document.getElementById('chat');const d=document.createElement('div');d.className='typing';d.id='ti';d.innerHTML='<div class="dot2"></div><div class="dot2"></div><div class="dot2"></div>';c.appendChild(d);d.scrollIntoView({behavior:'smooth'});}
function hideTyping(){const e=document.getElementById('ti');if(e)e.remove();}
async function send(){
  const inp=document.getElementById('inp');
  const q=inp.value.trim();
  if(!q&&!file)return;
  addMsg(q||(mode==='image'?'Analyse this image':'Read this document'),'user');
  inp.value='';inp.style.height='auto';
  document.getElementById('sb').disabled=true;
  showTyping();
  try{
    let reply='';
    const fd=new FormData();
    if(mode==='chat'){fd.append('message',q);const r=await fetch('/chat',{method:'POST',body:fd});const d=await r.json();reply=d.reply||'No response';}
    else if(mode==='image'){if(!file){hideTyping();addMsg('Please attach an image first.','err');document.getElementById('sb').disabled=false;return;}fd.append('file',file);fd.append('question',q||'Describe this image in detail.');const r=await fetch('/analyze-image',{method:'POST',body:fd});const d=await r.json();reply=d.reply||'No response';removeFile();}
    else if(mode==='document'){if(!file){hideTyping();addMsg('Please attach a document first.','err');document.getElementById('sb').disabled=false;return;}fd.append('file',file);fd.append('question',q||'Summarize this document.');const r=await fetch('/analyze-document',{method:'POST',body:fd});const d=await r.json();reply=d.reply||'No response';removeFile();}
    hideTyping();addMsg(reply,'ai');
  }catch(e){hideTyping();addMsg('Could not reach server.','err');}
  document.getElementById('sb').disabled=false;
}
</script></body></html>"""

@app.get("/", response_class=HTMLResponse)
def root():
    return HTML

@app.get("/health")
def health():
    return {"status": "PocketMind server is running"}

@app.post("/chat")
async def chat(message: str = Form(...)):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(message)
    return {"reply": response.text}

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...), question: str = Form(default="Describe this image in detail.")):
    contents = await file.read()
    encoded = base64.b64encode(contents).decode("utf-8")
    mime = file.content_type or "image/jpeg"
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([{"mime_type": mime, "data": encoded}, question])
    return {"reply": response.text}

@app.post("/analyze-document")
async def analyze_document(file: UploadFile = File(...), question: str = Form(default="Summarize this document.")):
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
    return {"reply": response.text
