#!/usr/bin/env python3
"""
Build the branded Proyecto Thalassa PDF (ES / EN) from markdown.

Pass 1 renders with a placeholder TOC (so pagination is stable),
then we read back which page each section landed on and re-render
with real page numbers. Finally we stamp the running footer.
"""
import re, sys, subprocess, io
from pathlib import Path

import markdown
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parent          # .../SigriCo/brand
PROJ = ROOT.parent                               # .../SigriCo
SCRATCH = Path("/private/tmp/claude-501/-Users-christophermir-Documents-Claude-Projects-Tequila-Tre-Ese-Webpage/5d149f8f-d937-4986-be53-7a3cb45716c5/scratchpad")
OUT = PROJ / "docs"
OUT.mkdir(exist_ok=True)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

COPY = {
    "es": dict(
        md=SCRATCH / "thalassa-es.md",
        stem="Proyecto-Thalassa-ES",
        org="SIGRICO, S.A.P.I. DE C.V.",
        title="PROYECTO<br>THALASSA",
        sub=("Estudio Técnico, Económico y Financiero para operar una concesión "
             "de acuacultura comercial en jaulas oceánicas sumergibles"),
        place="Costa occidental de Baja California Sur, México",
        species="Seriola lalandi · Seriola rivoliana · Lutjanus peru · Centropomus viridis · Totoaba macdonaldi",
        toc="Contenido",
        meta=[("Promotor del proyecto", "SIGRICO, S.A.P.I. de C.V."),
              ("Representante legal", "C. Alberto Eduardo Zamacona Aboumrad"),
              ("Técnico responsable", "Biol. Gustavo Pineda Mahr"),
              ("Versión", "3.0 — Julio 2026")],
        foot_place="La Paz, Baja California Sur · Julio de 2026",
        presented="Presentado ante la Comisión Nacional de Acuacultura y Pesca (CONAPESCA)",
        runfoot="PROYECTO THALASSA — SIGRICO, S.A.P.I. DE C.V.",
    ),
    "en": dict(
        md=SCRATCH / "thalassa-en.md",
        stem="Proyecto-Thalassa-EN",
        org="SIGRICO, S.A.P.I. DE C.V.",
        title="PROYECTO<br>THALASSA",
        sub=("Technical, Economic and Financial Study for the operation of a commercial "
             "aquaculture concession in submersible ocean cages"),
        place="Western coast of Baja California Sur, Mexico",
        species="Seriola lalandi · Seriola rivoliana · Lutjanus peru · Centropomus viridis · Totoaba macdonaldi",
        toc="Contents",
        meta=[("Project promoter", "SIGRICO, S.A.P.I. de C.V."),
              ("Legal representative", "C. Alberto Eduardo Zamacona Aboumrad"),
              ("Technical lead", "Biol. Gustavo Pineda Mahr"),
              ("Version", "3.0 — July 2026")],
        foot_place="La Paz, Baja California Sur · July 2026",
        presented="Submitted to the National Aquaculture and Fisheries Commission (CONAPESCA)",
        runfoot="PROYECTO THALASSA — SIGRICO, S.A.P.I. DE C.V.",
    ),
}

