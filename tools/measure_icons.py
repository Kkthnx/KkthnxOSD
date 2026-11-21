"""Per-icon vertical centers vs digit center in a 1x bar capture."""
import sys
from PIL import Image

im = Image.open(sys.argv[1]).convert("RGB")
w, h = im.size
blue = lambda p: p[2] > 120 and p[2] > p[0] + 50 and p[1] > p[0] + 20
white = lambda p: min(p) > 190
cols = [x for x in range(w) if any(blue(im.getpixel((x, y))) for y in range(h))]
runs, s0, pv = [], cols[0], cols[0]
for c in cols[1:]:
    if c > pv + 2:
        runs.append((s0, pv))
        s0 = c
    pv = c
runs.append((s0, pv))
for a, b in runs:
    pts = [(x, y) for x in range(a, b + 1) for y in range(h) if blue(im.getpixel((x, y)))]
    ys = [p[1] for p in pts]
    wt = [im.getpixel(p)[2] for p in pts]
    cy = sum(y * k for y, k in zip(ys, wt)) / sum(wt)
    print(f"icon x {a}-{b} w {b - a + 1} rows {min(ys)}-{max(ys)} bbox {(min(ys) + max(ys)) / 2} mass {cy:.2f}")
ys = [y for x in range(w) for y in range(h) if white(im.getpixel((x, y)))]
print("digits rows", min(ys), max(ys), "center", (min(ys) + max(ys)) / 2)
