import io, re
import pytest
from docx import Document
from pypdf import PdfWriter
import app as appmod

def docx_bytes(build):
    d = Document(); build(d); b = io.BytesIO(); d.save(b); return b.getvalue()
def post_file(client, name, data): return client.post("/api/parse?name=" + name, data=data)

def test_parse_docx_keeps_headings_lists_and_order(client):
    data = docx_bytes(lambda d: (d.add_heading("Intro", 1), d.add_paragraph("First point.", style="List Bullet"), d.add_paragraph("Body text.")))
    j = post_file(client, "a.docx", data).get_json()["paras"]
    assert [(p["t"], p["tag"]) for p in j] == [("Intro", "h2"), ("First point.", "li"), ("Body text.", "p")]
def test_parse_txt_is_not_handled_by_server_endpoint(client): assert post_file(client, "a.txt", b"hi").status_code == 400
@pytest.mark.parametrize("name,data,code", [("a.docx", b"", 422), ("a.docx", b"not a zip", 422), ("a.pdf", b"%PDF-1.4 junk", 422), ("a.exe", b"x", 400)])
def test_malformed_or_unsupported_files(client, name, data, code): assert post_file(client, name, data).status_code == code
def test_blank_docx_reports_no_text(client):
    assert "No text" in post_file(client, "a.docx", docx_bytes(lambda d: d.add_paragraph("  "))).get_json()["error"]
def test_scanned_pdf_reports_ocr_needed(client):
    w = PdfWriter(); w.add_blank_page(200, 200); b = io.BytesIO(); w.write(b)
    r = post_file(client, "scan.pdf", b.getvalue()); assert r.status_code == 422 and "OCR" in r.get_json()["error"]
def test_oversized_upload_is_413(client):
    assert post_file(client, "a.docx", b"0" * (appmod.MAX_BYTES + 1)).status_code == 413
def test_paragraph_cap(client, monkeypatch):
    monkeypatch.setattr(appmod, "MAX_PARAS", 3)
    data = docx_bytes(lambda d: [d.add_paragraph("p%d" % i) for i in range(6)])
    assert post_file(client, "a.docx", data).status_code == 413

def test_analyze_missing_key_and_unknown_provider(client, monkeypatch):
    assert client.post("/api/analyze", json={"prompt": "x"}).status_code == 503
    monkeypatch.setattr(appmod, "P", "nope"); r = client.post("/api/analyze", json={"prompt": "x"}); assert r.status_code == 503 and "Unknown" in r.get_json()["error"]
def test_analyze_requires_prompt(client): assert client.post("/api/analyze", json={}).status_code == 400
def test_analyze_provider_failure_and_timeout(client, monkeypatch):
    def boom(prompt): raise appmod.Fail(502, "Could not reach the AI provider: timed out")
    monkeypatch.setattr(appmod, "ask", boom)
    r = client.post("/api/analyze", json={"prompt": "x"}); assert r.status_code == 502 and "timed out" in r.get_json()["error"]
def test_analyze_invalid_ai_answer_is_reported_not_crashed(client, monkeypatch):
    monkeypatch.setattr(appmod, "ask", lambda p: "Sorry, I cannot do that.")
    j = client.post("/api/analyze", json={"prompt": "x"}).get_json(); assert j["items"] is None and "JSON" in j["parse_error"]
def test_analyze_valid_ai_answer(client, monkeypatch):
    monkeypatch.setattr(appmod, "ask", lambda p: '```json\n[{"p":0,"o":"a","s":"b","cat":"gram"}]\n```')
    assert client.post("/api/analyze", json={"prompt": "x"}).get_json()["items"][0]["o"] == "a"
def test_config_reports_cloud_vs_local(client, monkeypatch):
    assert client.get("/api/config").get_json()["cloud"] is True
    monkeypatch.setattr(appmod, "P", "ollama"); assert client.get("/api/config").get_json()["cloud"] is False

def test_validate_endpoint_splits_good_and_bad(client):
    j = client.post("/api/validate", json={"paras": ["It is very good."], "items": [
        {"p": 0, "o": "very good", "s": "strong", "cat": "clar"}, {"p": 0, "o": "nope", "s": "x", "cat": "clar"}]}).get_json()
    assert len(j["issues"]) == 1 and len(j["rejected"]) == 1
def test_validate_endpoint_bad_request(client): assert client.post("/api/validate", json={"paras": 1}).status_code == 400

def export(client, paras): return client.post("/api/export-docx", json={"paras": paras})
def test_export_docx_round_trip_with_accepted_text_and_styles(client):
    r = export(client, [{"t": "My Title", "h": "H1", "k": "h2"}, {"t": "Heading", "h": "H2", "k": "h2"}, {"t": "Revised sentence.", "k": "p"}, {"t": "Item", "k": "li"}])
    assert r.status_code == 200 and "Preserved" in r.headers["X-Format-Notes"]
    d = Document(io.BytesIO(r.data)); got = [(p.style.name, p.text) for p in d.paragraphs]
    assert got == [("Title", "My Title"), ("Heading 1", "Heading"), ("Normal", "Revised sentence."), ("List Bullet", "Item")]
def test_export_strips_xml_control_characters(client):
    r = export(client, [{"t": "bad\x00char", "k": "p"}]); assert Document(io.BytesIO(r.data)).paragraphs[0].text == "badchar"
@pytest.mark.parametrize("payload", [[], None, "x"])
def test_export_rejects_empty_payload(client, payload): assert export(client, payload).status_code == 400

def test_regression_suggestion_panel_escapes_untrusted_text():
    """Static check for the XSS found in the audit: panel HTML built from paper/AI text must go through esc()."""
    src = open("public/index.html", encoding="utf-8").read()
    for sel in ("#so2", "#ss", "#sw"):
        line = re.search(r"\$\('%s'\)\.innerHTML=[^\n;]*(?:;[^\n]{0,60})?" % re.escape(sel), src).group(0)
        if sel != "#sw" or "map" in line: assert "esc(" in line, sel
