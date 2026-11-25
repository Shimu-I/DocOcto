"""Build a .docx from the reviewed paragraphs. Only what the parser keeps can be written."""
import io, re
from docx import Document

FORMAT_NOTES = "Preserved: headings, paragraphs, bullet lists. Not preserved: bold/italic, tables, images, equations, page layout."
_BAD = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

def build_docx(paras):
    d = Document()
    for p in paras:
        t = _BAD.sub("", str(p.get("t", ""))).strip()
        if not t: continue
        if p.get("h") == "H1": d.add_heading(t, 0)
        elif p.get("k") == "h2" or p.get("h") == "H2": d.add_heading(t, 1)
        elif p.get("k") == "li": d.add_paragraph(t, style="List Bullet")
        else: d.add_paragraph(t)
    b = io.BytesIO(); d.save(b); return b.getvalue()
