"""End-to-end tests in a real headless Chromium (Playwright). Skipped automatically if Playwright or its browser is missing.
Not covered: the PDF page view and the real Mammoth/PDF.js libraries (they need internet or vendored files)."""
import atexit, contextlib, io, os, re, socket, subprocess, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as _p: _p.chromium.launch().close()   # skip cleanly if the browser is not installed
    HAVE = True
except Exception: HAVE = False
from docx import Document
_srv = None

def base_url():
    global _srv
    if _srv is None:
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
        env = dict(os.environ, PORT=str(port), AI_PROVIDER="gemini", AI_API_KEY="")
        _srv = (subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL), port)
        atexit.register(lambda: _srv[0].terminate())
        for _ in range(60):
            try: urllib.request.urlopen("http://127.0.0.1:%d/" % port).read(); break
            except Exception: time.sleep(0.2)
    return "http://127.0.0.1:%d" % _srv[1]

@contextlib.contextmanager
def app_page(init=None, route="#review", viewport=None):
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(accept_downloads=True, viewport=viewport) if viewport else b.new_context(accept_downloads=True)
        ctx.route(re.compile(r"^https?://(?!127\.0\.0\.1)"), lambda r: r.abort())   # offline: no CDN or fonts
        pg = ctx.new_page(); pg.errors = []; pg.on("pageerror", lambda e: pg.errors.append(str(e)))
        if init: pg.add_init_script(init)
        pg.goto(base_url() + "/" + route); pg.wait_for_selector("#doc" if route == "#review" else "#view-" + (route[1:] or "home")); yield pg; b.close()

def docx_bytes(paras):
    d = Document()
    for t in paras: d.add_paragraph(t)
    b = io.BytesIO(); d.save(b); return b.getvalue()
def upload(pg, name, data, mime="application/octet-stream"):
    pg.set_input_files("#fi", {"name": name, "mimeType": mime, "buffer": data})
    pg.wait_for_function("document.querySelector('#st').textContent.startsWith('Checked')", timeout=30000)
def text(pg, sel): return pg.inner_text(sel)
SAMPLE = ["We don't recieve a lot of people and the the model is very small.", "The results was good in this study today."]

def test_demo_loads_octopus_draws_and_no_script_errors():
    if not HAVE: return
    with app_page() as pg:
        pg.wait_for_timeout(1500)
        assert pg.locator("#doc .is").count() == 8 and pg.locator("#il .ir").count() == 8
        assert pg.evaluate("(()=>{const c=document.querySelector('#oct');const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;for(let i=3;i<d.length;i+=4)if(d[i]>0)return true;return false})()")
        assert pg.errors == []
def test_upload_runs_quick_check_and_lists_issues():
    if not HAVE: return
    with app_page() as pg:
        upload(pg, "t.docx", docx_bytes(SAMPLE)); assert pg.locator("#il .ir").count() >= 4 and "Checks run" in text(pg, "#ck"); assert pg.errors == []
def test_accept_changes_text_then_undo_restores_and_history_records_both():
    if not HAVE: return
    with app_page() as pg:
        upload(pg, "t.docx", docx_bytes(SAMPLE)); first = text(pg, "#doc .is").strip(); new = text(pg, "#ss ins").strip()
        assert new and new != first
        pg.click("#ac")
        assert pg.locator("#doc .is.done").count() == 1 and text(pg, "#doc .is.done").strip() == new and text(pg, "#hc") == "1" and "accepted" in text(pg, "#hist")
        pg.click("#un"); assert pg.locator("#doc .is.done").count() == 0 and text(pg, "#hc") == "2" and text(pg, "#doc .is").strip() == first and "undone" in text(pg, "#hist")
def test_accepted_replacement_really_appears_in_the_document():
    if not HAVE: return
    with app_page() as pg:
        upload(pg, "t.docx", docx_bytes(["We don't use any pretrained weights in this study today."]))
        pg.click("#ac"); assert "We do not use" in text(pg, "#doc")
def test_reject_keeps_original_wording():
    if not HAVE: return
    with app_page() as pg:
        upload(pg, "t.docx", docx_bytes(["We don't use any pretrained weights in this study today."]))
        pg.click("#rj"); assert "We don't use" in text(pg, "#doc") and pg.locator("#doc .is.rej").count() == 1 and "rejected" in text(pg, "#hist")
