import json, os, re, shutil, subprocess
from dococto.rules import quick_check, is_prose
def got(t): return {(x["o"], x["s"], x["cat"], x["occ"]) for x in quick_check([t])}

def test_known_rules_and_case_preserved():
    g = got("A lot of people don't recieve it.")
    assert ("A lot of", "Many", "style", 1) in g and ("don't", "do not", "style", 1) in g and ("recieve", "receive", "gram", 1) in g
def test_citation_and_et_al():
    g = got("See (Smith 2019) and Jones et al 2020 here.")
    assert ("(Smith 2019)", "(Smith, 2019)", "cit", 1) in g and ("et al", "et al.", "cit", 1) in g
def test_occurrence_number_for_repeated_phrase():
    assert ("clearly", "clearly", "clar", 2) in got("It is clearly true and clearly stated here.")
def test_table_rows_and_headings_are_skipped():
    assert quick_check(["Task W1 W2 W3 W4 W5 W6 W7 very good"]) == [] and quick_check([{"t": "very good indeed here now", "tag": "h2"}]) == []
def test_long_sentence_thresholds():
    s = lambda n: "The results are " + " ".join("words" for _ in range(n)) + "."
    assert any("long sentence" in x["w"][0] for x in quick_check([s(60)])) and not any("long sentence" in x["w"][0] for x in quick_check([s(10)] + [s(160)]))
def test_is_prose(): assert is_prose("We trained the model for fifty epochs today.") and not is_prose("Task W1 W2 W3 W4 W5 W6")
def test_matches_browser_rules_when_node_is_available():
    """Parity check: the JavaScript quickCheck in the page must give the same issues as this Python port."""
    if not shutil.which("node"): return
    root = os.path.dirname(os.path.dirname(__file__)); src = open(os.path.join(root, "public", "index.html"), encoding="utf-8").read()
    code = re.search(r"function isProse[^\n]*", src)[0] + re.search(r"const PHR=[\s\S]*?function quickCheck[\s\S]*?return out}", src)[0]
    texts = [d["text"] for d in json.load(open(os.path.join(root, "eval", "dataset.json"), encoding="utf-8"))]
    js = "const q=(()=>{%s;return quickCheck})();console.log(JSON.stringify(%s.map((t,i)=>q([{t,tag:'p'}]).map(x=>[i,x.o,x.s,x.cat,x.occ]))))" % (code, json.dumps(texts))
    j = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
    for i, t in enumerate(texts):
        assert sorted(tuple(x[1:]) for x in j[i]) == sorted((x["o"], x["s"], x["cat"], x["occ"]) for x in quick_check([t])), t
