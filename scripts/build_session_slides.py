# -*- coding: utf-8 -*-
"""Build the Live Session slide deck — slides/session.html.

A single, polished deck for the 1-hour live session: a strong story, a clear
agenda, one idea per slide, and the real figures the notebook produces. Same
magazine identity as the workshop, keyboard + hash navigation.
Run:  python scripts/build_session_slides.py
"""
import base64
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
SLIDES = ROOT / "slides"
FIGS   = SLIDES / "figs"

# ── Embed figures as base64 so the deck is a single portable file ─────────
def fig_data_uri(name):
    p = FIGS / f"sess_{name}.png"
    if not p.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()

CSS = """
:root{
  --ink:#0d1b2a; --ink2:#16263a; --paper:#f6f1e7; --accent:#c2410c;
  --accent2:#2a9d8f; --gold:#e9a44b; --grey:#6b6157; --cream:#cbd5dd;
  --serif:"Iowan Old Style","Palatino Linotype","Palatino","Georgia",serif;
  --mono:"JetBrains Mono","IBM Plex Mono",ui-monospace,monospace;
}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{height:100%;background:#06101a;}
body{font-family:var(--serif);display:flex;align-items:center;justify-content:center;min-height:100vh;}
.deck{position:relative;width:min(96vw,1320px);aspect-ratio:16/9;background:var(--paper);
  overflow:hidden;box-shadow:0 40px 120px rgba(0,0,0,.6);border-radius:2px;}
.slide{position:absolute;inset:0;padding:3.4rem 4.2rem;display:none;flex-direction:column;}
.slide.active{display:flex;}
.kick{font-family:var(--mono);font-size:.7rem;letter-spacing:.28em;text-transform:uppercase;
  color:var(--accent);margin-bottom:1.1rem;}
h1{font-size:4rem;line-height:1.02;font-weight:500;font-style:italic;letter-spacing:-.02em;color:var(--ink);}
h2{font-size:2.5rem;line-height:1.05;font-weight:500;letter-spacing:-.02em;color:var(--ink);margin-bottom:.4rem;}
p{font-size:1.18rem;line-height:1.5;color:#2a2520;}
.lede{font-size:1.5rem;line-height:1.38;color:#33291f;max-width:54ch;}
.muted{color:var(--grey);}
.foot{position:absolute;bottom:1.2rem;left:4.2rem;right:4.2rem;display:flex;justify-content:space-between;
  font-family:var(--mono);font-size:.62rem;letter-spacing:.18em;text-transform:uppercase;color:var(--grey);
  border-top:1px solid #d8cfbc;padding-top:.6rem;}
/* dark slides */
.dark{background:radial-gradient(120% 120% at 20% 0%, var(--ink2) 0%, var(--ink) 70%);}
.dark h1,.dark h2{color:var(--paper);}
.dark p{color:var(--cream);}
.dark .lede{color:#dfe7ee;}
.dark .kick{color:var(--gold);}
.dark .foot{color:#5b6b78;border-top-color:#23323f;}
/* cover */
.cover h1{font-size:4.6rem;max-width:16ch;}
.stats{display:flex;gap:2.6rem;margin-top:auto;}
.stat .n{font-size:2.7rem;font-style:italic;color:var(--gold);line-height:1;}
.stat .k{font-family:var(--mono);font-size:.64rem;letter-spacing:.14em;text-transform:uppercase;color:var(--cream);margin-top:.45rem;}
/* figure slide: text left, image right */
.fly{display:grid;grid-template-columns:0.82fr 1.18fr;gap:2.4rem;flex:1;min-height:0;align-items:center;}
.fly .txt{display:flex;flex-direction:column;justify-content:center;}
.fly .shot{height:100%;display:flex;align-items:center;justify-content:center;
  background:var(--ink);border-radius:6px;padding:.6rem;}
.fly .shot img{max-width:100%;max-height:100%;object-fit:contain;border-radius:3px;}
.fly.wide{grid-template-columns:1fr;}            /* full-width figure */
.fly.wide .shot{width:100%;}
.tag{display:inline-block;font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;
  padding:.2rem .6rem;border-radius:99px;margin-bottom:.9rem;width:max-content;}
.tag.live{background:#dcefe6;color:#0f5f4f;}
.tag.edit{background:#fbe6d8;color:var(--accent);}
.bullets{margin-top:.8rem;}
.bullets li{font-size:1.12rem;line-height:1.5;color:#2a2520;margin:.1rem 0 .55rem 1.1rem;}
.bignum{font-family:var(--mono);color:var(--accent);font-weight:600;}
.agenda{display:flex;flex-direction:column;gap:.55rem;margin-top:.4rem;flex:1;justify-content:center;}
.row{display:grid;grid-template-columns:3.2rem 1fr;gap:1.2rem;align-items:baseline;
  padding-bottom:.5rem;border-bottom:1px dashed #d8cfbc;}
.row .i{font-family:var(--mono);color:var(--accent);font-size:1.2rem;}
.row .t{font-size:1.16rem;color:#2a2520;}
.row .t b{color:var(--ink);}
.take{display:grid;grid-template-columns:2.4rem 1fr;gap:1rem;align-items:baseline;margin-bottom:1rem;}
.take .i{font-family:var(--mono);color:var(--gold);font-size:1.3rem;}
.formula{font-family:var(--mono);font-size:1.2rem;background:rgba(0,0,0,.04);border-left:3px solid var(--accent2);
  padding:.7rem 1rem;margin:.8rem 0;color:var(--ink);width:max-content;}
.nav{position:fixed;bottom:1.3rem;left:50%;transform:translateX(-50%);display:flex;gap:.3rem;
  background:rgba(255,255,255,.1);padding:.3rem .6rem;border-radius:999px;backdrop-filter:blur(8px);}
.nav button{background:none;border:0;color:#e7eef4;font-family:var(--mono);font-size:.78rem;cursor:pointer;padding:.2rem .6rem;border-radius:99px;}
.nav button:hover{background:rgba(255,255,255,.16);}
.nav .ct{color:#aebcc9;font-family:var(--mono);font-size:.72rem;padding:.2rem .5rem;}
"""

