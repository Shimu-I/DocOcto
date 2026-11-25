"""DocOcto server: serves the page, reads DOCX/PDF, and (optionally) calls a free AI provider.
API keys stay here and are never sent to the browser."""
import io, json, os, re, threading, urllib.error, urllib.request
from collections import Counter
from werkzeug.exceptions import RequestEntityTooLarge
from dococto.validate import parse_ai_json, validate_issues
from dococto.citations import check_citations
from dococto.export import build_docx, FORMAT_NOTES
from flask import Flask, Response, jsonify, request, send_from_directory

def load_env(path=".env"):
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
load_env()

app = Flask(__name__, static_folder="public", static_url_path="")
MAX_BYTES, MAX_PARAS, MAX_PAGES = 20 * 1024 * 1024, 20000, 400   # resource limits for uploads
app.config["MAX_CONTENT_LENGTH"] = MAX_BYTES

class Fail(Exception):
    def __init__(self, status, message):
        super().__init__(message); self.status = status

# ---------- document reading ----------
def parse_docx(data):
    from docx import Document
    paras = []
    for p in Document(io.BytesIO(data)).paragraphs:
        t = p.text.strip()
        if not t: continue
        st = (p.style.name or "") if p.style is not None else ""
        tag = "h2" if st.startswith(("Heading", "Title")) else "li" if st.startswith("List") else "p"
        paras.append({"t": t, "tag": tag})
        if len(paras) > MAX_PARAS: raise Fail(413, "Document has more than %d paragraphs." % MAX_PARAS)
    return paras

def parse_pdf(data):
    from pypdf import PdfReader
    paras = []
    reader = PdfReader(io.BytesIO(data))
    if len(reader.pages) > MAX_PAGES: raise Fail(413, "PDF has more than %d pages." % MAX_PAGES)
    for pg, page in enumerate(reader.pages, 1):
        buf = ""
        for line in (page.extract_text() or "").splitlines():
            line = line.strip()
            if not line: continue
            if not buf and len(line) < 80 and not re.search(r"[.!?,;]$", line):
                paras.append({"t": line, "tag": "h2", "page": pg}); continue
            if buf.endswith("-") and line[:1].islower(): buf = buf[:-1] + line   # re-join words hyphenated at line ends
            else: buf = (buf + " " + line).strip()
            if (re.search(r"[.!?]$", line) and len(buf) > 120) or len(buf) > 800:
                paras.append({"t": buf, "tag": "p", "page": pg}); buf = ""
        if buf: paras.append({"t": buf, "tag": "p", "page": pg})
    if sum(len(p["t"]) for p in paras) < 100:
        raise Fail(422, "No selectable text found. This looks like a scanned PDF and needs OCR first.")
    return paras

