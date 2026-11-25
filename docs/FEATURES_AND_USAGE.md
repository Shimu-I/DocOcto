# DocOcto: Features, Strengths, Weaknesses and How to Run It

Last updated: 2026-11-18. This is the complete reference for the project. For the short version see `../README.md`; for current status and your test checklist see `PROGRESS.md`.

---

## 1. At a glance

DocOcto is a **free, local-first writing reviewer for research papers**. You upload a PDF or Word file. DocOcto highlights writing problems on the real pages, explains each one, suggests a fix, and lets you accept or reject every change yourself. An animated wireframe octopus points at the problems.

- Runs on your own computer (Ubuntu tested). Everything needed is free and open source.
- Your original file is never modified.
- Nothing is changed unless you accept it, and every change can be undone.
- Text stays on your computer unless you choose a cloud AI provider and confirm.

---

## 2. What kind of documents it works on

| Format | Supported | Notes |
|---|---|---|
| **PDF with selectable text** | Yes | Shown as the real pages with issues drawn over the exact words. Two-column papers work, but text can be read in a mixed order. Up to 400 pages. |
| **Word `.docx`** | Yes | Shown with formatting: headings, bold and italic, lists, tables, images. Text boxes, headers and footers, comments and tracked changes are not handled. |
| **`.txt` and `.md`** | Yes | Shown as plain text. |
| **Scanned or photographed PDF** | No | Detected and refused: it needs OCR, which is not built in. |
| **Old `.doc`, `.odt`, `.rtf`** | No | Convert to `.docx` first. |
| **LaTeX `.tex`** | No | Upload the PDF compiled from it. |
| **PowerPoint, spreadsheets, images, ebooks** | No | Not designed for them. |
| **Google Docs** | Indirectly | Download as Word (.docx) or PDF first. |

Language: **English only** (US English rules and grammar engine). Size limits: 20 MB, 20,000 paragraphs, 400 PDF pages. Password-protected PDFs do not open.

Free workarounds: scanned PDF, `sudo apt install ocrmypdf` then `ocrmypdf scan.pdf readable.pdf`. Old Word files, `libreoffice --headless --convert-to docx file.doc`.

---

## 3. Features

### 3.1 Document view
- Real PDF pages (PDF.js) with a selectable text layer; issues are drawn as underlines over the exact words, and the selected issue is filled and outlined.
- Word files keep their formatting; a suggestion that crosses bold or italic text is still applied and undone cleanly.
- Page thumbnails built from the actual document; click to jump to a page.
- Zoom (60% to 160%) that keeps your place in the document.
- Page colour: soft paper (default), dark, or original white. Pointer, pan, fit-to-view, highlight on/off, octopus on/off and strength, pause.
- A scrolling Home page (hero, About the project, Features, How it works, and a working upload drop zone), a User guide page (supported files, limits, reading the results, shortcuts, examples, troubleshooting) and an About page with the technical details (methodology, preprocessing, evaluation, limitations, privacy). The top navigation has Home, Features, How it works, User guide, About and a prominent **Open app** button. There is no sidebar. On phones the navigation becomes a menu. The footer shows GitHub and contributor links only if you set `REPO_URL` and `OWNER_NAME` in `public/index.html`.
- Easy-to-read design: a light Purple Romance palette, 17 px base text (larger on the Review document), and a **Aa: Normal** text-size button (Normal, Large, Extra large) that is remembered. Typography follows a clear scale: 17 px body text, about 46 px page title, about 30 px section headings.

### 3.2 Four ways to check the writing
| Check | What it does | Needs |
|---|---|---|
| **Quick check** | Built-in rules: common misspellings, contractions, repeated words, wordy or vague phrases, informal openers, citation format slips, absolute claims, very long sentences. Runs automatically after an upload. | Nothing |
| **Grammar check** | LanguageTool (free, open source) for grammar, spelling and punctuation, merged with the Quick check rules. Likely technical terms are skipped (words used 3+ times, acronyms, hyphenated or numeric terms, your `ignore_words.txt`). | Java 17 and `requirements-grammar.txt`; large first download |
| **AI check** | An AI model reviews the text in batches and proposes fixes with reasons. | Local Ollama (free), or a free Gemini or Groq key |
| **Citation consistency** | Compares author-year citations with your reference list (APA): missing references, year mismatches, ambiguous author-year pairs, author-count mismatches (APA 7 "et al." rule), uncited references. | A heading called References, Bibliography or Works Cited |