DOC_CSS = """
@page { size: Letter; margin: 22mm 19mm 20mm 19mm; }
@page cover { margin: 0; }
.cover { page: cover; }

body { font-size: 9.6pt; line-height: 1.6; }

/* ---------- COVER ---------- */
.cover {
  width: 215.9mm; height: 279.4mm; background: var(--abyss); color: #EAF3F0;
  position: relative; padding: 26mm 22mm; display: flex; flex-direction: column;
}
.cover::after { /* light shafts */
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background:
    conic-gradient(from 180deg at 50% -8%,
      transparent 70deg, rgba(95,224,206,0.13) 80deg, transparent 86deg,
      transparent 96deg, rgba(22,164,176,0.18) 104deg, transparent 110deg,
      transparent 124deg, rgba(95,224,206,0.10) 130deg, transparent 136deg,
      transparent 152deg, rgba(22,164,176,0.14) 158deg, transparent 164deg,
      transparent 360deg);
  filter: blur(6px);
}
.cover > * { position: relative; z-index: 1; }
.cover__logo { width: 52mm; }
.cover__org { margin-top: 3mm; font-size: 7pt; letter-spacing: 0.26em; text-transform: uppercase; color: rgba(234,243,240,0.62); }
.cover__mid { margin-top: auto; }
.cover h1 { font-size: 42pt; line-height: 1.0; letter-spacing: 0.01em; color: #fff; font-weight: 300;
            page-break-before: auto; break-before: auto; }
.cover h1::after { content: none; display: none; }   /* the cover has its own rule */
.cover .teal-rule { width: 46pt; height: 2pt; background: var(--teal); margin: 7mm 0; }
.cover__sub { font-size: 11pt; line-height: 1.5; color: #EAF3F0; max-width: 120mm; font-weight: 300; }
.cover__place { margin-top: 3mm; font-size: 9pt; color: rgba(234,243,240,0.7); }
.cover__species {
  margin-top: 8mm; font-family: "Caudex", serif; font-style: italic;
  font-size: 10.5pt; color: var(--aqua); line-height: 1.7;
}
.cover__meta { margin-top: auto; padding-top: 10mm; border-top: 0.5pt solid rgba(255,255,255,0.16); }
.cover__meta dl { display: grid; grid-template-columns: 42mm 1fr; gap: 2mm 4mm; font-size: 8.4pt; }
.cover__meta dt { color: rgba(234,243,240,0.5); text-transform: uppercase; letter-spacing: 0.12em; font-size: 7pt; padding-top: 1pt; }
.cover__meta dd { color: #EAF3F0; }
.cover__foot { margin-top: 7mm; display: flex; justify-content: space-between; align-items: flex-end; }
.cover__foot .presented { font-size: 7.6pt; color: rgba(234,243,240,0.55); max-width: 110mm; line-height: 1.5; }
.cover__foot .fish { width: 12mm; opacity: 0.9; }
.cover__place2 { font-size: 7.6pt; color: var(--gold-lit); letter-spacing: 0.14em; text-transform: uppercase; margin-top: 2mm; }

/* ---------- TOC ---------- */
.toc { page-break-after: always; }
.toc h2 { font-size: 24pt; margin-bottom: 2mm; }
.toc ol { list-style: none; margin-top: 8mm; }
.toc li {
  display: flex; align-items: baseline; gap: 3mm;
  padding: 3.2mm 0; border-bottom: 0.5pt solid var(--rule); font-size: 10pt;
}
.toc .n { font-weight: 500; color: var(--gold); min-width: 12mm; font-size: 8.5pt; letter-spacing: 0.08em; }
.toc .t { flex: 1; }
.toc .dots { flex: 1; border-bottom: 0.5pt dotted #C3CECB; transform: translateY(-2pt); }
.toc .p { color: var(--teal); font-weight: 500; font-size: 9pt; min-width: 10mm; text-align: right; }

/* ---------- CONTENT ---------- */
h1 {
  page-break-before: always; break-before: page;
  font-size: 22pt; color: var(--ink); margin: 0 0 2mm;
  padding-top: 2mm;
}
h1 + p, h1 + ul { margin-top: 4mm; }
h1::after { content: ""; display: block; width: 46pt; height: 2pt; background: var(--teal); margin-top: 4mm; }
h2 {
  font-size: 13pt; color: var(--ink); margin: 8mm 0 2.5mm;
  page-break-after: avoid; break-after: avoid;
}
h3 {
  font-size: 10.6pt; font-weight: 500; color: var(--teal);
  margin: 6mm 0 2mm; page-break-after: avoid; break-after: avoid;
}
p { margin: 0 0 3mm; text-align: justify; hyphens: auto; }
ul, ol { margin: 0 0 4mm 5mm; }
li { margin-bottom: 1.6mm; }
strong { font-weight: 500; }
em { font-family: "Caudex", serif; font-style: italic; }
hr { display: none; }

/* keep the first section from double-breaking after the TOC */
h1:first-of-type { page-break-before: auto; break-before: auto; }
"""


def normalized_body(md_path):
    """Drop the source title block and normalise heading depth so the
    roman-numeral sections always sit at H1 (the two agents differed)."""
    raw = md_path.read_text(encoding="utf-8")
    m = re.search(r"^(#+)\s+([IVXLC]+)\.", raw, flags=re.M)
    if not m:
        return raw
    body = raw[m.start():]
    dedent = len(m.group(1)) - 1
    if dedent > 0:
        body = re.sub(r"^#{%d}(?=#+\s)" % dedent, "", body, flags=re.M)
    return body


def build_html(lang, page_map=None):
    c = COPY[lang]
    body_md = normalized_body(c["md"])

    html_body = markdown.markdown(
        body_md, extensions=["tables", "sane_lists", "attr_list"]
    )

    # section list for the TOC (roman-numeral H1s)
    sections = re.findall(r"^# (.+)$", body_md, flags=re.M)
    toc_rows = []
    for s in sections:
        s_clean = re.sub(r"\s+", " ", s).strip()
        mm = re.match(r"^([IVXLC]+)\.\s*(.+)$", s_clean)
        num, txt = (mm.group(1), mm.group(2)) if mm else ("", s_clean)
        pg = (page_map or {}).get(s_clean, "")
        toc_rows.append(
            f'<li><span class="n">{num}</span><span class="t">{txt}</span>'
            f'<span class="dots"></span><span class="p">{pg}</span></li>'
        )

    meta_rows = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in c["meta"])

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<title>{c['stem']}</title>
<link rel="stylesheet" href="../brand/fonts.css">
<link rel="stylesheet" href="../brand/brand-print.css">
<style>{DOC_CSS}</style>
</head>
<body>

