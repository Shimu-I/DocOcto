# DocOcto: Progress Tracker

Last updated: 2026-11-10. Edit the checkboxes and tables as you test. Anything not marked as tested has not been tested.

## 1. Where we are

| Measure | Estimate | How it was judged |
|---|---|---|
| Working product built | about 70% | Features written compared with the original brief |
| Portfolio upgrade built | about 82% | Milestone 1 and most of milestone 2 done; milestones 3 to 6 not started |
| Verified by real use | about 45% | Only what you confirmed in screenshots and your own pytest run |

These percentages are rough judgments, not measurements.

**Status legend:** Done = written and working as far as known. Tested (auto) = covered by automated tests. Tested (you) = you ran it and confirmed it. Untested = written but never run in a real browser or on real files. Missing = not built.

## 2. Feature tracker

| Feature | Built | Tested (auto) | Tested (you) | Notes |
|---|---|---|---|---|
| Layout and dark neon style | Done | No | Seen in screenshots | Never compared side by side with the reference image |
| Octopus: 3D head, 8 tentacles, suction cups | Done | No | Seen in screenshots | |
| Octopus roams and reaches text | Done | No | Seen in screenshots | Latest scroll behavior change untested |
| Upload DOCX, PDF, TXT, MD | Done | Server side only | PDF yes | DOCX, TXT and MD not yet confirmed by you |
| PDF page view with highlights | Done | No | Yes (screenshot) | Issues whose text cannot be found on the page are listed but not drawn |
| DOCX formatted view | Done | No | No | Needs a real DOCX test |
| Quick check (rules) | Done | Partly (sample text) | Yes | Many results are style opinions |
| Grammar check (LanguageTool) | Done | No | No | Needs Java and a large first download |
| AI check (Ollama, Gemini, Groq) | Done | Error paths only | No | Never run against a real provider |
| Suggestion safety checks (numbers, citations, equations, overlaps, schema) | Done | Yes, 48 tests pass | Yes (your pytest run) | |
| Issue list, category filters, kind filters | Done | No | Seen in screenshots | |
| Accept, Reject, Dismiss, Undo | Done | No | Used | Browser logic has no automated tests |
| Change history | Done | No | No | Added after your last test |
| Green label for accepted PDF changes | Done | No | No | Added after your last test |
| Jump to issue switch (no surprise scrolling) | Done | No | No | Needs your confirmation |
| Privacy notice before cloud AI | Done | Config endpoint only | No | |
| DOCX export | Done | Yes (file contents) | No | Not yet opened in Word or LibreOffice |
| Markdown export | Done | No | No | |
| Upload limits (20 MB, 20,000 paragraphs, 400 pages) | Done | Yes | No | |
| Patch installer (`apply_patch.sh`) | Done | Tested on a fake install | Unknown | Not confirmed on your machine |
| Escaping fix (XSS) | Done | Text check only | No | Not tested in a browser |
| Evaluation dataset, scoring and runner | Built; rules scored | Yes (metrics and rules tests) | No | LanguageTool and AI results still need your run. Labels were made by the AI assistant, not independent humans |
| Browser tests (Accept, Reject, Undo, scroll, shortcuts, XSS, export) | Built | Yes, 13 real-browser tests pass here | No | Not covered: PDF page view, real Mammoth/PDF.js, screen reader, octopus reaching text |
| APA citation consistency | Built | Yes (11 tests) | No | Runs inside Quick check and Grammar check; not in the online page; PDF reference lists may not parse |
| Review summary, report download, Settings/help dialog, before-and-after preview | Built | Static checks only | No | Open the Summary and Settings items in the sidebar |
| Keyboard shortcuts (j, k, a, r, u, ?) and screen-reader announcements | Built | Static checks only | No | Needs your keyboard test; screen reader never tried |
| Colour contrast (WCAG AA) | Done | Yes (ratios computed in tests) | No | Visual check still useful |
| OCR for scanned PDFs | Missing | | | Optional |
| Architecture diagram, final README, screenshots | Built | No | No | Screenshots are real captures of a sample document (no PDF view). A sample non-confidential document and your own thesis screenshots are still worth adding |

## 3. Test log

