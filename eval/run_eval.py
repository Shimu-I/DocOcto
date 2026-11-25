"""Compare rules, LanguageTool, AI and a combined workflow on eval/dataset.json.
Usage: python eval/run_eval.py --systems rules,lt,ai,combined     (systems that are not available are skipped and reported)"""
import argparse, datetime, json, os, platform, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from dococto.rules import quick_check
from dococto.metrics import load_dataset, score
from dococto.validate import validate_issues, parse_ai_json

class Skip(Exception): pass

def run_rules(texts):
    t = time.perf_counter(); p = quick_check(texts); return p, time.perf_counter() - t, {}

def run_lt(texts):
    try: import language_tool_python
    except ImportError: raise Skip("language-tool-python is not installed (pip install -r requirements-grammar.txt; needs Java 17)")
    import app
    try: tool = language_tool_python.LanguageTool(os.environ.get("LT_LANG", "en-US"))
    except Exception as e: raise Skip("LanguageTool could not start: %s" % e)
    t0, preds = time.perf_counter(), []
    for pi, t in enumerate(texts):
        for m in tool.check(t):
            ln = getattr(m, "errorLength", None) or getattr(m, "error_length", None) or len(getattr(m, "matchedText", "") or "")
            o = t[m.offset:m.offset + ln]
            if not o.strip(): continue
            reps = list(m.replacements or [])
            preds.append({"p": pi, "o": o, "occ": sum(1 for i in range(m.offset) if t.startswith(o, i)) + 1,
                          "cat": app.CAT.get((getattr(m, "category", "") or "").upper(), "clar"), "s": reps[0] if reps else o})
    return preds, time.perf_counter() - t0, {}

PROMPT = ("You are a careful academic copy-editor. Below are paragraphs from a research paper, each prefixed with [index]. Find genuine writing issues. "
 'Return ONLY a JSON array. Each item: {"p":paragraph index,"o":exact substring copied from that paragraph (at most 12 words),"occ":which occurrence of o in the paragraph (1 if unique),'
 '"cat":"gram"|"clar"|"style"|"rep"|"cit"|"str","s":replacement text for o only,"w":[one or two short reasons]}. Categories: gram=grammar/spelling, clar=vague or unclear wording, '
 "style=informal or non-academic tone, rep=repetition/redundancy, cit=citation formatting or reference consistency, str=transitions/structure/flow. Rules: keep the author's meaning; "
 "never invent data, results, sources or citations; never make a claim stronger; do not touch equations or numbers; for citation items only flag formatting problems, never claim a source was verified; "
 "at most 8 items per paragraph; return [] if there are no issues.\n\n")   # copy of the prompt in public/index.html; keep in sync

def run_ai(texts):
    import app
    if app.P != "ollama" and not app.KEY: raise Skip("no AI configured (set AI_PROVIDER and AI_API_KEY in .env, or use Ollama)")
    batches, cur, n = [], [], 0
    for i, t in enumerate(texts):
        if n > 5000: batches.append(cur); cur, n = [], 0
        cur.append(i); n += len(t)
    if cur: batches.append(cur)
    t0, preds, tok, failed = time.perf_counter(), [], 0, 0
    for b in batches:
        prompt = PROMPT + "\n\n".join("[%d] %s" % (i, texts[i]) for i in b)
        try: ans = app.ask(prompt); preds += parse_ai_json(ans); tok += (len(prompt) + len(ans)) // 4
        except Exception as e: failed += 1; print("  AI batch failed:", e)
    if failed == len(batches): raise Skip("every AI request failed, so nothing was scored (see the message above)")
    preds = [p for p in preds if isinstance(p, dict) and isinstance(p.get("p"), int) and 0 <= p["p"] < len(texts) and isinstance(p.get("o"), str)]
    return preds, time.perf_counter() - t0, {"model": "%s/%s" % (app.P, app.MODEL), "approx_tokens": tok, "failed_batches": failed}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--systems", default="rules,lt,ai,combined"); a = ap.parse_args()
    data = load_dataset(os.path.join(ROOT, "eval", "dataset.json")); texts = [d["text"] for d in data]
    want = [s.strip() for s in a.systems.split(",")]; res, notes, raw = {}, {}, {}
    for name, fn in (("rules", run_rules), ("lt", run_lt), ("ai", run_ai)):
        if name not in want and "combined" not in want: continue
        try: preds, sec, extra = fn(texts); raw[name] = preds
        except Skip as e: notes[name] = "skipped: %s" % e; continue
        if name in want:
            r = score(data, preds); r.update(seconds=sec, seconds_per_paragraph=sec / len(texts), **extra); res[name] = r
    if "combined" in want and raw:
        items = [p for ps in raw.values() for p in ps]; ok, bad = validate_issues(texts, items)
        r = score(data, ok); secs = sum(res[k]["seconds"] for k in raw if k in res)
        r.update(parts=list(raw), discarded_by_validation=len(bad), seconds=secs, seconds_per_paragraph=secs / len(texts)); res["combined"] = r
    elif "combined" in want: notes["combined"] = "skipped: no component system ran"
    out = {"date": datetime.date.today().isoformat(), "python": platform.python_version(), "n_paragraphs": len(data), "systems": res, "notes": notes}
    os.makedirs(os.path.join(ROOT, "eval", "results"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "eval", "results", "latest.json"), "w"), indent=1)
    write_report(out); print(open(os.path.join(ROOT, "eval", "RESULTS.md")).read())

