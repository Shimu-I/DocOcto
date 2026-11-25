> NOTE: this guide was written early and parts describe an earlier version. For the current features, limits and instructions, read FEATURES_AND_USAGE.md in this folder.

# DocOcto: Complete Project Guide

DocOcto is a free academic writing assistant. You upload a research paper, an animated neon wireframe octopus crawls over it, its tentacles point at writing problems, and every problem is listed on the right so you can accept or reject each suggested fix.

This guide explains what the project does, how it works inside, which technologies it uses, how to run it, and where its limits are.

---

## 1. The two editions

| | Online page | Python edition (Ubuntu) |
|---|---|---|
| Where it runs | A hosted page in your Claude account | Your own computer, at `http://localhost:3000` |
| File | `dococto.html` | `dococto-python.zip` |
| Reads DOCX/PDF with | Mammoth and PDF.js in the browser (loaded from a CDN) | Python (`python-docx`, `pypdf`) on your machine |
| AI check uses | Claude, through your Claude account | Ollama, Gemini or Groq (all with free options), set in `.env` |
| Grammar check (LanguageTool) | Not available | Yes (optional install) |
| Works offline | No | Yes, after the first install (except optional cloud AI) |

Both editions share the same front-end code. The Python edition is the same page with a small server behind it.

---

## 2. Features

### Interface
- Dark navy interface with neon pink and cyan accents, laid out in three columns as in the reference design.
- Header: logo, tagline, file name, status badge, View/Edit toggle, Quick check, Grammar check (Python edition), AI check, Export, Upload.
- Left sidebar: Overview, Issues (with unresolved count), Summary, Settings, and a status card with a progress bar.
- Center: a scrollable document, a page thumbnail strip, and a bottom toolbar.
- Right: category counts, a full list of all issues, and a suggestion card.

### Document handling
- Upload `.docx`, `.pdf`, `.txt` or `.md`.
- DOCX: headings, lists and paragraphs are kept.
- PDF: text is extracted and rebuilt into paragraphs. Page numbers are tracked. Words split by a hyphen at a line end are joined back together (Python edition).
- Scanned PDFs (no selectable text) are detected and reported as needing OCR.
- Page thumbnails are generated from your actual content: one per PDF page, or one per roughly 2,200 characters for other files. Lines that contain issues are marked amber.

### Issue review
- Six color-coded categories: Grammar, Clarity, Style & Tone, Repetition, Citation, Structure.
- Each highlight also has its own underline style (wavy, solid, dotted, dashed, double, overline), so color is never the only cue. Each has an accessible label.
- Click a category to filter highlights and the issue list. Click it again to clear.
- Click a highlighted phrase or a list row to select it. The document scrolls to it, the suggestion card updates, and a tentacle reaches it.
- Previous/next arrows move through issues.
- Accept applies the suggestion to the text. Reject keeps your original wording and marks it as kept. You can revisit either.
- A Fix button on each list row applies that one suggestion.
- Undo (button or Ctrl+Z) reverses accepts and rejects.
- Edit mode lets you type directly in the document.
- Export saves the revised text as a Markdown file. Your original file is never modified.

### Toolbar
Zoom out, zoom percentage, zoom in, pointer tool, pan tool (drag to scroll), focus selected issue, fit to view, Pause/Play animation, octopus on/off, show/hide highlights.

### Octopus
- 3D wireframe mantle with a mesh surface, two glowing cyan eyes and a slow turning motion.
- Eight tapered tentacles, each with its own length, curl and phase, with curved cross rings, inner mesh lines, suction cups and glowing tips.
- The whole octopus travels around the window, parks beside the issue it is pointing at, and moves to the next one every few seconds.
- Every tentacle reaches for its own visible issue at the same time. Tentacles with nothing to point at keep waving.
- Pause button, on/off switch, and automatic pause for people who set "reduce motion" in their system.

---

## 3. Technology stack

### Front end (both editions)
- **HTML, CSS, vanilla JavaScript** in a single file. No framework and no build step.
- **HTML Canvas 2D** for the octopus, drawn every frame with `requestAnimationFrame`.
- **CSS variables** for the color system (one variable per issue category), `color-mix()` for translucent highlights, CSS grid for the layout.
- **Google Fonts**: Inter (interface) and Source Serif 4 (headings), with system fallbacks.
- **Mammoth 1.6.0** and **PDF.js 3.11.174** (online page only) to read DOCX and PDF in the browser.

