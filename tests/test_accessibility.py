import os, re
SRC = open(os.path.join(os.path.dirname(__file__), "..", "public", "index.html"), encoding="utf-8").read()
def lum(h):
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
def ratio(a, b): x, y = sorted([lum(a), lum(b)], reverse=True); return (x + 0.05) / (y + 0.05)
V = dict(re.findall(r"--([\w-]+):(#[0-9a-fA-F]{6})", re.search(r":root\{[^}]*\}", SRC)[0]))

def test_text_colors_meet_wcag_aa_on_panel_and_page_backgrounds():
    for k in ("tx", "mu", "pk", "cy", "c-gram", "c-clar", "c-style", "c-rep", "c-cit", "c-str"):
        assert ratio(V[k], V["pn"]) >= 4.5 and ratio(V[k], "#FFFFFF") >= 4.5 and ratio(V[k], V["bg"]) >= 4.5, k
def test_accepted_and_removed_text_colors_meet_aa(): assert ratio("#1f5e44", "#E3F1EA") >= 4.5 and ratio("#B03A5B", "#FDFAFD") >= 4.5 and ratio("#FFFFFF", V["pk"]) >= 4.5
def test_each_category_has_its_own_underline_style_so_color_is_not_the_only_cue():
    styles = re.findall(r"\.is\[data-cat=(\w+)\]\{[^}]*text-decoration:([^;}]*)", SRC); assert len({re.sub(r'var\([^)]*\)', '', s).strip() for _, s in styles}) == 6
def test_highlights_have_accessible_labels_and_keyboard_focus():
    assert 'aria-label="${CATS[x.cat][1]} issue"' in SRC and "tabindex=\"0\"" in SRC
def test_status_changes_are_announced_and_dialogs_are_native():
    assert 'aria-live="polite"' in SRC and "showModal()" in SRC and "function say(" in SRC
def test_navigation_items_are_keyboard_operable():
    assert all(('id="%s" role="button" tabindex="0"' % i) in SRC for i in ("nv0", "nvf", "nvh", "nv2", "nv3")) and '<button class="btn pri" id="nv1">' in SRC
def test_reduced_motion_is_respected():
    assert "prefers-reduced-motion" in SRC and "paused=matchMedia" in SRC.replace(" ", "")
