"""Build detailed, step-by-step HTML slide decks for the three modules.

Each notebook step becomes a slide that shows: what happens, the key code, and
the real figure produced by the executed notebook (extracted to slides/figs/ by
extract_figures.py). Same magazine style as slides/intro.html, keyboard nav.

Run:  python scripts/extract_figures.py   # once, to refresh figures
      python scripts/build_slides_html.py
"""
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLIDES = ROOT / "slides"

# ── Shared CSS (intro.html palette) ──────────────────────────────────────
CSS = """
:root{
  --ink:#0e1a26; --paper:#f6f1e7; --paper-2:#eee5d4; --accent:#c2410c;
  --accent-2:#115e59; --grey:#6b6157; --rule:#1e2e3a;
  --serif:"Iowan Old Style","Source Serif Pro","Apple Garamond","Baskerville","Times New Roman",serif;
  --mono:"JetBrains Mono","IBM Plex Mono",ui-monospace,monospace;
}
*{box-sizing:border-box;}
html,body{margin:0;padding:0;background:var(--ink);}
body{font-family:var(--serif);color:var(--ink);min-height:100vh;display:flex;align-items:center;justify-content:center;}
.deck{width:min(96vw,1320px);aspect-ratio:16/9;background:var(--paper);box-shadow:0 30px 90px rgba(0,0,0,.5);position:relative;overflow:hidden;}
.slide{position:absolute;inset:0;padding:3.2rem 4rem;display:none;flex-direction:column;
  background-image:radial-gradient(rgba(0,0,0,.03) 1px,transparent 1px);background-size:4px 4px;}
.slide.active{display:flex;}
.label{font-family:var(--mono);font-size:.66rem;letter-spacing:.22em;text-transform:uppercase;color:var(--accent);margin-bottom:.7rem;}
h1{font-size:3.8rem;font-weight:500;line-height:1.02;letter-spacing:-.025em;margin:0 0 1rem;font-style:italic;}
h2{font-size:2.1rem;font-weight:500;line-height:1.08;letter-spacing:-.02em;margin:0 0 .5rem;}
h3{font-size:1.05rem;font-weight:600;margin:0 0 .35rem;}
p,li{font-size:1.02rem;line-height:1.5;color:#2a2520;}
.lede{font-size:1.3rem;line-height:1.4;color:#3a2e22;max-width:60ch;}
hr.rule{border:0;height:1px;background:var(--rule);margin:.3rem 0 1.1rem;width:100%;}
.footer{position:absolute;bottom:1rem;left:4rem;right:4rem;display:flex;justify-content:space-between;
  font-family:var(--mono);font-size:.62rem;letter-spacing:.15em;text-transform:uppercase;color:var(--grey);
  border-top:1px solid #d6cdba;padding-top:.55rem;}
.nav{position:fixed;bottom:1.1rem;left:50%;transform:translateX(-50%);display:flex;gap:.3rem;
  background:rgba(255,255,255,.08);padding:.3rem .55rem;border-radius:999px;backdrop-filter:blur(8px);z-index:10;}
.nav button{background:none;border:0;color:var(--paper-2);font-family:var(--mono);font-size:.75rem;cursor:pointer;padding:.2rem .5rem;border-radius:99px;}
.nav button:hover{background:rgba(255,255,255,.12);}
.counter{color:var(--paper-2);font-family:var(--mono);font-size:.7rem;padding:.2rem .5rem;}
code{font-family:var(--mono);font-size:.92em;background:rgba(0,0,0,.05);padding:.05em .3em;border-radius:3px;}
pre.code{font-family:var(--mono);font-size:.82rem;background:var(--ink);color:#d4cdb9;
  padding:1.1rem 1.3rem;border-radius:5px;white-space:pre;line-height:1.45;overflow:hidden;margin:0;}
pre.code .c{color:#7f7361;font-style:italic;}
pre.code .k{color:#e9a44b;}
pre.code .s{color:#b8c66e;}
pre.code .n{color:#86b8c9;}
ul.tight{padding-left:1.1rem;margin:.3rem 0;}
ul.tight li{margin-bottom:.3rem;}
.fig{background:#0d1b2a;border-radius:5px;padding:.5rem;display:flex;align-items:center;justify-content:center;}
.fig img{max-width:100%;max-height:100%;object-fit:contain;border-radius:3px;}
/* step layout: code left, figure right */
.step{display:grid;grid-template-columns:1fr 1fr;gap:1.6rem;flex:1;min-height:0;align-items:stretch;}
.step .col{display:flex;flex-direction:column;min-height:0;}
.step .col.explain p{margin:.2rem 0 .7rem;}
.step .fig{flex:1;min-height:0;}
/* figure-dominant layout */
.figbig{display:grid;grid-template-columns:1fr;gap:.8rem;flex:1;min-height:0;}
.figbig .fig{flex:1;min-height:0;}
.figbig .cap{display:flex;gap:1.4rem;}
.figbig .cap>div{flex:1;}
/* two-text columns */
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:2.2rem;flex:1;align-items:start;}
.pill{display:inline-block;font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;
  padding:.15rem .5rem;border-radius:99px;margin-bottom:.6rem;}
.pill.run{background:#dcefe6;color:var(--accent-2);}
.pill.edit{background:#fbe6d8;color:var(--accent);}
.pill.concept{background:#e7e2f3;color:#5b4a8a;}
.stat-row{display:flex;gap:2.4rem;margin-top:auto;padding-top:1.2rem;}
.stat{display:flex;flex-direction:column;}
.stat .n{font-size:2.6rem;font-weight:500;line-height:1;color:var(--accent);font-style:italic;}
.stat .k{font-family:var(--mono);font-size:.66rem;letter-spacing:.13em;text-transform:uppercase;color:var(--grey);margin-top:.4rem;}
.divider{background:linear-gradient(160deg,var(--ink) 0%,#16263a 100%);color:var(--paper);}
.divider h1{color:var(--paper);}
.divider .lede{color:#cbd5dd;}
.divider .label{color:#e9a44b;}
.cover{background:linear-gradient(160deg,var(--ink) 0%,#16263a 100%);color:var(--paper);}
.cover h1{color:var(--paper);font-size:4.6rem;}
.cover .lede{color:#cbd5dd;}
.cover .label{color:#e9a44b;}
.cover .stat .k{color:#cbd5dd;}
.takeaway{display:grid;grid-template-columns:34px 1fr;gap:1rem;align-items:baseline;margin-bottom:.8rem;}
.takeaway .tn{font-family:var(--mono);font-size:1.2rem;color:var(--accent);font-weight:600;}
table.mini{border-collapse:collapse;width:100%;margin-top:.4rem;}
table.mini td,table.mini th{text-align:left;padding:.32rem .5rem;border-bottom:1px solid #d6cdba;font-size:.9rem;}
table.mini th{font-family:var(--mono);font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;color:var(--accent-2);}
.formula{font-size:1.25rem;text-align:center;background:rgba(255,255,255,.5);border-left:3px solid var(--accent-2);
  padding:.8rem 1rem;margin:.6rem 0;font-family:var(--mono);}
"""