Quick check and Grammar check also run the citation consistency check.

### 3.3 Safe suggestions
Every suggestion from every source goes through one validator before you see it. It is rejected if it:
- cannot be located in the text;
- overlaps or conflicts with another suggestion;
- changes a number;
- adds a citation that is not in the original;
- edits an equation or notation;
- adds stronger wording (such as "proves" or "clearly");
- is a runaway rewrite (much longer than the original).

Suggestions are labelled **Likely error**, **Optional style**, **Citation check** or **Review only**. Each shows the original, the replacement, the category and the reason. The suggestion card previews the change in the sentence (old text struck through, new text in green). Items with no replacement offer **Mark reviewed** and **Dismiss** instead of Accept and Reject.

### 3.4 Reviewing
- Right-hand panel: category counts, a full list of every issue in document order (with page numbers for PDFs), kind filters, a **Fix** button on each row, the suggestion card, and the change history.
- **Accept, Reject, Undo**, plus a **Change history** of every action with time, page, original and replacement.
- Review-only items (such as very long sentences) are hidden by default and shown with the **Review only** button.
- The document scrolls only when you scroll. The magnifier button, or the **Jump** switch, scrolls to the selected issue.
- **Summary** (button on the Review screen): counts of accepted, reviewed, rejected, dismissed and open items, a table by category, the changes made, and a downloadable Markdown review report.
- **Settings** (button on the Review screen): privacy status (local or cloud), keyboard shortcuts, animation status.
- **Edit** on a PDF opens an editable revised-text view (the PDF is never changed); **View** returns to the pages. On Word and text files, Edit edits the document directly.

### 3.5 Export
- **DOCX:** headings, paragraphs and bullet lists with your accepted changes and edits.
- **Markdown:** the same revised text.
- **Review report** (Markdown) from the Summary dialog.

### 3.6 Octopus
A procedural Canvas animation: 3D mesh head with glowing eyes, eight tapered tentacles with suction cups and glowing tips. The octopus roams the window, parks beside an issue and its tentacles reach the highlighted words by inverse kinematics. It only visits issues already visible, never scrolls the page, never blocks clicks or selection, respects the system reduce-motion setting, and can be paused, hidden or set to bold (default) or soft.

### 3.7 Accessibility
Keyboard shortcuts (`j`, `k`, `a`, `r`, `u`, `?`, Esc), visible focus outlines, live announcements for selections and changes, keyboard-operable navigation, a text-size control, native dialogs, WCAG AA contrast on all text colours (checked by tests), a different underline style for each category so colour is never the only cue, and reduced-motion support.

---

## 4. Strengths

- **Private by default.** Reading, rules, grammar, citation checks, validation and export run on your computer. Cloud AI is optional and asks first.
- **Free end to end.** No account, subscription or paid service is needed.
- **Trustworthy suggestions.** Code, not just a prompt, blocks changes to numbers, citations and equations and blocks stronger claims. Unusable AI output is discarded and reported.
- **You stay in control.** Nothing changes without Accept; Undo, history and a summary show exactly what changed. The original file is never touched.
- **Works on the real document.** PDF pages and Word formatting are shown as they are, with highlights on the exact words.
- **Explains itself.** Every flag has a reason; a "Checks run" line shows what ran, what failed and how many suggestions were discarded.
- **Academic focus.** Citation consistency, technical-term handling and a skip for tables, headings and running headers.
- **Measured and tested.** 111 automated tests (28 in a real browser), a small evaluation harness, and honest reporting of limits.
- **Distinctive and accessible interface.**