### Python edition (server)
- **Python 3** with **Flask** (web server).
- **python-docx** reads DOCX files.
- **pypdf** reads PDF text.
- **language-tool-python** (optional) runs **LanguageTool**, a free open-source grammar and spelling engine. It needs Java 17 or newer.
- The standard library (`urllib`, `json`, `re`, `collections`) handles AI provider calls and text processing.

### Optional AI providers (Python edition)
| Provider | Cost | Notes |
|---|---|---|
| Ollama | Free, local | Runs a model on your computer. Default model `llama3.1:8b`. |
| Gemini | Free tier | Needs a free API key. Default model `gemini-2.0-flash`. |
| Groq | Free tier | Needs a free API key. Default model `llama-3.3-70b-versatile`. |
| Anthropic | Paid | Supported but not required. |

Free tiers and model names change over time. Set `AI_MODEL` in `.env` if a default stops working.

### Online page only
- A runtime feature lets the page ask Claude to analyze text (AI check) and lets it save a file (Export), using your own Claude account.

---

## 4. Project layout (Python edition)

```
dococto-python/
  app.py                    Flask server: file reading, grammar, AI
  run.sh                    One command: venv, install, start
  requirements.txt          flask, python-docx, pypdf
  requirements-grammar.txt  language-tool-python (optional)
  ignore_words.txt          Words the grammar check should skip
  .env.example              Settings template (copy to .env)
  .gitignore                Keeps .venv and .env out of version control
  README.md                 Setup and troubleshooting
  public/
    index.html              The whole front end
```

---

## 5. How it works

### 5.1 The document model
After a file is read, the app holds a list of paragraphs:

```
{ t: "paragraph text", tag: "p" | "h2" | "li", page: 3 }
```

An **issue** looks like this:

```
{ id, cat, o: "exact original phrase", s: "suggested replacement",
  w: ["reason", ...], st: "open" | "acc" | "rej", p: paragraphIndex }
```

### 5.2 Stable anchors
Issues are never found by searching for a phrase alone. Each one is anchored by **paragraph index + exact phrase + occurrence number** ("the 2nd time this phrase appears in paragraph 7"). `buildDoc()` turns those anchors into character offsets, sorts them, and drops any issue whose range overlaps an earlier one. Anything that cannot be located in the text is discarded, so the app never shows a suggestion pointing at nothing.

### 5.3 Rendering the document
`buildDoc()` writes each paragraph as HTML and wraps each issue range in a `<span class="is">` with data attributes for its id and category. Text is HTML-escaped first. Because the spans are real text in the page, text stays selectable, searchable and keyboard-focusable.

### 5.4 Accept, reject, undo
- Accept replaces the span's text with the suggestion and records the previous state on an undo stack.
- Reject marks the span as kept and leaves the wording unchanged.
- Undo pops the stack and restores both the text and the status.
- The export reads the current text from the page, so accepted fixes and any manual edits are included. The parsed original stays untouched in memory.

### 5.5 Where highlights meet the octopus
`tpos(id)` asks the browser for the highlighted span's real position with `getClientRects()`, converts it to canvas coordinates, and returns nothing if the phrase is off-screen. Nothing is hard-coded. Scrolling, zooming and resizing all work because positions are re-read every frame, only for the few spans needed. The first rectangle is used when a phrase wraps across lines.

The canvas has `pointer-events: none`, so it never blocks clicks, selection or scrolling.

---

## 6. How the octopus is built

### 6.1 The mantle (head)
- Shape: a profile function gives the radius at each height. The top is a dome, and the lower part narrows like a bulb.
- Surface: 18 longitude lines and 13 rings are computed as 3D points, rotated by a slowly changing yaw angle, and projected to 2D with a slight tilt.
- Depth cue: lines on the front face are bright, lines on the back are faint.
- Extras: glowing nodes where lines cross, a layered pink outline glow, and two eyes placed on the 3D surface so they turn with the head.
- Size: the mantle is about 46 by 128 units, scaled to the window width.

### 6.2 The eight tentacles
Each tentacle is a chain of 34 segments.