def test_review_only_items_are_hidden_until_the_filter_is_switched_on():
    if not HAVE: return
    long = "The results are " + " ".join("term" + chr(97 + i % 26) + chr(97 + i // 26) for i in range(60)) + "."
    with app_page() as pg:
        upload(pg, "t.docx", docx_bytes([long])); assert pg.locator("#il .ir").count() == 0 and "Review only 1" in text(pg, "#kf")
        pg.click(".kc[data-k=review]"); assert pg.locator("#il .ir").count() == 1 and "Mark reviewed" in text(pg, "#ac")
        pg.click("#ac"); assert "No text was changed" in text(pg, "#toast") and "termaa" in text(pg, "#doc") and "reviewed" in text(pg, "#hist")
def test_document_never_scrolls_by_itself_while_the_octopus_tours():
    if not HAVE: return
    paras = ["Paragraph %d: we don't recieve a lot of data here, and the results show something quite long today." % i for i in range(60)]
    with app_page() as pg:
        upload(pg, "t.docx", docx_bytes(paras)); pg.wait_for_timeout(8000)
        assert pg.evaluate("document.querySelector('#doc').scrollTop") == 0 and pg.errors == []
def test_selecting_an_issue_does_not_scroll_unless_jump_is_on():
    if not HAVE: return
    paras = ["Paragraph %d: we don't recieve a lot of data here, and the results show something quite long today." % i for i in range(60)]
    with app_page() as pg:
        upload(pg, "t.docx", docx_bytes(paras)); pg.locator("#il .ir").nth(150).click() if pg.locator("#il .ir").count() > 150 else pg.locator("#il .ir").last.click()
        pg.wait_for_timeout(600); assert pg.evaluate("document.querySelector('#doc').scrollTop") == 0
        pg.click("#sj"); pg.locator("#il .ir").last.click(); pg.wait_for_timeout(1500); assert pg.evaluate("document.querySelector('#doc').scrollTop") > 0
def test_keyboard_shortcuts_navigate_accept_and_undo():
    if not HAVE: return
    with app_page() as pg:
        upload(pg, "t.docx", docx_bytes(SAMPLE)); pass
        pg.keyboard.press("j"); assert text(pg, "#sn").startswith("2 of")
        pg.keyboard.press("a"); assert text(pg, "#hc") == "1"
        pg.keyboard.press("u"); assert text(pg, "#hc") == "2"
def test_summary_dialog_counts_and_is_closable():
    if not HAVE: return
    with app_page() as pg:
        upload(pg, "t.docx", docx_bytes(SAMPLE)); pg.click("#ac"); pg.click("#sumbtn")
        assert pg.evaluate("document.querySelector('#dlg').open") and "Accepted fixes: 1" in text(pg, "#db").replace("\n", " ")
        pg.keyboard.press("Escape"); assert not pg.evaluate("document.querySelector('#dlg').open")
def test_untrusted_text_cannot_inject_html_or_run_script():
    if not HAVE: return
    evil = b"We recieve <img src=x onerror=\"window.__xss=1\"> data and <script>window.__xss=2</script> a lot of it today."
    with app_page() as pg:
        upload(pg, "evil.txt", evil, "text/plain"); pg.click("#nx"); pg.click("#nx"); pg.wait_for_timeout(500)
        assert pg.evaluate("window.__xss") is None and pg.locator("#doc img, #doc script, #db img, #so2 img, #ss img").count() == 0
def test_docx_export_downloads_a_valid_word_file_with_the_accepted_change():
    if not HAVE: return
    with app_page() as pg:
        upload(pg, "t.docx", docx_bytes(["We don't use any pretrained weights in this study today."])); pg.click("#ac")
        with pg.expect_download() as d: pg.click("#ed")
        path = d.value.path(); text_out = "\n".join(p.text for p in Document(path).paragraphs); assert "We do not use" in text_out
def test_formatted_docx_suggestion_spanning_bold_italic_boundary_accepts_and_undoes_cleanly():
    if not HAVE: return
    stub = "window.mammoth={convertToHtml:async()=>({value:'<h1>Title</h1><p>We recruited <em>a lot</em> of people and the model works today.</p>'})}"
    with app_page(stub) as pg:
        pg.set_input_files("#fi", {"name": "f.docx", "mimeType": "application/octet-stream", "buffer": docx_bytes(["x"])})
        pg.wait_for_function("document.querySelector('#st').textContent.startsWith('Checked')", timeout=30000)
        assert pg.locator("#doc [data-id]").count() >= 2 and pg.locator("#doc em").count() >= 1
        pg.click("#ac"); assert "recruited many people" in text(pg, "#doc").replace("\n", " ")
        pg.click("#un"); t = text(pg, "#doc").replace("\n", " "); assert "recruited a lot of people" in t and pg.locator("#doc em").first.inner_text() == "a lot"
        assert pg.errors == []

PDF_STUB = """window.pdfjsLib={GlobalWorkerOptions:{},getDocument:()=>({promise:Promise.resolve({numPages:30,getPage:async n=>({
 getViewport:({scale})=>({width:600*scale,height:800*scale,scale}),render:()=>({promise:Promise.resolve()}),
 getTextContent:async()=>({items:Array.from({length:12},(_,i)=>({str:'Line '+i+' of page '+n+' we recieve a lot of data in this study today.',transform:[1,0,0,1,0,700-i*20]}))})})})}),
 renderTextLayer:({container,textContent})=>{textContent.items.forEach((it,i)=>{const s=document.createElement('span');s.textContent=it.str;s.style.cssText='left:10px;top:'+(10+i*20)+'px';container.appendChild(s)});return{promise:Promise.resolve()}}};"""
TOP_PAGE = "(()=>{const d=document.querySelector('#doc'),t=d.getBoundingClientRect().top;for(const p of d.querySelectorAll('.pdfpg')){const r=p.getBoundingClientRect();if(r.bottom>t+4)return[+p.dataset.pg,(t-r.top)/r.height]}})()"

def test_pdf_zoom_keeps_your_reading_position():
    if not HAVE: return
    with app_page(PDF_STUB) as pg:
        pg.set_input_files("#fi", {"name": "p.pdf", "mimeType": "application/pdf", "buffer": b"%PDF-stub"})
        pg.wait_for_function("document.querySelector('#st').textContent.startsWith('Checked')", timeout=30000)
        assert pg.locator(".pdfpg").count() == 30
        pg.evaluate("(()=>{const d=document.querySelector('#doc');d.style.scrollBehavior='auto';const p=d.querySelector('.pdfpg[data-pg=\"12\"]');d.scrollTop=p.offsetTop+p.offsetHeight*0.4})()")
        pg.wait_for_timeout(300); before = pg.evaluate(TOP_PAGE); assert before[0] == 12
        pg.click("#zi"); pg.wait_for_timeout(700); after = pg.evaluate(TOP_PAGE)
        assert after[0] == 12 and abs(after[1] - before[1]) < 0.08 and text(pg, "#zl") == "110%"
        pg.click("#zo"); pg.click("#zo"); pg.wait_for_timeout(700); back = pg.evaluate(TOP_PAGE); assert back[0] == 12 and abs(back[1] - before[1]) < 0.08
        assert pg.errors == []
def test_pdf_edit_mode_edits_revised_text_and_export_uses_it():
    if not HAVE: return
    with app_page(PDF_STUB) as pg:
        pg.set_input_files("#fi", {"name": "p.pdf", "mimeType": "application/pdf", "buffer": b"%PDF-stub"})
        pg.wait_for_function("document.querySelector('#st').textContent.startsWith('Checked')", timeout=30000)
        pg.click("#me"); assert pg.locator("[data-rev]").count() > 3 and pg.evaluate("document.querySelector('#doc').isContentEditable") and pg.locator(".pdfpg").count() == 0
        pg.evaluate("document.querySelector('[data-rev=\"0\"]').textContent='MY EDITED PARAGRAPH'")
        pg.click("#mv"); assert pg.locator(".pdfpg").count() == 30 and "kept in the revised text" in text(pg, "#toast")
        with pg.expect_download() as d: pg.click("#ed")
        assert "MY EDITED PARAGRAPH" in "\n".join(p.text for p in Document(d.value.path()).paragraphs); assert pg.errors == []
def test_home_page_has_no_sidebar_and_explains_the_app():
    if not HAVE: return
    with app_page(route="") as pg:
        h = text(pg, "#view-home")
        assert pg.is_visible("#view-home") and not pg.is_visible("#view-review") and pg.locator("aside").count() == 0
        for w in ("Get started", "About the project", "Features", "How it works", "Start reviewing", "never touched", "very good"): assert w in h, w
        assert pg.locator("#features .fi").count() == 8
def test_navigation_between_home_review_manual_and_about():
    if not HAVE: return
    with app_page(route="") as pg:
        pg.click("#nv2"); assert pg.is_visible("#view-manual") and "#manual" in pg.url and "Keyboard shortcuts" in text(pg, "#view-manual")
        pg.click("[data-scroll=m10]"); pg.wait_for_timeout(800); assert pg.evaluate("window.scrollY") > 300
        pg.click("#nv3"); assert pg.is_visible("#view-about") and "Privacy" in text(pg, "#view-about")
        pg.click("#nv1"); assert pg.is_visible("#view-review") and pg.is_visible("#doc")
        pg.click("#nv0"); assert pg.is_visible("#view-home") and pg.get_attribute("#nv0", "aria-current") == "page"
def test_try_demo_and_upload_from_home_open_the_review_screen():
    if not HAVE: return
    with app_page(route="") as pg:
        pg.click("#h-demo"); assert pg.is_visible("#view-review") and pg.locator("#il .ir").count() == 8
    with app_page(route="") as pg:
        pg.set_input_files("#fi", {"name": "t.docx", "mimeType": "application/octet-stream", "buffer": docx_bytes(SAMPLE)})
        pg.wait_for_function("document.querySelector('#st').textContent.startsWith('Checked')", timeout=30000); assert pg.is_visible("#view-review")
MIN_FONT = "(()=>{let m=99;document.querySelectorAll('#view-review *, header *').forEach(e=>{if(e.closest('.textLayer,.sr,canvas,.thumbs')||!e.offsetParent)return;if(![...e.childNodes].some(n=>n.nodeType==3&&n.textContent.trim()))return;m=Math.min(m,parseFloat(getComputedStyle(e).fontSize))});return m})()"
def test_text_is_large_enough_to_read_comfortably():
    if not HAVE: return
    with app_page() as pg:
        upload(pg, "t.docx", docx_bytes(SAMPLE))
        assert pg.evaluate("getComputedStyle(document.documentElement).fontSize") == "17px" and pg.evaluate("parseFloat(getComputedStyle(document.querySelector('#doc p')).fontSize)") >= 18
        assert pg.evaluate(MIN_FONT) >= 13.5
def test_text_size_button_enlarges_everything_and_is_remembered():
    if not HAVE: return
    with app_page() as pg:
        pg.click("#fs"); assert text(pg, "#fs") == "Aa: Large" and pg.evaluate("getComputedStyle(document.documentElement).fontSize") == "19.55px"
        pg.reload(); pg.wait_for_selector("#doc"); assert pg.evaluate("getComputedStyle(document.documentElement).fontSize") == "19.55px"
        pg.click("#setbtn"); pg.click("[data-fs='2']"); assert pg.evaluate("getComputedStyle(document.documentElement).fontSize") == "22.1px"
def test_page_colour_and_octopus_strength_controls_work():
    if not HAVE: return
    with app_page() as pg:
        assert "pt-soft" in pg.get_attribute("#doc", "class") and pg.evaluate("getComputedStyle(document.querySelector('#oct')).opacity") == "1"
        pg.click("#pt"); assert "pt-dark" in pg.get_attribute("#doc", "class") and text(pg, "#pt") == "Page: dark"
        pg.click("#oa"); pg.wait_for_timeout(500); assert pg.evaluate("getComputedStyle(document.querySelector('#oct')).opacity") == "0.5" and text(pg, "#oa") == "Octopus: soft"

def overflow(pg): return pg.evaluate("document.documentElement.scrollWidth - window.innerWidth")
def test_top_navigation_has_the_required_items_and_a_prominent_app_button():
    if not HAVE: return
    with app_page(route="") as pg:
        nav = text(pg, "#mainnav")
        for w in ("Home", "Features", "How it works", "User guide", "About"): assert w in nav, w
        assert text(pg, "#nv1").startswith("Open app") and pg.locator("aside").count() == 0
        pg.click("#nv3"); pg.click("#nvf"); pg.wait_for_timeout(900)
        assert pg.is_visible("#view-home") and 0 <= pg.evaluate("document.querySelector('#features').getBoundingClientRect().top") < 300
        pg.click("#nvh"); pg.wait_for_timeout(900); assert 0 <= pg.evaluate("document.querySelector('#how').getBoundingClientRect().top") < 300
def test_typography_follows_the_design_brief():
    if not HAVE: return
    with app_page(route="", viewport={"width": 1440, "height": 900}) as pg:
        px = lambda sel: pg.evaluate("parseFloat(getComputedStyle(document.querySelector('%s')).fontSize)" % sel)
        assert 36 <= px(".hero h1") <= 48 and 26 <= px("#features h2") <= 32 and 15 <= px("body") <= 17 and px(".lead") >= 17
def test_drop_zone_rejects_bad_files_and_accepts_a_real_paper():
    if not HAVE: return
    import base64
    drop = "([name,b64,type])=>{const bytes=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));const dt=new DataTransfer();dt.items.add(new File([bytes],name,{type}));document.querySelector('#dz').dispatchEvent(new DragEvent('drop',{dataTransfer:dt,bubbles:true,cancelable:true}))}"
    with app_page(route="") as pg:
        pg.evaluate(drop, ["virus.exe", base64.b64encode(b"MZ").decode(), "application/octet-stream"])
        assert "not supported" in text(pg, "#dzerr") and pg.is_visible("#view-home")
        pg.evaluate(drop, ["empty.txt", "", "text/plain"]); assert "empty" in text(pg, "#dzerr")
        pg.evaluate(drop, ["paper.docx", base64.b64encode(docx_bytes(SAMPLE)).decode(), "application/octet-stream"])
        pg.wait_for_function("document.querySelector('#st').textContent.startsWith('Checked')", timeout=30000)
        assert pg.is_visible("#view-review") and pg.locator("#il .ir").count() >= 4
def test_mobile_layout_has_no_sideways_scroll_and_a_working_menu():
    if not HAVE: return
    with app_page(route="", viewport={"width": 390, "height": 844}) as pg:
        assert pg.is_visible("#menu") and not pg.is_visible("#nv2") and overflow(pg) <= 1
        pg.click("#menu"); assert pg.is_visible("#nv2") and pg.get_attribute("#menu", "aria-expanded") == "true"
        pg.click("#nv2"); assert pg.is_visible("#view-manual") and not pg.is_visible("#mainnav") and overflow(pg) <= 1
        pg.click("#menu"); pg.click("#nv3"); assert overflow(pg) <= 1
        pg.click("#nv1"); assert pg.is_visible("#view-review") and pg.is_visible("#doc") and overflow(pg) <= 1
    with app_page(route="", viewport={"width": 820, "height": 1100}) as pg: assert overflow(pg) <= 1
def test_footer_shows_real_links_only_and_hides_unset_ones():
    if not HAVE: return
    with app_page(route="") as pg:
        f = text(pg, "#foot")
        assert "User guide" in f and "About and technical details" in f and not pg.is_visible("#f-repo") and not pg.is_visible("#f-people") and "your-username" not in f
def test_loading_state_is_visible_while_working():
    if not HAVE: return
    with app_page() as pg:
        pg.evaluate("hSt('Checking\u2026')"); assert pg.evaluate("document.body.classList.contains('working')") and "Checking" in text(pg, "#st")
        pg.evaluate("hSt('Checked \u2713')"); assert not pg.evaluate("document.body.classList.contains('working')")
def test_about_page_numbers_match_the_evaluation_results():
    if not HAVE: return
    import json
    r = json.load(open(os.path.join(ROOT, "eval", "results", "latest.json")))["systems"]["rules"]; s = r["strict"]
    with app_page(route="#about") as pg:
        a = text(pg, "#view-about"); assert "%d%%" % round(100 * s["precision"]) in a and "%d%%" % round(100 * s["recall"]) in a and "%d%%" % round(100 * s["f1"]) in a
        assert "labels were written by an AI assistant" in a and "Methodology" in a and "Known limitations" in a
