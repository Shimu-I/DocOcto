from dococto.citations import check_citations
from dococto.validate import validate_issues

def P(t, tag="p"): return {"t": t, "tag": tag}
REFS = [P("References", "h2"),
        P("Vaswani, A., Shazeer, N., Parmar, N., & Uszkoreit, J. (2017). Attention is all you need. NeurIPS. Devlin, J., & Chang, M. (2019). BERT. NAACL."),
        P("Smith, J., & Lee, K. (2020). Findings. Journal A, 1, 2-3."), P("Jones, P. (2017). Old work. Journal B."),
        P("Kim, S. (2019a). First. Journal C."), P("Kim, S. (2019b). Second. Journal C."), P("Garcia, M. (2015). Never cited. Journal D.")]
BODY = [P("Introduction", "h2"), P("Transformers (Vaswani et al., 2017) changed NLP, and BERT (Devlin et al., 2019) built on them. Smith and Lee (2020) agree, "
        "while (Jones, 2018; Brown, 2021) disagree. Later work (Kim, 2019) is unclear. See also (Smith & Lee, 2020, p. 4).")]
def run(paras): return check_citations(paras)
def by(r, text): return [i for i in r["issues"] if text in i["w"][0]]

def test_missing_reference_and_year_mismatch_and_ambiguous_and_uncited():
    r = run(BODY + REFS); s = r["summary"]
    assert s["missing"] == 1 and s["year_mismatch"] == 1 and s["ambiguous"] == 1 and s["uncited"] == 1
    assert by(r, "No reference entry found for Brown")[0]["o"] == "Brown, 2021"
    assert "Jones (2017)" in by(r, "text cites 2018")[0]["w"][0]
    assert by(r, "Ambiguous")[0]["o"] == "Kim, 2019" and "Garcia" in by(r, "not cited")[0]["w"][0]
def test_author_count_rules_apa7():
    r = run(BODY + REFS); assert any(i["o"] == "Devlin et al., 2019" for i in by(r, "et al.")) and not by(r, "Smith")
def test_matching_citations_are_not_flagged():
    r = run(BODY + REFS); flagged = {i["o"] for i in r["issues"]}
    assert "Vaswani et al., 2017" not in flagged and "Smith & Lee, 2020, p. 4" not in flagged and "Smith and Lee (2020)" not in flagged
def test_two_entries_in_one_paragraph_are_split():
    r = run(BODY + REFS); assert r["summary"]["references"] == 7
def test_all_issues_are_review_only_and_locatable_by_the_validator():
    r = run(BODY + REFS); paras = [p["t"] for p in BODY + REFS]
    ok, bad = validate_issues(paras, r["issues"]); assert not bad and all(i["kind"] == "check" and i["s"] == i["o"] for i in ok) and len(ok) == len(r["issues"])
def test_every_issue_carries_the_not_verified_disclaimer():
    assert all("does not check that a source exists" in i["w"][1] for i in run(BODY + REFS)["issues"])
def test_repeated_citation_uses_occurrence_numbers():
    r = run([P("Intro", "h2"), P("As shown (Brown, 2021) and again (Brown, 2021)."), P("References", "h2"), P("Lee, K. (2020). X. Y.")])
    assert sorted(i["occ"] for i in r["issues"] if i["o"] == "Brown, 2021") == [1, 2]
def test_no_reference_list_gives_note_not_false_alarms():
    r = run(BODY); assert r["issues"] == [] and "No reference list" in r["notes"][0]
def test_numeric_style_is_reported_as_unsupported():
    r = run([P("Intro", "h2"), P("Prior work [1], [2] and [3,4] shows this."), P("References", "h2"), P("[1] A. B. Title.")]); assert r["issues"] == [] and "Numeric" in r["notes"][0]
def test_non_apa_reference_paragraphs_are_skipped_with_a_note():
    r = run(BODY + [P("References", "h2"), P("1. Some unparsable entry text here.")]); assert r["summary"]["references"] == 0 and r["notes"]
def test_endpoint_roundtrip_and_bad_request(client):
    j = client.post("/api/citations", json={"paras": BODY + REFS}).get_json(); assert j["summary"]["missing"] == 1
    assert client.post("/api/citations", json={"paras": "x"}).status_code == 400