JS = """
const s=[...document.querySelectorAll('.slide')];let i=0;
const show=n=>{i=(n+s.length)%s.length;s.forEach((x,k)=>x.classList.toggle('active',k===i));
document.querySelector('.ct').textContent=(i+1)+' / '+s.length;location.hash=i+1;};
document.querySelector('.pv').onclick=()=>show(i-1);
document.querySelector('.nx').onclick=()=>show(i+1);
addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key===' ')show(i+1);if(e.key==='ArrowLeft')show(i-1);});
show((parseInt(location.hash.slice(1))||1)-1);
"""

FOOT = "Mar Menor · Live Earth-Observation Session"


def cover():
    return f"""<section class="slide dark cover active">
  <div class="kick">Live Earth-Observation Session · 60 minutes</div>
  <h1>Watch a lagoon<br>collapse, from space.</h1>
  <p class="lede" style="margin-top:1.4rem;">In one hour you download real satellite
    and pollution data with your own hands — and see the 2021 Mar Menor crisis
    appear on screen. No install, mostly no account.</p>
  <div class="stats">
    <div class="stat"><div class="n">10 m</div><div class="k">Sentinel-2 detail</div></div>
    <div class="stat"><div class="n">5</div><div class="k">live data sources</div></div>
    <div class="stat"><div class="n">7</div><div class="k">hands-on steps</div></div>
    <div class="stat"><div class="n">0</div><div class="k">software to install</div></div>
  </div>
  <div class="foot"><span>00</span><span>{FOOT}</span></div>
</section>"""


def story():
    return f"""<section class="slide dark">
  <div class="kick">The place · the crisis</div>
  <h2 style="color:#fff;max-width:18ch;">A small sea that broke, on camera.</h2>
  <div class="fly" style="margin-top:1.4rem;">
    <div class="txt">
      <p class="lede">The Mar Menor is Europe's largest coastal lagoon — shallow,
        closed, ringed by farmland.</p>
      <p style="margin-top:1rem;">In <b style="color:#fff;">August 2021</b> it turned
        green and three tonnes of fish died: an algal bloom, fed by farm runoff and a
        marine heatwave, stripped the water of oxygen.</p>
      <p style="margin-top:1rem;" class="muted">Every stage of it was recorded from
        orbit — free, open, and the subject of today's session.</p>
    </div>
    <div class="shot"><img src="{fig_data_uri('truecolor')}" alt="Mar Menor true colour"></div>
  </div>
  <div class="foot"><span>01</span><span>{FOOT}</span></div>
</section>"""


def agenda():
    rows = [
        ("1", "<b>Browse</b> any date from orbit — NASA GIBS"),
        ("2", "<b>Download</b> real Sentinel-2 (10 m) — only our window"),
        ("3", "<b>Measure</b> the bloom — the NDCI chlorophyll index"),
        ("4", "<b>Add</b> live pollution data — air quality"),
        ("5", "<b>Unlock</b> server products with a free Copernicus key"),
        ("6", "<b>Detect</b> the crises with machine learning"),
        ("7", "<b>Store &amp; query</b> it all in a database"),
    ]
    items = "".join(f'<div class="row"><span class="i">{i}</span><span class="t">{t}</span></div>'
                    for i, t in rows)
    return f"""<section class="slide">
  <div class="kick">What we'll do together</div>
  <h2>Seven steps, one hour.</h2>
  <div class="agenda">{items}</div>
  <div class="foot"><span>02</span><span>{FOOT}</span></div>
</section>"""