JS = """
const slides=[...document.querySelectorAll('.slide')];let i=0;
const show=n=>{i=(n+slides.length)%slides.length;
 slides.forEach((s,k)=>s.classList.toggle('active',k===i));
 document.getElementById('counter').textContent=(i+1)+' / '+slides.length;
 location.hash=i+1;};
document.getElementById('next').onclick=()=>show(i+1);
document.getElementById('prev').onclick=()=>show(i-1);
document.addEventListener('keydown',e=>{
 if(e.key==='ArrowRight'||e.key===' ')show(i+1);
 if(e.key==='ArrowLeft')show(i-1);});
const start=parseInt(location.hash.replace('#',''))||1;show(start-1);
"""


# ── Tiny code highlighter (comments, keywords, strings) ──────────────────
KEYWORDS = ["import", "from", "def", "return", "for", "in", "if", "else", "with",
            "as", "True", "False", "None", "and", "or", "not", "lambda"]

def hl(code):
    out = []
    for line in code.split("\n"):
        esc = html.escape(line)
        if esc.strip().startswith("#"):
            out.append(f'<span class="c">{esc}</span>')
            continue
        # strings
        esc = _wrap_strings(esc)
        for kw in KEYWORDS:
            esc = _wrap_kw(esc, kw)
        out.append(esc)
    return "\n".join(out)

def _wrap_strings(s):
    res, in_s, q, buf = [], False, "", ""
    i = 0
    while i < len(s):
        ch = s[i]
        if not in_s and ch in ('"', "'"):
            in_s, q, buf = True, ch, ch
        elif in_s and ch == q:
            buf += ch; res.append(f'<span class="s">{buf}</span>'); in_s = False; buf = ""
        elif in_s:
            buf += ch
        else:
            res.append(ch)
        i += 1
    if in_s:
        res.append(f'<span class="s">{buf}</span>')
    return "".join(res)

def _wrap_kw(s, kw):
    import re
    return re.sub(rf'(?<![\w.])({kw})(?![\w])', r'<span class="k">\1</span>', s)