1. **Rest shape.** Each tentacle has its own direction, length (about 285 to 400 units) and total curl, so they head left, down, curl inward and curl upward. The set is deliberately not symmetrical.
2. **Motion.** The angle of each segment is the rest curl plus a traveling wave along the tentacle, a slow sway, and a slower secondary wave. Each tentacle has its own phase and amplitude, driven only by time, so there is no random jitter.
3. **Reaching.** When a tentacle has a target, the chain is bent toward it with **FABRIK** (a simple inverse-kinematics method) for 6 passes per frame. The base stays fixed, segment lengths stay constant, and the result blends in smoothly using an eased factor, so the tentacle curves toward the text instead of sliding in a straight line.
4. **Probing.** The tip drifts slightly around its target so it feels alive.
5. **Shape.** Width tapers from thick at the base to thin at the tip. The outline, two inner lines, curved cross rings and a faint center line give a wireframe volume.
6. **Suction cups.** Small double rings sit on the inner edge of each tentacle's curl, computed from the same centerline so they move with it. They flatten a little where the tentacle bends.
7. **Glow.** Each tentacle is drawn in layers: a wide faint stroke, then a thin bright stroke, with additive blending. The tips use a small shadow blur and brighten when they reach text. A thin neon thread connects the tip to the phrase.
8. **Depth order.** Tentacles on the far side of the body are drawn first, then the mantle, then the near ones.

### 6.3 Choosing targets
Every frame, the app lists the visible open issues (the selected one and the current tour target come first). It scores every tentacle against every issue by distance relative to the tentacle's length, then assigns greedily from the best score. A small bonus keeps a tentacle on its previous target to avoid flicker. Targets that are too far are skipped, so those tentacles keep waving.

### 6.4 Roaming
The head moves toward the current tour issue, sitting on the side of it that has more room and slightly above it. Every 2.6 seconds the tour moves to the next unresolved issue. If that issue is off-screen, the document scrolls to it first. Selecting an issue makes the octopus go there immediately.

### 6.5 Performance and accessibility
- One `requestAnimationFrame` loop, no DOM creation per frame, geometry rebuilt from simple math.
- Expensive blur is used only on tips and eyes.
- The loop is wrapped in `try/catch`, so a drawing error cannot break the document.
- Reduced-motion preference starts the animation paused.
- Pause, octopus on/off and show/hide highlights are always available.

---

## 7. The three checkers

### 7.1 Quick check (free, works offline, both editions)
Rule-based pattern matching in the browser. It looks for:
- Wordy phrases ("in order to", "due to the fact that", "a number of").
- Informal quantities and hedges ("a lot of", "kind of", "sort of").
- Intensifiers ("very good", "really important").
- Common misspellings (about 20 frequent ones).
- Contractions ("don't", "can't", "it's").
- Repeated words ("the the").
- Informal sentence openers ("And", "But", "So", "Also").
- Citation formatting: a missing comma in "(Smith 2020)", and "et al" without a period.
- Absolute or strong wording ("always", "never", "clearly", "proves").
- Very long sentences (over 45 words).

It is pattern matching, not understanding. It misses subtle problems and can flag harmless text. Items that only need your attention (like a long sentence) carry no replacement.

### 7.2 Grammar check (free, Python edition, optional install)
Sends each paragraph to **LanguageTool**, which finds grammar, spelling, punctuation and style problems with suggested replacements. The results are merged with the Quick check rules for citations and style. To reduce false alarms on research writing, the server skips spelling flags for likely technical terms: words used three or more times, acronyms, hyphenated or numeric terms, and anything in `ignore_words.txt`. Headings are not checked.

Setup:
```
sudo apt install -y openjdk-17-jre-headless
source .venv/bin/activate
pip install -r requirements-grammar.txt
```
The first run downloads the engine (a few hundred MB).

### 7.3 AI check (optional)
The paper is split into batches of about 5,000 characters. Each batch is sent to the AI with instructions to return a JSON list. Each item carries the paragraph index, the exact phrase, the occurrence number, a category, a replacement and one or two reasons. The prompt tells the AI to:
- Keep the author's meaning.
- Never invent data, results, sources or citations.
- Never make a claim stronger.
- Leave equations and numbers alone.
- Flag only the formatting of citations, and never claim a source was verified.

The page shows real progress (batch X of Y). Every returned item is validated against your text before it is shown. In the Python edition the API key stays on the server and is never sent to the browser.

Small free models make more mistakes than large ones and sometimes return invalid output. Invalid or unlocatable items are dropped.

---

## 8. Server API (Python edition)

| Endpoint | Purpose |
|---|---|
| `POST /api/parse?name=file.docx` | Raw file bytes in, `{paras: [...]}` out. Handles `.docx` and `.pdf`. Returns an error for scanned or unreadable files. |
| `POST /api/analyze` | `{prompt}` in, `{text}` out. Calls the chosen AI provider. |
| `POST /api/grammar` | `{paras: [...]}` in, `{issues: [...]}` out. Runs LanguageTool. |
| `GET /` | Serves the page. |