def figure_slide(num, kick, title, fig, tag, blurb, bullets=None, wide=False,
                 formula=None):
    tag_html = f'<span class="tag {tag[0]}">{tag[1]}</span>' if tag else ""
    bl = ""
    if bullets:
        bl = '<ul class="bullets">' + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>"
    fm = f'<div class="formula">{formula}</div>' if formula else ""
    if wide:
        body = f"""<div class="fly wide">
          <div class="txt">{tag_html}<p class="lede">{blurb}</p>{fm}{bl}</div>
          <div class="shot"><img src="{fig_data_uri(fig)}" alt="{title}"></div>
        </div>"""
    else:
        body = f"""<div class="fly">
          <div class="txt">{tag_html}<p class="lede">{blurb}</p>{fm}{bl}</div>
          <div class="shot"><img src="{fig_data_uri(fig)}" alt="{title}"></div>
        </div>"""
    return f"""<section class="slide">
  <div class="kick">{kick}</div>
  <h2>{title}</h2>
  {body}
  <div class="foot"><span>{num}</span><span>{FOOT}</span></div>
</section>"""


def takeaways():
    items = [
        ("Free &amp; open", "the data that recorded a disaster is one request away — no paywall."),
        ("Move few pixels", "search a catalogue, read only your window, let the server compute."),
        ("One pattern", "discover → take a subset → analyse → store. It works for any coast."),
        ("You did it live", "browse, download, measure, detect and store — in one hour, no install."),
    ]
    rows = "".join(f'<div class="take"><span class="i">{k+1}</span>'
                   f'<span><b>{h}.</b> <span class="muted">{t}</span></span></div>'
                   for k, (h, t) in enumerate(items))
    return f"""<section class="slide dark">
  <div class="kick">What you take away</div>
  <h2 style="color:#fff;">The barrier was never access.</h2>
  <div style="margin-top:1.4rem;flex:1;display:flex;flex-direction:column;justify-content:center;">{rows}</div>
  <p class="muted" style="font-family:var(--mono);font-size:.8rem;letter-spacing:.1em;">
    Go further → notebooks 01 · 02 · 03 in the repo</p>
  <div class="foot"><span>fin</span><span>{FOOT}</span></div>
</section>"""


slides = [
    cover(),
    story(),
    agenda(),
    figure_slide("03", "Step 1 · browse", "Find a clear day from orbit.", "gibs",
                 ("live", "live · no login"),
                 "NASA GIBS returns a true-colour picture of any day since 2000. "
                 "We scout for cloud-free dates before downloading the heavy data.",
                 bullets=["One URL, one image — change the date and re-run."]),
    figure_slide("04", "Step 2 · download", "What each wavelength sees.", "bands",
                 ("live", "live · no login"),
                 "Sentinel-2 records separate bands. We read only our window (≈16 MB, "
                 "not 800). Watch the bloom flip from dark in red to bright in red-edge.",
                 wide=True),
    figure_slide("05", "Step 3 · measure", "The bloom, as a number.", "ndci",
                 ("live", "live"),
                 "The NDCI turns two bands into chlorophyll at every pixel. Land is "
                 "greyed out; the bloom is strongest in the north-west, by the farmland.",
                 formula="NDCI = (B05 − B04) / (B05 + B04)"),
    figure_slide("06", "Step 4 · pollution", "More than water colour.", "airquality",
                 ("live", "live · no login"),
                 "A keyless API returns hourly PM2.5, PM10 and ozone — the dust over the "
                 "same farmland that feeds the lagoon. Same pattern: ask, receive, plot."),
    figure_slide("07", "Step 5 · go pro", "Five products, one request.", "wq_panel",
                 ("edit", "free account"),
                 "With a free Copernicus key the server computes products for you. One "
                 "call returns the three optical components of the water — plus the bloom peak.",
                 wide=True,
                 bullets=["True colour · chlorophyll · bloom hotspots · turbidity · CDOM."]),
    figure_slide("08", "Step 6 · machine learning", "It finds the crises itself.", "anomaly",
                 ("live", "live"),
                 "An Isolation Forest, trained only on the calm years, flags every later "
                 "day that looks abnormal — and rediscovers the 2019 and 2021 crises "
                 "it was never shown.",
                 bullets=["100% of the documented crisis days, caught out-of-sample."]),
    takeaways(),
]

html = (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Mar Menor — Live Session</title><style>{CSS}</style></head><body>"
        f"<div class='deck'>{''.join(slides)}</div>"
        f"<div class='nav'><button class='pv'>← prev</button>"
        f"<span class='ct'>1 / {len(slides)}</span>"
        f"<button class='nx'>next →</button></div>"
        f"<script>{JS}</script></body></html>")

(SLIDES / "session.html").write_text(html, encoding="utf-8")
print(f"session.html written — {len(slides)} slides")