# ── Slide builders ───────────────────────────────────────────────────────
def cover(label, title_html, lede, stats, foot):
    s = '<section class="slide active cover">'
    s += f'<div class="label">{label}</div>'
    s += f'<h1>{title_html}</h1>'
    s += '<hr class="rule" style="background:var(--accent);width:200px;margin-top:1.4rem;">'
    s += f'<p class="lede">{lede}</p>'
    s += '<div class="stat-row">'
    for n, k in stats:
        s += f'<div class="stat"><span class="n">{n}</span><span class="k">{k}</span></div>'
    s += '</div>'
    s += f'<div class="footer"><span>{foot[0]}</span><span>{foot[1]}</span></div>'
    return s + '</section>'

def divider(label, title, lede, foot):
    return (f'<section class="slide divider"><div class="label">{label}</div>'
            f'<h1 style="font-size:3.2rem;margin-top:.5rem;">{title}</h1>'
            f'<hr class="rule" style="background:var(--accent);width:160px;">'
            f'<p class="lede">{lede}</p>'
            f'<div class="footer"><span>{foot[0]}</span><span>{foot[1]}</span></div></section>')

def step(label, title, explain_html, code, fig, foot, pill=("run", "RUN")):
    """Code on the left, figure on the right."""
    pill_html = f'<span class="pill {pill[0]}">{pill[1]}</span>' if pill else ''
    fig_html = (f'<div class="fig"><img src="figs/{fig}" alt=""></div>' if fig
                else '<div class="fig" style="background:none;"></div>')
    code_html = (f'<pre class="code">{hl(code)}</pre>' if code else '')
    return (f'<section class="slide"><div class="label">{label}</div>'
            f'<h2>{title}</h2><hr class="rule">'
            f'<div class="step"><div class="col explain">{pill_html}{explain_html}{code_html}</div>'
            f'<div class="col">{fig_html}</div></div>'
            f'<div class="footer"><span>{foot[0]}</span><span>{foot[1]}</span></div></section>')

def figbig(label, title, fig, caption_cols, foot, pill=("run", "RUN")):
    """Big figure on top, caption columns below."""
    pill_html = f'<span class="pill {pill[0]}">{pill[1]}</span>' if pill else ''
    caps = "".join(f'<div>{c}</div>' for c in caption_cols)
    return (f'<section class="slide"><div class="label">{label}</div>'
            f'<h2>{pill_html}{title}</h2><hr class="rule">'
            f'<div class="figbig"><div class="fig"><img src="figs/{fig}" alt=""></div>'
            f'<div class="cap">{caps}</div></div>'
            f'<div class="footer"><span>{foot[0]}</span><span>{foot[1]}</span></div></section>')

def concept(label, title, left_html, right_html, foot, pill=("concept", "CONCEPT")):
    pill_html = f'<span class="pill {pill[0]}">{pill[1]}</span>' if pill else ''
    return (f'<section class="slide"><div class="label">{label}</div>'
            f'<h2>{pill_html}{title}</h2><hr class="rule">'
            f'<div class="two-col"><div>{left_html}</div><div>{right_html}</div></div>'
            f'<div class="footer"><span>{foot[0]}</span><span>{foot[1]}</span></div></section>')

def takeaways(label, title, items, foot):
    body = ""
    for n, (head, txt) in enumerate(items, 1):
        body += (f'<div class="takeaway"><span class="tn">{n}</span>'
                 f'<span><strong>{head}</strong> {txt}</span></div>')
    return (f'<section class="slide divider"><div class="label">{label}</div>'
            f'<h1 style="font-size:2.6rem;">{title}</h1><hr class="rule">'
            f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center;">{body}</div>'
            f'<div class="footer"><span>{foot[0]}</span><span>{foot[1]}</span></div></section>')


def render(title, slides):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{CSS}</style></head><body>'
            f'<div class="deck">{"".join(slides)}</div>'
            f'<div class="nav"><button id="prev">&larr; prev</button>'
            f'<span class="counter" id="counter"></span>'
            f'<button id="next">next &rarr;</button></div>'
            f'<script>{JS}</script></body></html>')


# =========================================================================
# Build each module from its own content module
# =========================================================================
from slides_content import MODULE1, MODULE2, MODULE3   # noqa: E402

BUILDERS = {"cover": cover, "divider": divider, "step": step,
            "figbig": figbig, "concept": concept, "takeaways": takeaways}

def build(spec, outfile, title):
    out = []
    for kind, args in spec:
        out.append(BUILDERS[kind](*args))
    (SLIDES / outfile).write_text(render(title, out), encoding="utf-8")
    print(f"{outfile}: {len(spec)} slides")


if __name__ == "__main__":
    build(MODULE1, "module1.html", "Mar Menor Workshop — Module 1")
    build(MODULE2, "module2.html", "Mar Menor Workshop — Module 2")
    build(MODULE3, "module3.html", "Mar Menor Workshop — Module 3")
    print("Done.")
