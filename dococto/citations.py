"""APA-style author-year citation CONSISTENCY check (in-text citations vs the reference list).
It never checks that a source exists or supports a claim; it only compares what is inside this document."""
import re

NAME = r"[A-Z][A-Za-z'\u2019\-]+"
AUTH = r"(?:%s(?:\set\sal\.?|\s(?:and|&)\s%s)?)" % (NAME, NAME)
YEAR = r"\d{4}[a-z]?"
NARR = re.compile(r"(%s)\s\((%s)\)" % (AUTH, YEAR))
PART = re.compile(r"^(%s),?\s+(%s)(?:,\s*pp?\.\s*[\d\u2013-]+)?$" % (AUTH, YEAR))
PREFIX = re.compile(r"^(?:e\.g\.,?|see|cf\.|also)\s+", re.I)
HEAD = re.compile(r"^\W*(?:\d+(?:\.\d+)*\.?\s*)?(references|reference list|bibliography|works cited)\W*$", re.I)
STOP = re.compile(r"^\W*(?:\d+(?:\.\d+)*\.?\s*)?(appendix|appendices|acknowledg)", re.I)
START = re.compile(r"(?:^|(?<=[.)\]]\s))(%s,\s(?:[A-Z]\.(?:\s|-)?){1,4})" % NAME)
NOTE = "This only compares the citations and the reference list inside your document. It does not check that a source exists or supports the claim."

def _occ(t, o, idx): return sum(1 for i in range(idx) if t.startswith(o, i)) + 1

def _kind(a):
    return "etal" if "et al" in a else "two" if re.search(r"\s(?:and|&)\s", a) else "one"

def find_citations(paras, upto):
    out = []
    for pi in range(upto):
        t = paras[pi]["t"]
        if paras[pi].get("tag") == "h2": continue
        def add(a, y, o, idx): out.append({"p": pi, "o": o, "occ": _occ(t, o, idx), "first": re.match(NAME, a)[0].lower(), "year": y, "kind": _kind(a)})
        for m in NARR.finditer(t): add(m[1], m[2], m[0], m.start())
        for m in re.finditer(r"\(([^()]{3,300})\)", t):
            inner, base = m[1], m.start(1)
            for part in re.finditer(r"[^;]+", inner):
                raw = part[0]; s = raw.strip(); lead = len(raw) - len(raw.lstrip())
                s2 = PREFIX.sub("", s); lead += len(s) - len(s2)
                pm = PART.match(s2)
                if pm: add(pm[1], pm[2], s2, base + part.start() + lead)
    return out

def find_references(paras, h):
    refs, unparsed = [], 0
    for pi in range(h + 1, len(paras)):
        p = paras[pi]
        if p.get("tag") == "h2" and STOP.match(p["t"]): break
        t = p["t"]; starts = [m.start(1) for m in START.finditer(t)]
        if not starts: unparsed += 1; continue
        for k, s in enumerate(starts):
            seg = t[s:starts[k + 1] if k + 1 < len(starts) else len(t)]
            ym = re.search(r"\((%s|n\.d\.)\)" % YEAR, seg)
            if not ym: unparsed += 1; continue
            names = re.findall(r"(%s),\s(?:[A-Z]\.(?:\s|-)?)+" % NAME, seg[:ym.start()])
            o = START.match(seg)[1].strip()
            refs.append({"p": pi, "o": o, "occ": _occ(t, o, s), "first": names[0].lower(), "year": ym[1], "n": len(names), "cited": False})
    return refs, unparsed

def check_citations(paras):
    """paras: [{'t','tag'}]. Returns {'issues': [...], 'summary': {...}, 'notes': [...]}. Issues are review-only (s == o)."""
    notes, issues = [], []
    h = next((i for i, p in enumerate(paras) if p.get("tag") == "h2" and HEAD.match(p["t"])), None)
    summ = {"citations": 0, "references": 0, "missing": 0, "year_mismatch": 0, "ambiguous": 0, "author_count": 0, "uncited": 0}
    body = h if h is not None else len(paras)
    cites = find_citations(paras, body)
    numeric = sum(len(re.findall(r"\[\d+(?:[,\u2013-]\s*\d+)*\]", p["t"])) for p in paras[:body])
    if numeric >= 3 and len(cites) < 3:
        return {"issues": [], "summary": summ, "notes": ["Numeric citations such as [1] were found. Only author-year (APA) citations are supported."]}
    summ["citations"] = len(cites)
    if h is None: return {"issues": [], "summary": summ, "notes": ["No reference list heading (References, Bibliography) was found, so citations cannot be matched."]}
    refs, unparsed = find_references(paras, h); summ["references"] = len(refs)
    if unparsed: notes.append("%d reference paragraph(s) did not look like APA entries and were skipped." % unparsed)
    if not refs: return {"issues": [], "summary": summ, "notes": notes + ["The reference list was found but no APA-style entries could be read."]}
    def issue(it, msg): issues.append({"p": it["p"], "o": it["o"], "occ": it["occ"], "cat": "cit", "s": it["o"], "w": [msg, NOTE], "kind": "check"})
    for c in cites:
        cands = [r for r in refs if r["first"] == c["first"]]
        exact = [r for r in cands if r["year"] == c["year"]]
        based = [r for r in cands if r["year"][:4] == c["year"][:4] and r["year"] != c["year"]] if not exact else []
        if exact:
            r = exact[0]; r["cited"] = True
            if c["kind"] == "etal" and r["n"] <= 2: summ["author_count"] += 1; issue(c, "'et al.' is used, but the reference lists only %d author(s). APA 7 names both authors of a two-author work." % r["n"])
            elif c["kind"] == "two" and r["n"] >= 3: summ["author_count"] += 1; issue(c, "Two authors are named, but the reference lists %d. APA 7 uses 'et al.' for three or more authors." % r["n"])
            elif c["kind"] == "one" and r["n"] >= 2: summ["author_count"] += 1; issue(c, "One author is named, but the reference lists %d authors." % r["n"])
        elif based and len(based) >= 2 and not c["year"][-1].isalpha():
            for r in based: r["cited"] = True
            summ["ambiguous"] += 1; issue(c, "Ambiguous: the reference list has %d works by %s in %s (%s). Add a letter such as %sa or %sb." % (len(based), c["first"].title(), c["year"], ", ".join(r["year"] for r in based), c["year"], c["year"]))
        elif based:
            based[0]["cited"] = True
        elif cands:
            for r in cands: r["cited"] = True   # the reference is probably this one with a wrong year; do not also report it as uncited
            summ["year_mismatch"] += 1; issue(c, "The reference list has %s (%s) but the text cites %s." % (c["first"].title(), ", ".join(sorted({r["year"] for r in cands})), c["year"]))
        else:
            summ["missing"] += 1; issue(c, "No reference entry found for %s (%s). Checked first author and year only." % (c["first"].title(), c["year"]))
    for r in refs:
        if not r["cited"]:
            summ["uncited"] += 1; issue(r, "This reference is not cited in the text (no citation with first author %s and year %s). It may be cited under a different spelling." % (r["first"].title(), r["year"]))
    return {"issues": issues, "summary": summ, "notes": notes}