<section class="cover">
  <div>
    <img class="cover__logo" src="../brand/assets/logo-primary-white.png" alt="SigriCo">
    <div class="cover__org">{c['org']}</div>
  </div>

  <div class="cover__mid">
    <h1>{c['title']}</h1>
    <div class="teal-rule"></div>
    <p class="cover__sub">{c['sub']}</p>
    <p class="cover__place">{c['place']}</p>
    <p class="cover__species">{c['species']}</p>
  </div>

  <div class="cover__meta">
    <dl>{meta_rows}</dl>
    <div class="cover__foot">
      <div>
        <p class="presented">{c['presented']}</p>
        <p class="cover__place2">{c['foot_place']}</p>
      </div>
      <img class="fish" src="../brand/assets/mark-fish-gold.png" alt="">
    </div>
  </div>
</section>

<section class="toc">
  <p class="label"><span class="num">—</span>{c['toc']}</p>
  <h2>{c['toc']}</h2>
  <div class="rule-teal"></div>
  <ol>{''.join(toc_rows)}</ol>
</section>

{html_body}

</body>
</html>"""


def render(html_path, pdf_path):
    pdf_path = Path(pdf_path)
    pdf_path.unlink(missing_ok=True)          # never let a stale PDF be read back
    subprocess.run([
        CHROME, "--headless", "--disable-gpu", "--no-sandbox",
        "--allow-file-access-from-files",
        "--no-pdf-header-footer",
        "--virtual-time-budget=10000",   # let base64 fonts finish loading before print
        f"--print-to-pdf={pdf_path}",
        f"file://{html_path}",
    ], check=True, capture_output=True, timeout=180)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"Chrome produced no PDF for {html_path}")


FRONT_PAGES = 2   # cover + contents


def find_pages(lang):
    """Deterministic TOC pagination.

    Every roman section starts on a fresh page (page-break-before), so a
    section occupies the same number of pages alone as it does in the full
    document. Render each one standalone, count its pages, and accumulate.
    Far more reliable than scraping text out of subset-embedded fonts.
    """
    c = COPY[lang]
    body = normalized_body(c["md"])
    parts = [p for p in re.split(r"(?m)^(?=# )", body) if p.strip().startswith("# ")]

    out, cursor = {}, FRONT_PAGES + 1
    tmp_html = OUT / f"_probe-{lang}.html"
    tmp_pdf = OUT / f"_probe-{lang}.pdf"

    for part in parts:
        title = re.sub(r"\s+", " ", re.match(r"^# (.+)$", part, flags=re.M).group(1)).strip()
        frag = markdown.markdown(part, extensions=["tables", "sane_lists", "attr_list"])
        tmp_html.write_text(
            f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<link rel="stylesheet" href="../brand/fonts.css">'
            f'<link rel="stylesheet" href="../brand/brand-print.css">'
            f"<style>{DOC_CSS}</style></head><body>{frag}</body></html>",
            encoding="utf-8",
        )
        render(tmp_html, tmp_pdf)
        n = len(PdfReader(str(tmp_pdf)).pages)
        if re.match(r"^[IVXLC]+\.", title):
            out[title] = cursor
        cursor += n

    tmp_html.unlink(missing_ok=True)
    tmp_pdf.unlink(missing_ok=True)
    return out


def stamp(pdf_path, runfoot):
    """Stamp the running footer + page numbers (skip the cover)."""
    fut = ROOT / "fonts" / "futura-lt-light.ttf"
    futm = ROOT / "fonts" / "futura-lt-medium.ttf"
    pdfmetrics.registerFont(TTFont("FuturaLT", str(fut)))
    pdfmetrics.registerFont(TTFont("FuturaLT-Md", str(futm)))

    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    W, H = letter

    for i, page in enumerate(reader.pages):
        if i > 0:  # never stamp the cover
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=(W, H))
            y = 34
            c.setStrokeColorRGB(0.086, 0.643, 0.690)   # teal
            c.setLineWidth(0.75)
            c.line(54, y + 12, 54 + 26, y + 12)
            c.setFillColorRGB(0.43, 0.49, 0.47)
            c.setFont("FuturaLT", 6.6)
            c.drawString(54, y, runfoot)
            c.setFillColorRGB(0.086, 0.643, 0.690)
            c.setFont("FuturaLT-Md", 8)
            c.drawRightString(W - 54, y, str(i + 1))
            c.save()
            buf.seek(0)
            page.merge_page(PdfReader(buf).pages[0])
        writer.add_page(page)

    with open(pdf_path, "wb") as f:
        writer.write(f)


def main():
    for lang in ("es", "en"):
        c = COPY[lang]
        html = OUT / f"{c['stem']}.html"
        pdf = OUT / f"{c['stem']}.pdf"

        pmap = find_pages(lang)                      # deterministic page numbers
        html.write_text(build_html(lang, pmap), encoding="utf-8")
        render(html, pdf)
        stamp(pdf, c["runfoot"])

        n = len(PdfReader(str(pdf)).pages)
        print(f"{c['stem']}.pdf  ->  {n} pages, TOC entries mapped: {len(pmap)}  {sorted(pmap.values())}")


if __name__ == "__main__":
    main()
