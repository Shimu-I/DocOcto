"""Deterministic checks for suggestions from ANY source (rules, LanguageTool, AI).
Prompts can be ignored by a model; these checks cannot."""
import json, re

CATS = {"gram", "clar", "style", "rep", "cit", "str"}
NUM = re.compile(r"\d+(?:[.,]\d+)?")
CITE = re.compile(r"\([^()]*\d{4}[a-z]?\)|\[\d+(?:\s*[,\u2013-]\s*\d+)*\]")
MATH = re.compile(r"[=<>\u00b1\u00d7\u00f7\u2211\u222b\u221a\u2248\u2260\u2264\u2265\u2208]|\$[^$]+\$|\\[a-zA-Z]+")
STRONG = {"proves", "proven", "prove", "always", "never", "undoubtedly", "definitely", "conclusively", "significantly", "clearly", "obviously"}

def _norm(c): return re.sub(r"[^0-9a-z]", "", c.lower())   # "(Smith, 2019)" and "(Smith 2019)" are the same citation
def _words(s): return set(re.findall(r"[a-z]+", s.lower()))

def parse_ai_json(text):
    """Pull a JSON list out of a model answer. Raises ValueError with a readable reason."""
    t = re.sub(r"```(?:json)?", "", text or "").strip()
    i, j = t.find("["), t.rfind("]")
    if i < 0 or j < i: raise ValueError("no JSON list found in the AI answer")
    try: data = json.loads(t[i:j + 1])
    except json.JSONDecodeError as e: raise ValueError("the AI answer is not valid JSON (%s)" % e.msg)
    if not isinstance(data, list): raise ValueError("expected a JSON list")
    return data

def locate(text, phrase, occ):
    """Start offset of the occ-th (1-based, overlapping) occurrence, or -1."""
    pos = -1
    for _ in range(occ):
        pos = text.find(phrase, pos + 1)
        if pos < 0: return -1
    return pos

def unsafe_reason(o, s):
    if len(s) > 3 * len(o) + 40: return "replacement is much longer than the original (possible rewrite)"
    if {_norm(c) for c in CITE.findall(s)} - {_norm(c) for c in CITE.findall(o)}: return "replacement adds a citation that is not in the original"
    if set(NUM.findall(s)) != set(NUM.findall(o)): return "replacement changes a number"
    if MATH.search(o): return "original contains an equation or notation"
    strong = (_words(s) & STRONG) - _words(o)
    if strong: return "replacement adds stronger wording (%s)" % ", ".join(sorted(strong))
    return None

def validate_issues(paras, items):
    """Return (accepted, rejected). Accepted items carry offsets a/b and a kind:
    'error' (objective grammar), 'style' (optional), 'review' (flag only, no replacement)."""
    bad, cand = [], []
    def rej(it, why): bad.append({"item": it if isinstance(it, dict) else {"raw": str(it)[:80]}, "reason": why})
    for it in items:
        if not isinstance(it, dict): rej(it, "not an object"); continue
        p, o, s, cat, occ = it.get("p"), it.get("o"), it.get("s"), it.get("cat"), it.get("occ", 1)
        if not isinstance(p, int) or isinstance(p, bool) or not 0 <= p < len(paras): rej(it, "paragraph index out of range"); continue
        if not isinstance(o, str) or not o.strip(): rej(it, "missing original phrase"); continue
        if not isinstance(s, str): rej(it, "missing replacement"); continue
        if cat not in CATS: rej(it, "unknown category"); continue
        if not isinstance(occ, int) or isinstance(occ, bool) or occ < 1: occ = 1
        a = locate(paras[p], o, occ)
        if a < 0: rej(it, "phrase not found in that paragraph (occurrence %d)" % occ); continue
        why = unsafe_reason(o, s) if s != o else None
        if why: rej(it, why); continue
        cand.append((p, a, a + len(o), it, occ))
    cand.sort(key=lambda c: (c[0], c[1], -(c[2] - c[1])))
    last, ok = {}, []
    for p, a, b, it, occ in cand:
        prev = last.get(p)
        if prev and a < prev[1]:
            if (a, b) == (prev[0], prev[1]):
                rej(it, "duplicate" if it["s"] == prev[2] else "conflicts with another suggestion for the same text")
            else: rej(it, "overlaps another suggestion")
            continue
        last[p] = (a, b, it["s"])
        w = it.get("w")
        w = [str(x)[:300] for x in w[:3]] if isinstance(w, list) and w else ["Suggested by the check."]
        kind = "check" if it.get("kind") == "check" and it["s"] == it["o"] else "review" if it["s"] == it["o"] else "error" if it["cat"] == "gram" else "style"
        ok.append({"p": p, "o": it["o"], "occ": occ, "cat": it["cat"], "s": it["s"], "w": w, "kind": kind, "a": a, "b": b})
    return ok, bad
