"""Python port of the browser's Quick check rules, so they can be evaluated and tested.
Keep in sync with quickCheck() in public/index.html (tests/test_rules.py compares both when node is installed)."""
import re

PHR = {"in order to": ("to", 'Wordy: "to" means the same.', "clar"), "due to the fact that": ("because", 'Wordy; "because" is shorter.', "clar"),
       "a number of": ("several", "Imprecise quantity; give a number if you can.", "clar"), "a lot of": ("many", 'Informal quantity. Use "many"/"much" or a measure.', "style"),
       "kind of": ("somewhat", "Informal hedge.", "style"), "sort of": ("somewhat", "Informal hedge.", "style"), "in this day and age": ("currently", "Cliché.", "style"),
       "proves": ("shows", "Strong claim: check that your evidence supports it.", "clar")}
MIS = {"teh": "the", "recieve": "receive", "seperate": "separate", "occured": "occurred", "definately": "definitely", "wich": "which", "adress": "address",
       "begining": "beginning", "enviroment": "environment", "accomodate": "accommodate", "untill": "until", "thier": "their", "becuase": "because",
       "goverment": "government", "alot": "a lot", "occurence": "occurrence", "independant": "independent", "neccessary": "necessary", "sucessful": "successful"}
CON = {"don't": "do not", "doesn't": "does not", "didn't": "did not", "can't": "cannot", "won't": "will not", "isn't": "is not", "aren't": "are not",
       "wasn't": "was not", "weren't": "were not", "it's": "it is", "they're": "they are", "we're": "we are", "couldn't": "could not",
       "shouldn't": "should not", "wouldn't": "would not"}
OPENERS = {"And": "In addition,", "But": "However,", "So": "Therefore,", "Also": "In addition,"}
_PROSE = re.compile(r"[(\[]?[A-Za-z][A-Za-z'\u2019-]*[.,;:)\]?!]*")

def is_prose(t):
    w = t.split()
    return len(w) >= 5 and sum(1 for x in w if _PROSE.fullmatch(x)) / len(w) >= 0.7

def _cap(s, m): return s[0].upper() + s[1:] if m[:1].isupper() and s[:1].islower() else s
def _occ(t, o, idx): return sum(1 for i in range(idx) if t.startswith(o, i)) + 1

def quick_check(paras):
    """paras: list of str or {'t','tag'}. Returns issues {p,o,occ,cat,s,w} (before validation)."""
    out = []
    for pi, pr in enumerate(paras):
        t, tag = (pr, "p") if isinstance(pr, str) else (pr["t"], pr.get("tag", "p"))
        if tag == "h2" or not is_prose(t): continue
        def add(m, idx, cat, s, w): out.append({"p": pi, "o": m, "occ": _occ(t, m, idx), "cat": cat, "s": s, "w": [w]})
        for m in re.finditer(r"\b(" + "|".join(PHR) + r")\b", t, re.I):
            r = PHR[m[0].lower()]; add(m[0], m.start(), r[2], _cap(r[0], m[0]), r[1])
        for m in re.finditer(r"\b(very|really)\s+([a-z]{3,})\b", t, re.I):
            add(m[0], m.start(), "clar", m[2], "Intensifier adds little; use a precise word or a measurable result.")
        for m in re.finditer(r"\b(" + "|".join(MIS) + r")\b", t, re.I):
            add(m[0], m.start(), "gram", _cap(MIS[m[0].lower()], m[0]), "Likely misspelling.")
        for m in re.finditer(r"\b[A-Za-z]+[\u2019'](?:t|s|re)\b", t):
            c = CON.get(m[0].lower().replace("\u2019", "'"))
            if c: add(m[0], m.start(), "style", _cap(c, m[0]), "Contractions are usually avoided in academic writing.")
        for m in re.finditer(r"\b([A-Za-z]+)\s+\1\b", t, re.I):
            if len(m[1]) > 1: add(m[0], m.start(), "gram", m[1], "Repeated word. Check it is not intentional.")
        for m in re.finditer(r"(?:^|[.!?]\s)(And|But|So|Also)\s", t):
            o = m[1]; add(o, m.start() + m[0].index(o), "str", OPENERS[o], "Informal sentence opener. Check the logical link to the previous sentence.")
        for m in re.finditer(r"\(([A-Z][A-Za-z-]+(?:\set al\.?|\sand\s[A-Z][A-Za-z-]+)?)\s(\d{4}[a-z]?)\)", t):
            add(m[0], m.start(), "cit", "(%s, %s)" % (m[1], m[2]), "Author-year citations normally put a comma before the year. Check your required style. Not verified against any source.")
        for m in re.finditer(r"\bet al(?!\.)", t): add(m[0], m.start(), "cit", "et al.", '"et al." needs a period.')
        for m in re.finditer(r"\b(obviously|clearly|undoubtedly|always|never)\b", t, re.I):
            add(m[0], m.start(), "clar", m[0], "Strong or absolute wording. Check the evidence supports it, or soften it.")
        for m in re.finditer(r"[^.!?]+[.!?]", t):
            s = m[0].strip(); w = s.split()
            if 55 < len(w) <= 150:
                o = (re.match(r"(?:\S+\s+){7}\S+", s) or [" ".join(w[:8])])[0]; at = t.find(o, m.start())
                if at >= 0: add(o, at, "clar", o, "Very long sentence (%d words). Consider splitting it." % len(w))
    return out
