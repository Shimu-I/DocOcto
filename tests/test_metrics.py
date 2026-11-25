import os
from dococto.metrics import load_dataset, score, iou
DATA = [{"id": "a", "text": "The results was good.", "gold": [{"o": "was", "cat": "gram", "fixes": ["were"], "a": 12, "b": 15}]},
        {"id": "b", "text": "Nothing wrong here.", "gold": []}]
def P(p, o, s="x", cat="gram", occ=1): return {"p": p, "o": o, "s": s, "cat": cat, "occ": occ}

def test_iou_basic(): assert iou(0, 10, 5, 15) == 5 / 15 and iou(0, 5, 5, 10) == 0
def test_perfect_prediction():
    r = score(DATA, [P(0, "was", "were")]); assert r["strict"]["precision"] == 1 == r["strict"]["recall"] and r["category_accuracy"] == 1 and r["fix_accuracy"] == 1
def test_false_positive_and_clean_paragraph_alarm():
    r = score(DATA, [P(0, "was", "were"), P(1, "wrong")]); assert r["strict"]["fp"] == 1 and r["clean_paragraph_false_alarm_rate"] == 1 and r["strict"]["precision"] == 0.5
def test_miss_counts_as_false_negative():
    r = score(DATA, []); assert r["strict"]["fn"] == 1 and r["strict"]["recall"] == 0 and r["strict"]["precision"] == 0
def test_strict_vs_lenient_overlap():
    r = score(DATA, [P(0, "results was good")]); assert r["strict"]["tp"] == 0 and r["lenient"]["tp"] == 1
def test_each_prediction_used_once():
    r = score(DATA, [P(0, "was", "were"), P(0, "was", "were")]); assert r["strict"]["tp"] == 1 and r["strict"]["fp"] == 1
def test_wrong_category_and_wrong_fix_reduce_those_metrics_only():
    r = score(DATA, [P(0, "was", "is", cat="style")]); assert r["strict"]["tp"] == 1 and r["category_accuracy"] == 0 and r["fix_accuracy"] == 0
def test_dataset_integrity():
    d = load_dataset(os.path.join(os.path.dirname(__file__), "..", "eval", "dataset.json"))
    assert len({x["id"] for x in d}) == len(d) and sum(1 for x in d if not x["gold"]) >= 5
    from dococto.validate import CATS
    assert all(g["cat"] in CATS and g["fixes"] for x in d for g in x["gold"])