---

## 5. Weaknesses and limits

**Accuracy**
- It is **less accurate than commercial tools such as Grammarly**. Expect missed problems and some wrong or unwanted suggestions.
- Quick check is rule matching, not understanding. On the built-in test set it caught about half of the labelled problems and almost none of the grammar-agreement errors (see section 11). Many of its flags are style opinions ("very small", "clearly").
- Grammar check depends on LanguageTool and flags some valid technical terms until you add them to `ignore_words.txt`.
- Small free AI models make more mistakes than large paid ones. Results vary between runs.
- Nothing checks meaning, logic, or scientific correctness.

**Documents**
- PDFs are never edited. Accepted fixes go to the revised text, history and export. The exported Word file keeps only headings, paragraphs and bullets (no bold or italic, tables, images, equations or original layout).
- Two-column PDFs, footnotes and running headers can be read in the wrong order or merged into paragraphs. A highlight is not drawn if its text cannot be found on the page (it still appears in the list).
- Scanned PDFs need OCR first. English only.
- If you edit the revised text of a PDF, fixes accepted afterwards are not merged into your edits; accept fixes first, then edit.

**Citations**
- APA author-year only. Numbered styles such as [1] are detected and reported as unsupported.
- It compares your document with itself. It **never** verifies that a source exists or supports a claim.
- A PDF reference list that does not extract as APA entries is skipped with a note.

**Engineering**
- The whole front end is one large file (`public/index.html`), which is harder to maintain than separate modules.
- The page-view libraries (PDF.js and Mammoth) need one internet connection to download. Fonts fall back to system fonts offline.
- The animation uses the CPU through Canvas; on a very old machine use Pause or hide it.
- Not independently security-audited. The server listens on localhost only; do not expose it to a network without more hardening.
- The online preview page has no server, so it lacks the citation check, Grammar check, validation endpoint and DOCX export.

---

## 6. How to run it (Ubuntu)

### 6.1 First time
```
sudo apt update && sudo apt install -y python3 python3-venv python3-pip
unzip dococto-python-full.zip          # or: python3 -m zipfile -e dococto-python-full.zip .
cd dococto-python
bash run.sh
```
`run.sh` creates a private Python environment (`.venv`), installs three free libraries (Flask, python-docx, pypdf), downloads the two page-view libraries once (internet needed that one time), and starts the server. Open **http://localhost:3000**. Stop with Ctrl+C. Next time just run `bash run.sh`.

If your path has spaces or brackets, put it in quotes: `cd "$HOME/Downloads/dococto-python (1)/dococto-python"`.

### 6.2 Optional: Grammar check
```
sudo apt install -y openjdk-17-jre-headless
source .venv/bin/activate
pip install -r requirements-grammar.txt
```
Restart `bash run.sh`. The first run downloads the grammar engine (a few hundred MB).

### 6.3 Optional: AI check
Copy `.env.example` to `.env` and set:
- Local and free: `AI_PROVIDER=ollama` (install from ollama.com, then `ollama pull llama3.1:8b`; use `llama3.2:3b` on under 8 GB RAM).
- Free cloud keys: `AI_PROVIDER=gemini` or `groq` and put the key in `AI_API_KEY`. Free tiers and model names change; set `AI_MODEL` if the default stops working.
Restart afterwards. Cloud providers receive your text only after you confirm.

### 6.4 Updating an existing install
Put `dococto-patch.zip` next to `apply_patch.sh` and run `bash apply_patch.sh`. It finds your folder, backs up every file it replaces in `.patch_backup/`, and never touches `.env`, `.venv` or `ignore_words.txt`. Then restart and hard-refresh the browser (Ctrl+Shift+R).

### 6.5 Tests
```
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q                    # 83 tests
pip install playwright && playwright install chromium
python -m pytest -q                    # 111 tests: adds 28 real-browser tests
```