@app.post("/api/parse")
def parse():
    name = (request.args.get("name") or "").lower()
    try:
        if name.endswith(".docx"): paras = parse_docx(request.get_data())
        elif name.endswith(".pdf"): paras = parse_pdf(request.get_data())
        else: raise Fail(400, "Use a .docx or .pdf file here.")
        if not paras: raise Fail(422, "No text found in this file.")
        return jsonify(paras=paras)
    except Fail as e:
        return jsonify(error=str(e)), e.status
    except RequestEntityTooLarge:
        return jsonify(error="File too large (limit %d MB)." % (MAX_BYTES // 1048576)), 413
    except Exception as e:
        return jsonify(error="Could not read this file: %s" % e), 422

@app.errorhandler(413)
def too_large(_): return jsonify(error="Request too large (limit %d MB)." % (MAX_BYTES // 1048576)), 413

# ---------- optional AI check (free providers) ----------
P = os.environ.get("AI_PROVIDER", "ollama").lower()
KEY = os.environ.get("AI_API_KEY", "")
DEF = {"ollama": "llama3.1:8b", "gemini": "gemini-2.0-flash", "groq": "llama-3.3-70b-versatile", "anthropic": "claude-sonnet-5-5"}
MODEL = os.environ.get("AI_MODEL") or DEF.get(P, "")

def post(url, headers, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=300) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            m = json.loads(e.read()).get("error"); m = m.get("message") if isinstance(m, dict) else m
        except Exception: m = None
        raise Fail(502, m or "The AI provider returned an error (%s)." % e.code)
    except Exception as e:
        if P == "ollama": raise Fail(502, "Cannot reach Ollama. Install it from ollama.com, run 'ollama pull %s', and keep it running." % MODEL)
        raise Fail(502, "Could not reach the AI provider: %s" % e)

def ask(prompt):
    if P not in DEF: raise Fail(503, "Unknown AI_PROVIDER '%s'. Use ollama, gemini, groq or anthropic." % P)
    if P != "ollama" and not KEY: raise Fail(503, "AI_API_KEY is not set in .env. Use Quick check, or see the README for free keys.")
    msgs = [{"role": "user", "content": prompt}]
    if P == "ollama":
        return post(os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/chat", {}, {"model": MODEL, "stream": False, "messages": msgs})["message"]["content"]
    if P == "gemini":
        j = post("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % MODEL, {"x-goog-api-key": KEY}, {"contents": [{"parts": [{"text": prompt}]}]})
        return "".join(p.get("text", "") for p in j["candidates"][0]["content"]["parts"])
    if P == "groq":
        return post("https://api.groq.com/openai/v1/chat/completions", {"Authorization": "Bearer " + KEY}, {"model": MODEL, "messages": msgs})["choices"][0]["message"]["content"]
    j = post("https://api.anthropic.com/v1/messages", {"x-api-key": KEY, "anthropic-version": "2023-06-01"}, {"model": MODEL, "max_tokens": 4000, "messages": msgs})
    return "".join(b.get("text", "") for b in j["content"] if b.get("type") == "text")

@app.post("/api/analyze")
def analyze():
    prompt = (request.get_json(silent=True) or {}).get("prompt")
    if not isinstance(prompt, str) or not prompt: return jsonify(error="Missing prompt"), 400
    try:
        text = ask(prompt)
        try: return jsonify(text=text, items=parse_ai_json(text))
        except ValueError as e: return jsonify(text=text, items=None, parse_error=str(e))
    except Fail as e: return jsonify(error=str(e)), e.status
    except Exception as e: return jsonify(error="AI check failed: %s" % e), 502

# ---------- grammar and spelling: LanguageTool (free, open source, runs on your computer) ----------
_tool = None
def _init_tool():
    global _tool
    if _tool is None:
        try: import language_tool_python
        except ImportError: raise Fail(503, "Grammar engine not installed. Run: pip install -r requirements-grammar.txt  and  sudo apt install -y openjdk-17-jre-headless")
        try: _tool = language_tool_python.LanguageTool(os.environ.get("LT_LANG", "en-US"))
        except Exception as e: raise Fail(503, "Could not start LanguageTool. It needs Java 17+ (sudo apt install -y openjdk-17-jre-headless). Details: %s" % e)
    return _tool

_lt_lock = threading.Lock()
def get_tool():
    with _lt_lock: return _init_tool()   # one LanguageTool instance even with concurrent requests

CAT = {"TYPOS": "gram", "GRAMMAR": "gram", "PUNCTUATION": "gram", "CASING": "gram", "CONFUSED_WORDS": "gram", "TYPOGRAPHY": "gram",
       "COMPOUNDING": "gram", "REDUNDANCY": "rep", "STYLE": "style", "COLLOQUIALISMS": "style", "PLAIN_ENGLISH": "style", "WIKIPEDIA": "style"}
def ignore_words():
    try: return {w.strip().lower() for w in open("ignore_words.txt", encoding="utf-8") if w.strip()}
    except OSError: return set()

@app.post("/api/grammar")
def grammar():
    paras = (request.get_json(silent=True) or {}).get("paras")
    if not isinstance(paras, list): return jsonify(error="Missing paragraphs"), 400
    try:
        tool, out, ign = get_tool(), [], ignore_words()
        freq = Counter(w.lower() for t in paras if isinstance(t, str) for w in re.findall(r"[A-Za-z][A-Za-z'-]+", t))
        for pi, t in enumerate(paras):
            if not isinstance(t, str) or not t.strip(): continue
            for m in tool.check(t):
                off = m.offset
                ln = getattr(m, "errorLength", None) or getattr(m, "error_length", None) or len(getattr(m, "matchedText", "") or "")
                o = t[off:off + ln]
                if not o.strip(): continue
                cid = (getattr(m, "category", "") or "").upper()
                if cid == "TYPOS" or str(getattr(m, "ruleId", "")).startswith("MORFOLOGIK"):
                    # skip likely technical terms: names, acronyms, hyphenated or numeric terms, words used 3+ times, your ignore list
                    if (o.lower() in ign or freq[o.lower()] >= 3 or any(c.isdigit() for c in o)
                            or sum(c.isupper() for c in o) > 1 or "-" in o or "_" in o): continue
                reps = list(m.replacements or [])
                out.append({"p": pi, "o": o, "occ": sum(1 for i in range(off) if t.startswith(o, i)) + 1,
                            "cat": CAT.get(cid, "clar"), "s": reps[0] if reps else o, "w": [m.message or "Possible issue."]})
        return jsonify(issues=out)
    except Fail as e: return jsonify(error=str(e)), e.status
    except Exception as e: return jsonify(error="Grammar check failed: %s" % e), 502

@app.post("/api/citations")
def citations():
    paras = (request.get_json(silent=True) or {}).get("paras")
    if not isinstance(paras, list) or len(paras) > MAX_PARAS or not all(isinstance(p, dict) for p in paras): return jsonify(error="Bad request"), 400
    try: return jsonify(**check_citations([{"t": str(p.get("t", "")), "tag": p.get("tag", "p")} for p in paras]))
    except Exception as e: return jsonify(error="Citation check failed: %s" % e), 500

@app.get("/api/config")
def config(): return jsonify(provider=P, model=MODEL, cloud=P != "ollama")   # cloud=True means text leaves this computer

@app.post("/api/validate")
def validate():
    j = request.get_json(silent=True) or {}
    paras, items = j.get("paras"), j.get("items")
    if not isinstance(paras, list) or not isinstance(items, list) or len(items) > 5000: return jsonify(error="Bad request"), 400
    ok, bad = validate_issues([str(t) for t in paras], items)
    return jsonify(issues=ok, rejected=bad)

@app.post("/api/export-docx")
def export_docx():
    paras = (request.get_json(silent=True) or {}).get("paras")
    if not isinstance(paras, list) or not paras or len(paras) > MAX_PARAS: return jsonify(error="No paragraphs to export."), 400
    try: data = build_docx([p for p in paras if isinstance(p, dict)])
    except Exception as e: return jsonify(error="DOCX export failed: %s" % e), 500
    return Response(data, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"X-Format-Notes": FORMAT_NOTES, "Content-Disposition": "attachment; filename=revised.docx"})

@app.get("/")
def index(): return send_from_directory("public", "index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))
    print("DocOcto running at http://localhost:%d  (AI check provider: %s)" % (port, P))
    app.run(host="127.0.0.1", port=port)
