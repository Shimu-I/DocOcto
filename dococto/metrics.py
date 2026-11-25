"""Scoring for the evaluation. A prediction is a TRUE POSITIVE when it is in the same paragraph as a gold issue and their
character spans overlap enough (strict: IoU >= 0.5; lenient: any overlap). Each gold issue and each prediction is used at most once."""
import json
from dococto.validate import locate, CATS

def load_dataset(path):
    data = json.load(open(path, encoding="utf-8"))
    for it in data:
        for g in it["gold"]:
            a = locate(it["text"], g["o"], g.get("occ", 1))
            if a < 0: raise ValueError("gold phrase not found in %s: %r" % (it["id"], g["o"]))
            g["a"], g["b"] = a, a + len(g["o"])
    return data

def iou(a0, a1, b0, b1):
    inter = max(0, min(a1, b1) - max(a0, b0)); union = max(a1, b1) - min(a0, b0)
    return inter / union if union else 0.0

def _spans(preds, data):
    for p in preds:
        a = locate(data[p["p"]]["text"], p["o"], p.get("occ", 1))
        if a >= 0: yield p, a, a + len(p["o"])

def _match(data, preds, ok):
    used, pairs = set(), []
    sp = list(_spans(preds, data))
    for pi, it in enumerate(data):
        for g in it["gold"]:
            best, bs = None, 0
            for k, (p, a, b) in enumerate(sp):
                if k in used or p["p"] != pi: continue
                s = iou(g["a"], g["b"], a, b)
                if ok(s) and s > bs: best, bs = k, s
            if best is not None: used.add(best); pairs.append((pi, g, sp[best][0]))
    return pairs, len(sp)

def _prf(tp, n_pred, n_gold):
    fp, fn = n_pred - tp, n_gold - tp
    p = tp / n_pred if n_pred else 0.0; r = tp / n_gold if n_gold else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0}

def score(data, preds):
    n_gold = sum(len(it["gold"]) for it in data); words = sum(len(it["text"].split()) for it in data)
    strict_pairs, n_pred = _match(data, preds, lambda s: s >= 0.5)
    len_pairs, _ = _match(data, preds, lambda s: s > 0)
    out = {"n_gold": n_gold, "n_pred": n_pred, "strict": _prf(len(strict_pairs), n_pred, n_gold), "lenient": _prf(len(len_pairs), n_pred, n_gold)}
    out["fp_per_1000_words"] = 1000 * out["strict"]["fp"] / words if words else 0.0
    clean = [i for i, it in enumerate(data) if not it["gold"]]
    flagged = {p["p"] for p in preds}
    out["clean_paragraph_false_alarm_rate"] = sum(1 for i in clean if i in flagged) / len(clean) if clean else 0.0
    out["category_accuracy"] = sum(1 for _, g, p in strict_pairs if p.get("cat") == g["cat"]) / len(strict_pairs) if strict_pairs else None
    withfix = [(g, p) for _, g, p in strict_pairs if g.get("fixes")]
    out["fix_accuracy"] = sum(1 for g, p in withfix if p.get("s", "").strip().lower() in [f.lower() for f in g["fixes"]]) / len(withfix) if withfix else None
    cats = {}
    for it in data:
        for g in it["gold"]: cats.setdefault(g["cat"], [0, 0])[1] += 1
    for _, g, _p in strict_pairs: cats[g["cat"]][0] += 1
    out["recall_by_category"] = {c: (v[0] / v[1]) for c, v in sorted(cats.items())}
    return out