### 6.6 Evaluation
```
python eval/run_eval.py --systems rules                   # always works
python eval/run_eval.py --systems rules,lt,combined       # after installing Grammar check
python eval/run_eval.py --systems rules,lt,ai,combined    # also needs Ollama or a free key
```
Results are written to `eval/RESULTS.md` and `eval/results/latest.json`.

---

## 7. Using it

1. Open the app. The Home page explains the steps. Drop a paper into **Start reviewing**, or press **Open app** and then **Upload paper**. The User guide page has the full guide.
2. Quick check runs automatically. For grammar errors also press **Grammar check**; for deeper review press **AI check**.
3. Read the right-hand list. Click an issue (or press `j` / `k`). The octopus points at it. Use the magnifier button to scroll to it.
4. Press **Fix** (or `a`) to accept, **Reject** (or `r`) to keep your words, **Undo** (or `u`) to reverse. Items with no replacement use **Mark reviewed** and **Dismiss**.
5. Open **Summary** to see what you did and download a review report. Use **DOCX** or **Markdown** to export the revised text.

| Control | What it does |
|---|---|
| Quick check / Grammar check / AI check | Run that check (each replaces the current issue list) |
| View / Edit | Read the document / edit text (PDF: edit the revised text) |
| DOCX / Markdown / Upload | Export the revised text / import a file |
| Likely errors, Optional style, Citation checks, Review only | Show or hide that kind of suggestion |
| Zoom, pointer, pan, magnifier, fit | Navigate the page; the magnifier scrolls to the selected issue |
| Page: soft / dark / original | PDF page colour |
| Octopus: bold / soft, Octopus, Highlights, Pause, Jump | Animation and highlight controls |
| `j` `k` `a` `r` `u` `?` Esc | Next, previous, accept, reject, undo, help, close |

---

## 8. Configuration

| Variable (`.env`) | Purpose | Default |
|---|---|---|
| `AI_PROVIDER` | `ollama`, `gemini`, `groq`, `anthropic` | `ollama` |
| `AI_MODEL` | Model name | provider default |
| `AI_API_KEY` | Key for cloud providers (never sent to the browser) | empty |
| `PORT` | Server port | `3000` |
| `OLLAMA_URL` | Ollama address | `http://localhost:11434` |
| `LT_LANG` | LanguageTool language | `en-US` |

Other files you can edit: `ignore_words.txt` (words the grammar check should not flag, one per line).

---

## 9. Privacy and security

| Feature | Where text is processed |
|---|---|
| Viewing, Quick check, citation check, validation, export | Your computer |
| Grammar check (LanguageTool) | Your computer |
| AI check with Ollama | Your computer |
| AI check with Gemini, Groq or Anthropic | That provider, after you confirm |

- The server stores nothing and logs no document text. API keys stay in `.env` on the server.
- Untrusted text (from papers and AI answers) is escaped before display. Tests check that injected HTML and scripts do not run.
- Uploads are limited to 20 MB, 20,000 paragraphs and 400 PDF pages.
- Not independently audited. Keep it on localhost.

---

## 10. How it is built

| Part | Technology |
|---|---|
| Front end | One HTML file with CSS and vanilla JavaScript; Canvas 2D for the octopus; PDF.js and Mammoth for viewing |
| Server | Python 3, Flask, python-docx, pypdf; optional LanguageTool (Java) |
| AI | Ollama, Gemini, Groq or Anthropic through plain HTTPS from the server |
| Tests | pytest; Playwright with Chromium for browser tests |

Flow: the page extracts paragraphs from the document; the server runs the checks; every suggestion passes `validate_issues`; the page anchors each suggestion by paragraph, exact phrase and occurrence number (never by phrase alone) and draws it; accept, reject and undo update the revised text and history, which feed export and the report.

```
app.py                  server and API
dococto/validate.py     suggestion validation and AI-answer parsing
dococto/rules.py        Python copy of the Quick check rules (kept in sync by a test)
dococto/citations.py    APA citation consistency
dococto/export.py       DOCX export
dococto/metrics.py      evaluation scoring
public/index.html       the whole front end
eval/                   dataset, runner, results
tests/                  111 tests
docs/                   documentation and screenshots
scripts/get_vendor.py   one-time download of PDF.js and Mammoth
run.sh, apply_patch.sh  start and update scripts
```