Settings go in `.env` (copy from `.env.example`): `AI_PROVIDER`, `AI_MODEL`, `AI_API_KEY`, `PORT`, and optionally `OLLAMA_URL` and `LT_LANG`.

The server listens only on `127.0.0.1` (your own computer), accepts uploads up to 20 MB (20,000 paragraphs, 400 PDF pages), and keeps `.env` out of version control.

---

## 9. Running it on Ubuntu

```
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
unzip dococto-python.zip
cd dococto-python
bash run.sh
```
Then open http://localhost:3000. Stop with Ctrl+C. Next time, run `bash run.sh` again.

By hand:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Common problems:
- `venv` error: `sudo apt install python3-venv`.
- `externally-managed-environment`: you ran pip outside the virtual environment. Run `source .venv/bin/activate` first.
- Port in use: set `PORT=3001` in `.env`.
- "Cannot reach Ollama": install it, run `ollama pull llama3.1:8b`, and keep it running.
- "AI_API_KEY is not set": add the key to `.env` and restart, or use Quick check or Grammar check.
- Grammar check cannot start: install Java 17 and `requirements-grammar.txt`.

---

## 10. Honest limits

- **Accuracy.** No automatic checker is perfect, and DocOcto is not as polished as a paid tool like Grammarly. Expect missed problems and wrong suggestions, especially with technical terms, equations and citations. Always review each suggestion.
- **PDF display.** PDFs appear as reflowed text, not as the original page images. Two-column layouts, headers and footnotes can come out in a mixed order. DOCX gives cleaner results.
- **No OCR.** Scanned PDFs are detected but cannot be read.
- **DOCX details.** Tables, images, equations and tracked changes are not read or preserved.
- **Export.** Export is Markdown only. Fixes change the text shown in DocOcto and the export. They do not edit your original PDF or DOCX. There is no DOCX or PDF export yet.
- **Edit mode.** Text you type in Edit mode is included in the export, but it is not re-checked until you run a check again.
- **Citations and claims.** DocOcto never verifies that a citation exists or that a scientific claim is true.
- **Demo content.** The preloaded demo paper and its 8 issues are samples, not real analysis.
- **Structure.** It is a single-file front end with a small server, not a React/TypeScript/Vite project.

### Academic integrity rules built in
- Suggestions come with a reason.
- The original file and parsed text are never overwritten.
- Nothing is changed until you accept it.
- The AI is told not to invent or strengthen anything, and unlocatable suggestions are discarded.

---

## 11. What has been tested

Tested:
- Code syntax checks for the front end and the server.
- Quick check rules on a sample sentence (all expected issues found with correct anchors).
- The Flask endpoints with a test client: DOCX reading, bad PDF error, wrong file type error, missing-key error, page serving.

Not yet tested:
- Visual comparison on screen against the reference image.
- Real PDF files, scanned PDFs and large papers.
- LanguageTool, Ollama, Gemini and Groq on a real machine.
- Keyboard-only use and screen readers.

A manual checklist is in `README.md`.

---

## 12. Possible next steps

- Real PDF page rendering with PDF.js so annotations sit on the original pages.
- DOCX export with formatting preserved, using a free library.
- OCR for scanned PDFs (for example Tesseract).
- Equation and citation-aware checking, and reference-list consistency checks.
- A rebuild in React, TypeScript and Vite with separate components.
- A "reject all of this kind" and "ignore this word" control inside the interface.

---

## 13. Glossary

- **Mantle**: the octopus's head.
- **Anchor**: the paragraph, phrase and occurrence that locate an issue.
- **FABRIK**: an inverse-kinematics method that bends a chain of segments toward a target.
- **LanguageTool**: a free, open-source grammar and spelling engine.
- **Ollama**: free software that runs AI models on your own computer.
- **Canvas 2D**: the browser's drawing surface used for the octopus.
- **OCR**: turning a picture of text into real text.

---

## 14. Update: Milestone 1 (reliability and trust)
- Fixed an escaping bug in the suggestion panel (paper text and AI explanations are now escaped).
- New server-side validation (`dococto/validate.py`) rejects suggestions that cannot be located, overlap, change numbers, add citations, alter equations or add stronger wording. Suggestions are labelled likely error, optional style, or review only.
- New Word export (`dococto/export.py`): headings, paragraphs and bullet lists only.
- Upload limits, a privacy confirmation before sending text to a cloud AI provider, and a "Checks run" line.
- A pytest suite (48 tests). See `docs/AUDIT_AND_ROADMAP.md` for the audit, roadmap and what is still untested. Sections 7, 8 and 10 above describe the earlier version where they differ.
