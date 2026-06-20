"""Extract output figures from the executed notebooks into slides/figs/.

For each of the three notebooks, walk the cells in order; whenever a code cell
has an image output, save it as slides/figs/<mod>_NN.png and record the nearest
preceding markdown heading. Writes slides/figs/manifest.json so the deck
generator knows which figure belongs to which step.
"""
import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB_DIR = ROOT / "notebooks"
FIG_DIR = ROOT / "slides" / "figs"
FIG_DIR.mkdir(parents=True, exist_ok=True)

NOTEBOOKS = {
    "mod1": "01_satellite_data_extraction.ipynb",
    "mod2": "02_insitu_timeseries_ml.ipynb",
    "mod3": "03_build_database.ipynb",
}


def first_heading(md_text):
    for line in md_text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()
    return None


def main():
    manifest = {}
    for mod, fname in NOTEBOOKS.items():
        nb = json.loads((NB_DIR / fname).read_text(encoding="utf-8"))
        figs = []
        current_heading = None
        n = 0
        for cell in nb["cells"]:
            if cell["cell_type"] == "markdown":
                h = first_heading("".join(cell["source"]))
                if h:
                    current_heading = h
                continue
            if cell["cell_type"] != "code":
                continue
            # find image outputs
            for out in cell.get("outputs", []):
                data = out.get("data", {})
                png = data.get("image/png")
                if not png:
                    continue
                n += 1
                fn = f"{mod}_{n:02d}.png"
                (FIG_DIR / fn).write_bytes(base64.b64decode(png))
                figs.append({"file": fn, "heading": current_heading})
                break   # one figure per cell is enough
        manifest[mod] = figs
        print(f"{mod}: {len(figs)} figures")
        for f in figs:
            print(f"    {f['file']}  <-  {f['heading']}")
    (FIG_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print("Manifest written to", FIG_DIR / "manifest.json")


if __name__ == "__main__":
    main()