---

## 11. Testing and evaluation

**Tests.** 111 automated tests pass in the build environment: parsing and malformed or oversized files, API errors and invalid AI answers, suggestion validation, citation consistency, DOCX export, evaluation scoring, a check that the Python rules match the browser's, escaping, colour contrast, and 21 real-browser tests (accept, reject, undo, history, shortcuts, summary, no self-scrolling, injection safety, DOCX download, formatted Word text, PDF zoom position and PDF edit mode with a stubbed PDF.js, the welcome guide, and page and octopus controls).

**Evaluation (built-in rules only).** On a 41-paragraph set with 35 labelled issues:

| Measure | Result |
|---|---|
| Precision (strict span match) | 82% |
| Recall | 51% |
| F1 | 63% |
| Lenient precision / recall | 86% / 54% |
| False alarms per 1,000 words | 10 |
| Clean paragraphs wrongly flagged | 12% |
| Correct category among matches | 94% |
| Correct fix among matches | 89% |
| Recall by type | citations 100%, style 100%, structure 100%, clarity 71%, repetition 50%, grammar 12% |

**Read this before quoting these numbers.** The dataset is small, was labelled by the AI assistant that helped build DocOcto (not by independent humans), and partly matches what the rules were built to find. Results on real papers will differ. LanguageTool and AI have not been scored yet because they were not available in the build environment; run `python eval/run_eval.py --systems rules,lt,ai,combined` to measure them.

---

## 12. What has been verified

| Area | Evidence |
|---|---|
| PDF page view, highlights, issue list on a real 22-page security paper | Your screenshot (73 issues found) |
| Quick check, accept, undo, reject, history, shortcuts, summary, citations, DOCX export, welcome guide, no self-scrolling | Real-browser tests in the build environment, plus screenshots |
| PDF zoom position and PDF edit mode | Real-browser tests with a stubbed PDF.js (not the real library) |
| Test suite on your machine | You ran the earlier 48 tests; the latest suite has not been run by you |
| Not yet verified by anyone | Real Word upload with Mammoth, Grammar check, AI check, a screen reader, a scanned PDF, the latest changes on your real PDF |

---

## 13. Troubleshooting

| Problem | Fix |
|---|---|
| `venv` error | `sudo apt install python3-venv python3-pip` |
| `externally-managed-environment` | Run `source .venv/bin/activate` first, or use `bash run.sh` |
| `werkzeug` or `flask` not found when testing | You are in the wrong environment; `source .venv/bin/activate` inside the project folder |
| Port in use | Set `PORT=3001` in `.env` |
| Page view or DOCX formatting does not load | Needs internet once: run `python scripts/get_vendor.py`; otherwise it falls back to plain text and says so |
| "No selectable text found" | The PDF is scanned; use `ocrmypdf` first |
| "Cannot reach Ollama" | Start Ollama and run `ollama pull llama3.1:8b` |
| "AI_API_KEY is not set" | Add the key to `.env` and restart, or use Quick check |
| Grammar check cannot start | Install Java 17 and `requirements-grammar.txt` (section 6.2) |
| Old interface after updating | Hard-refresh the browser (Ctrl+Shift+R) |
| Many flags look irrelevant | Hide Optional style or Review only; add terms to `ignore_words.txt`; reject freely |
| Something broke | Press F12, open the Console tab, and copy the message with a screenshot |

---

## 14. Possible next steps

- Run and report the LanguageTool and AI evaluation; have a human review the dataset labels.
- Test with real Word files and a wider set of PDFs; tune the rules from real results.
- Optional: OCR for scanned PDFs, numeric citation styles, saved review sessions, a custom vocabulary screen, splitting the front end into modules.
- Not planned: user accounts, cloud storage, collaboration, a framework rewrite.