| What | Where it ran | Result |
|---|---|---|
| Python test suite (parsing, errors, validation, export, escaping check) | Build sandbox, stand-in runner | 48 passed |
| Same suite with real pytest | Your Ubuntu machine | 48 passed in 0.61 s |
| Syntax check of the page JavaScript | Build sandbox | Passes |
| Full suite incl. new metrics, rules and browser-vs-Python rules parity tests | Build sandbox, stand-in runner | 100 passed incl. 21 real-browser tests (not yet run on your machine) |
| Evaluation of rules on 41 paragraphs | Build sandbox | See `eval/RESULTS.md`; LanguageTool and AI not run |
| Quick check rules on sample text | Build sandbox | Expected issues found; table rows and 173-word blocks not flagged |
| 13 end-to-end tests in headless Chromium (accept/undo/reject, 8 s no-scroll check, Jump switch, shortcuts, summary, injection, DOCX download, stubbed formatted DOCX across italic text) | Build sandbox | All pass, run twice |
| Patch installer on a fake old install | Build sandbox | Replaced files, kept `.env`, `.venv`, `ignore_words.txt`, made a backup |
| PDF upload, page view, highlights, octopus | Your machine, by screenshot | Worked; 33 issues found on `thesis_full.pdf` |
| Accept on a review-only item | Your machine, by screenshot | Nothing changed (expected, no replacement); led to the Mark reviewed fix |

**Not yet run by anyone (PDF page view and real Mammoth/PDF.js are not covered by any automated test):** real DOCX upload with Mammoth, Grammar check, AI check, DOCX export opened in Word, a screen reader, keyboard-only use, a scanned PDF, a very large PDF, the test suite after the latest changes.

## 4. Your testing checklist

Tick these as you go and paste any failure to me.

- [ ] On your real PDF: zoom in and out and confirm you stay on the same page
- [ ] On your real PDF: press Edit, change a sentence, press View, then DOCX and check your edit is in the file
- [ ] Check the new softer page colour, the Page and Octopus buttons, and the welcome guide
- [ ] Apply the latest patch (`bash apply_patch.sh`), restart with `bash run.sh`, hard-refresh the browser (Ctrl+Shift+R)
- [ ] Run `python -m pytest -q` again and note the result
- [ ] The document no longer scrolls by itself
- [ ] Magnifier button scrolls to the selected issue
- [ ] Accept on a real fix: green label appears above the PDF highlight
- [ ] Change history lists the accept, and Undo adds an "undone" entry
- [ ] Review-only items are hidden by default and appear with the Review only button
- [ ] Upload a real `.docx`: formatting, tables and images look right
- [ ] Accept a fix in the DOCX view and see the text change in place
- [ ] Press the DOCX button, open the file in Word or LibreOffice
- [ ] Grammar check (after installing Java and `requirements-grammar.txt`)
- [ ] AI check with Ollama, then optionally a free Gemini or Groq key
- [ ] Press Tab through the page and confirm you can see where focus is
- [ ] Press j, k, a, r, u and ? with focus on the page and confirm each works
- [ ] Open Summary and Settings in the sidebar; press Download report and open the file
- [ ] Check that Accept shows a red/green before-and-after preview
- [ ] Run `python -m pytest -q` after applying the latest patch (expect 100 passed with Playwright installed, 83 without)
- [ ] Upload a thesis with a References section and check the Citation checks list (missing, uncited, ambiguous)
- [ ] Run `python eval/run_eval.py --systems rules` and open `eval/RESULTS.md`
- [ ] Read `eval/dataset.json` and fix any label you disagree with
- [ ] After installing LanguageTool: `python eval/run_eval.py --systems rules,lt,combined`
- [ ] With Ollama running: `python eval/run_eval.py --systems rules,lt,ai,combined`

## 5. Roadmap