def f(x): return "n/a" if x is None else "%.0f%%" % (100 * x)
def write_report(o):
    L = ["# Evaluation results", "", "Generated by `python eval/run_eval.py` on %s (Python %s). %d paragraphs. **Read the limitations below before quoting any number.**" % (o["date"], o["python"], o["n_paragraphs"]), "",
         "| System | Precision | Recall | F1 | Lenient P / R | False alarms per 1,000 words | Clean paragraphs flagged | Category correct | Fix correct | Seconds per paragraph |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in o["systems"].items():
        s, l = r["strict"], r["lenient"]
        L.append("| %s | %s | %s | %s | %s / %s | %.0f | %s | %s | %s | %.3f |" % (k, f(s["precision"]), f(s["recall"]), f(s["f1"]), f(l["precision"]), f(l["recall"]), r["fp_per_1000_words"], f(r["clean_paragraph_false_alarm_rate"]), f(r["category_accuracy"]), f(r["fix_accuracy"]), r["seconds_per_paragraph"]))
    L += ["", "Recall by issue category (strict):", ""]
    for k, r in o["systems"].items(): L.append("- **%s**: %s" % (k, ", ".join("%s %s" % (c, f(v)) for c, v in r["recall_by_category"].items())))
    for k, r in o["systems"].items():
        extra = {x: r[x] for x in ("model", "approx_tokens", "failed_batches", "parts", "discarded_by_validation") if x in r}
        if extra: L.append("- %s details: %s" % (k, extra))
    if o["notes"]: L += ["", "Not run:", ""] + ["- **%s** %s" % (k, v) for k, v in o["notes"].items()]
    L += ["", "## How the numbers are computed", "",
          "- A prediction is a **true positive** when it is in the same paragraph as a gold issue and the two text spans overlap with IoU of at least 0.5 (strict) or at all (lenient). Each gold issue and each prediction counts once.",
          "- **Precision** = TP / predictions. **Recall** = TP / gold issues. **F1** is their harmonic mean. **False alarms per 1,000 words** = unmatched predictions per 1,000 words. **Clean paragraphs flagged** = share of paragraphs with no gold issue that got at least one prediction.",
          "- **Category correct** and **Fix correct** are measured only among true positives. A fix is correct if it equals one of the acceptable fixes listed in the dataset.",
          "- **Combined** merges all systems that ran and passes them through the same validation the app uses (unlocatable, overlapping, number-changing and similar suggestions are discarded).", "",
          "## Limitations", "",
          "- The dataset is small and was **labeled by the AI assistant that helped build DocOcto, not by independent human reviewers**. Treat it as a seed set. Have a human check every label before using results in a CV or paper.",
          "- It mixes simple errors the rules were designed for with errors they cannot detect, so rule results partly reflect how the examples were chosen. Results on real papers will differ.",
          "- Phrases are anchored by exact text, so a prediction that flags a slightly different span can count as a miss under the strict rule.",
          "- AI results come from one run and can vary between runs. Cost is reported only as approximate token counts, not money.",
          "- Meaning preservation is not measured automatically; read the suggested fixes yourself."]
    open(os.path.join(ROOT, "eval", "RESULTS.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

if __name__ == "__main__": main()
