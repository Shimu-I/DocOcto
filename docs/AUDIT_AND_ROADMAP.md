# DocOcto: Audit, Roadmap and Milestone Log

"Verified" means I ran it or read the exact code in this audit. "Assumed" or "untested" means I did not run it.

## 1. Audit (before Milestone 1)

| Area | Current state | Evidence | Recommended action | Priority |
|---|---|---|---|---|
| Output escaping | Suggestion panel inserted paper text, AI suggestions and AI reasons into `innerHTML` unescaped (XSS from a crafted PDF/DOCX or a model answer) | Verified: 3 unescaped assignments (`#so2`, `#ss`, `#sw`); parser returns `<img onerror=...>` text raw | Escape all untrusted text; add regression test | P0 |
| AI output trust | Prompt asked the model not to invent or strengthen; nothing enforced it. Client only checked the phrase could be found | Verified in code | Server-side deterministic validation (numbers, citations, equations, strong wording, overlaps, schema) | P1 |
| Automated tests | None | Verified: no tests directory | pytest suite for parsing, API, validation, export | P1 |
| Upload limits | 50 MB cap, no paragraph or page cap; oversize returned a misleading 422 | Verified: 51 MB gave 422; 5,000-paragraph DOCX parsed in 4.6 s with no cap | 20 MB cap with 413, paragraph cap, PDF page cap | P1 |
| Privacy transparency | Cloud providers receive document text; UI never says so | Verified: no confirm dialog, no config endpoint | `/api/config` plus a confirmation before the first cloud send | P1 |
| DOCX export | Not implemented (Markdown only) | Verified | `.docx` export of headings, paragraphs, bullets with an honest format note | P1 |
| Concurrency | LanguageTool initialised without a lock; two parallel requests could start two engines | Verified in code; race not reproduced | Add lock | P2 |
| Anchoring | Paragraph + phrase + occurrence; overlapping ranges dropped client-side | Verified in code; now also covered by server tests | Keep; validate server-side | Done |
| Accept/Reject/Undo | Works in the browser (DOM text replacement, undo stack) | Read in code; **untested by automation** | Extract logic into testable module or add browser tests | P1 (next) |
| Evaluation | No dataset, no metrics; the guide's accuracy statements are qualitative | Verified | Build labeled dataset and compare the four workflows | P1 (next) |
| Citation consistency | Only format slips (comma, "et al.") | Verified | APA author-year in-text vs reference list | P2 |
| Accessibility | Labels and focus styles partly present; no live announcements, no review summary, no before/after view | Read in code; not audited with a screen reader | Targeted improvements | P2 |
| Guide vs code | Guide said 50 MB limit and Markdown-only export | Verified | Updated in this milestone | Done |
| Documented gaps | No visual check against the reference, no real-PDF, LanguageTool, Ollama, Gemini or Groq runs | Stated in guide | Verify on a real machine | P1 |

## 2. Roadmap

| # | Milestone | Effort | Acceptance criteria | Skills shown |
|---|---|---|---|---|
| M1 | Reliability and trust (**done**, see below) | 1 to 2 days | Tests pass; XSS fixed; validation, limits, DOCX export, privacy notice | Testing, security, API design |
| M2 | Evaluation harness | 2 to 3 days | 40 to 60 labeled paragraphs; script reports precision, recall, false-positive rate, location accuracy, latency for rules, LanguageTool, AI and combined; results file committed with limitations | Experiment design, metrics |
| M3 | Browser-side tests | 1 day | Accept, reject, undo, edit, anchoring covered by automated browser or module tests | Front-end testing |
| M4 | APA citation consistency | 2 days | In-text vs reference list: missing, uncited, ambiguous; tests; explicitly not source verification | Parsing, domain logic |
| M5 | UX and accessibility | 2 days | Review summary, before/after view, live announcements, keyboard pass, contrast check | Accessibility |
| M6 | Portfolio package | 1 day | Real screenshots or demo clip, architecture diagram, final README, sample non-confidential documents | Communication |

Optional, evaluate later: custom vocabulary UI (high value, low cost), saved review sessions (medium, low-medium), PDF page overlay (high value, high cost), OCR (medium, medium, adds Tesseract), more citation styles (medium, high), framework migration (not justified by the audit).

## 3. Milestone 1 log

Changed: `dococto/validate.py` (new), `dococto/export.py` (new), `app.py` (limits, config, validate, export, lock, AI answer parsing), `public/index.html` (escaping, kind labels, privacy notice, checks-run line, DOCX button), `tests/` (new), `requirements-dev.txt`, README.

Test results: 48 passed, 0 failed. These ran with a minimal stand-in runner because `pytest` could not be installed in the build sandbox (no internet). Run `python -m pytest -q` yourself to confirm with real pytest.

Not done or not verified: browser behaviour of the new buttons, privacy dialog, DOCX opening in Word or LibreOffice, real PDFs, LanguageTool and cloud providers, and the front-end accept/reject/undo logic.

## 4. Status update
M1 done. M2 built (rules scored; LanguageTool and AI not yet run; labels author-made). M4 built. M5 built (contrast verified by test; keyboard and screen reader not yet verified by a person). M6 partly done (README and architecture diagram; screenshots and sample documents missing). M3 (browser tests for Accept, Reject, Undo) is not started because it needs a real browser. See `PROGRESS.md`.

M3 update: 13 real-browser tests (tests/test_browser.py) now cover accept, reject, undo, history, keyboard shortcuts, the summary dialog, no self-scrolling, injection safety, DOCX download, and a suggestion that spans italic text in the formatted-DOCX path (Mammoth stubbed). They passed twice in headless Chromium in the build environment. Not covered: the PDF page view, the real Mammoth and PDF.js libraries, and screen readers.
