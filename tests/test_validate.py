import pytest
from dococto.validate import validate_issues, parse_ai_json

P = ["The model is very good and very fast. Results rose by 12% (Smith, 2020)."]
def item(**k): return {"p": 0, "o": "very good", "occ": 1, "cat": "clar", "s": "strong", "w": ["vague"], **k}
def check(items, paras=P): return validate_issues(paras, items)

def test_valid_suggestion_gets_offsets_and_kind():
    ok, bad = check([item()]); assert not bad and ok[0]["a"] == 13 and ok[0]["kind"] == "style"
def test_repeated_phrase_uses_occurrence_number():
    ok, _ = check([item(o="very", occ=2, s="highly", cat="clar")]); assert ok[0]["a"] == P[0].index("very", 14)
def test_grammar_fix_is_marked_objective_and_flag_only_is_review():
    assert check([item(cat="gram")])[0][0]["kind"] == "error"
    assert check([item(s="very good")])[0][0]["kind"] == "review"
def test_unlocatable_phrase_rejected():
    _, bad = check([item(o="missing words")]); assert "not found" in bad[0]["reason"]
def test_occurrence_beyond_count_rejected():
    _, bad = check([item(o="very", occ=3)]); assert bad
def test_overlap_and_conflict_and_duplicate():
    ok, bad = check([item(), item(o="good and", s="x"), item(s="great"), item()])
    assert len(ok) == 1 and {b["reason"] for b in bad} >= {"overlaps another suggestion", "duplicate", "conflicts with another suggestion for the same text"}
def test_number_change_rejected():
    _, bad = check([item(o="12%", s="15%")]); assert "number" in bad[0]["reason"]
def test_invented_citation_rejected():
    _, bad = check([item(o="Results rose", s="Results rose (Lee, 2021)")]); assert "citation" in bad[0]["reason"]
def test_equation_text_not_rewritten():
    _, bad = check([item(o="x = y", s="x equals y")], paras=["We set x = y here."]); assert "equation" in bad[0]["reason"]
def test_strengthened_claim_rejected():
    _, bad = check([item(o="suggests", s="proves")], paras=["The data suggests a link."]); assert "stronger" in bad[0]["reason"]
def test_runaway_rewrite_rejected():
    _, bad = check([item(s="x" * 200)]); assert "longer" in bad[0]["reason"]
@pytest.mark.parametrize("bad_item", [None, "text", {}, item(p=9), item(p=True), item(o=""), item(s=None), item(cat="zzz")])
def test_malformed_items_rejected_without_crashing(bad_item):
    ok, bad = check([bad_item]); assert not ok and len(bad) == 1
def test_parse_ai_json_variants():
    assert parse_ai_json('```json\n[{"p":0}]\n```') == [{"p": 0}]
    assert parse_ai_json('Here you go: [{"p":1}] hope it helps') == [{"p": 1}]
    assert parse_ai_json("[]") == []
@pytest.mark.parametrize("txt", ["", "no list", '[{"p": 0,', "[1, 2"])
def test_parse_ai_json_rejects_garbage(txt):
    with pytest.raises(ValueError): parse_ai_json(txt)

def test_regression_citation_comma_fix_is_not_an_invented_citation():
    ok, bad = check([item(o="(Smith 2019)", s="(Smith, 2019)", cat="cit")], paras=["See (Smith 2019) for details."])
    assert ok and not bad
def test_regression_changed_citation_year_still_rejected():
    _, bad = check([item(o="(Smith 2019)", s="(Smith, 2020)", cat="cit")], paras=["See (Smith 2019) for details."]); assert bad
