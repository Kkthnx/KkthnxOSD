"""Report plate box, content box and padding for a 1x bar capture taken at screen origin."""
import sys
from PIL import Image

im = Image.open(sys.argv[1]).convert("RGB")
w, h = im.size
BG = (128, 0, 128)
plate = None
pts = [(x, y) for x in range(w) for y in range(h) if im.getpixel((x, y)) != BG]
px0, px1 = min(p[0] for p in pts), max(p[0] for p in pts)
py0, py1 = min(p[1] for p in pts), max(p[1] for p in pts)
pc = im.getpixel((px0 + 1, py1 - 1))

def is_content(p):
    return sum(abs(a - b) for a, b in zip(p, pc)) > 60 and p != BG

cp = [(x, y) for x in range(px0, px1 + 1) for y in range(py0, py1 + 1) if is_content(im.getpixel((x, y)))]
cx0, cx1 = min(p[0] for p in cp), max(p[0] for p in cp)
cy0, cy1 = min(p[1] for p in cp), max(p[1] for p in cp)
print(f"plate x {px0}-{px1} y {py0}-{py1} center {(px0 + px1) / 2}")
print(f"content x {cx0}-{cx1} y {cy0}-{cy1} center {(cx0 + cx1) / 2}")
print(f"pad left {cx0 - px0} right {px1 - cx1} top {cy0 - py0} bottom {py1 - cy1}")