| # | Milestone | Status | Acceptance criteria |
|---|---|---|---|
| M1 | Reliability and trust | Done, partly verified | Tests pass; escaping fixed; validation; limits; DOCX export; privacy notice |
| M1.5 | Real page view and review usability | Built, mostly untested | PDF pages, DOCX formatting, history, kind filters, no auto-scroll |
| M2 | Evaluation harness | Built; rules scored, LanguageTool and AI not yet run | 40 to 60 labeled paragraphs; precision, recall, false positives, location accuracy, speed for rules, LanguageTool, AI and combined; results file |
| M3 | Browser tests | Built; 13 pass in Chromium here, not yet run on your machine | Accept, Reject, Undo, edit and anchoring covered automatically |
| M4 | APA citation consistency | Built, not yet tried on a real thesis | In-text vs reference list: missing, uncited, ambiguous; tests; clearly not source verification |
| M5 | UX and accessibility | Built; contrast checked by test, keyboard and screen reader untested | Review summary, before-and-after view, live announcements, keyboard and contrast pass |
| M6 | Portfolio package | Partly done (README, architecture diagram); your screenshots and sample documents missing | Real screenshots, architecture diagram, final README, sample documents |

## 6. Open issues and known limits

- Accuracy is below Grammarly. Rule results include style opinions. Review each suggestion.
- A PDF cannot be edited in place. Accepted changes go into the revised text and the history.
- Two-column PDFs can place text in a mixed order. Hyphenated words at line ends can stop a highlight from being placed.
- No OCR. Scanned PDFs are detected and refused.
- DOCX export keeps only headings, paragraphs and bullet lists.
- The page viewers need two small libraries downloaded once (internet needed one time).
- The front end is one large file. Splitting it would help maintainability.
- `docs/` and the project guide describe an earlier version in places and need updating in M6.
- The LanguageTool engine may flag technical terms; add them to `ignore_words.txt`.

## 7. Change log

| Version | What changed |
|---|---|
| v0.1 | Layout and the first octopus |
| v0.2 | 3D head, 8 tentacles, suction cups, roaming and reaching |
| v0.3 | Upload, Quick check, AI check, Markdown export, free providers, Python edition for Ubuntu |
| v0.4 | Issue list, Fix buttons, LanguageTool grammar check |
| v0.5 (Milestone 1) | Escaping fix, server-side validation, upload limits, privacy notice, DOCX export, 48 tests |
| v0.6 | PDF page view with highlights, formatted DOCX view, auto Quick check on upload, patch installer |
| v0.7 | No auto-scroll (Jump to issue switch), change history, kind filters, Mark reviewed and Dismiss, fewer false flags on tables and headers |
| v0.8 | Evaluation dataset, scoring, runner and Python copy of the rules; prose detection fixed; bug fixed where a citation comma fix was rejected as an invented citation |
| v0.9 | APA author-year citation consistency check (missing, year mismatch, ambiguous, author count, uncited) with 11 tests; new Citation checks filter |
| v0.10 | Review summary and report download, Settings/help dialog, shortcuts, announcements, before-and-after preview, contrast tests, portfolio README with architecture diagram |
| v0.15 | Redesign from the UI/UX brief: top navigation (Home, Features, How it works, User guide, About, Open app), scrolling home page with About the project, Features, How it works and a working drop zone, user guide with supported files and result-reading, About page with methodology, preprocessing, evaluation and limitations, footer, mobile menu, loading indicator, type scale. 28 real-browser tests (111 total). Found and fixed a bug where an unset GitHub link was visible |
| v0.14 | Octopus made dark and bold by default (darker plum and aubergine, thicker lines, deeper fill); Octopus button now toggles bold and soft |
| v0.13 | New design: light Purple Romance palette, larger text with a Text size button, no sidebar, Home page with features section, Manual and About pages, octopus recoloured for the light theme. Tests updated (104; 21 in a real browser) |
| v0.12 | Fixes from your PDF test: zoom keeps your place, Edit works on PDFs (revised-text editor), softer page colours and quieter highlights, subtle octopus, calmer header buttons, welcome guide on open. 4 new browser tests (zoom tested with a stubbed PDF.js) |
| v0.11 | 13 real-browser tests; confirmed in Chromium that accept/undo/reject, no self-scrolling, shortcuts, summary and DOCX export work on the text and stubbed formatted-DOCX paths |

## 8. How to keep this file current

After each test, change the matching row from Untested or No to Yes or Failed, and add a line to the test log with what you ran, where, and the result. When something breaks, add it to section 6 until it is fixed. Update the percentages only when a milestone changes status.
