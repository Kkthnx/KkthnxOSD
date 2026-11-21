"""Build the KkthnxOSD bar for RTSS, writing the icon atlas, the OVL layout and the OVX import package.

Usage is python build_osd.py <output folder>
Tuning values below can be overridden with OSD_* environment variables while testing.
"""
import hashlib
import io
import math
import os
import struct
import sys
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

NAME = "Kkthnx_OSD_Bar"
PNG = None  # set by build_atlas, includes a content hash

def env(key, default):
    return type(default)(os.environ.get(f"OSD_{key}", default))

# Typography, measured on a 1440p screen with ZoomRatio 1
FONT_FACE = "Bahnschrift"
FONT_HEIGHT = env("FONT", 15)     # pixels
FONT_WEIGHT = 600
LINE = env("LINE", 18)            # rendered line height, measured
ICON = env("ICON", 15)            # icon sprite width and height
ICON_TOP = env("ICON_TOP", 2)     # icon offset inside the line so it centers on the digits
GRAPH_W = env("GRAPH_W", 40)
GRAPH_H = env("GRAPH_H", 18)
GRAPH_M = env("GRAPH_M", 3)        # inner margin, centers the trace on the digits
GRAPH_FLAGS = env("GRAPH_FLAGS", "10")  # hex RTSS graph flags, 10 = line over a faint tinted track
GRAPH_MAX_MS = env("GRAPH_MAX", 50.0)  # RTSS drops values above max, so keep headroom for stutters

# Palette from a colorblind-safe reference set, contrast checked against the backplate
PLATE = "C80B0E14"     # AARRGGBB, 78% opaque near-black
VALUE = "E6EDF3"       # values
UNIT = "8B949E"        # units, low emphasis
ACCENT_HEX = "56B4E9"  # icons and graph, sky blue
ACCENT = tuple(int(ACCENT_HEX[i:i + 2], 16) for i in (0, 2, 4))
WARN = "F0E442"        # yellow
CRIT = "FF7A45"        # vermillion lifted for dark backgrounds

# Thresholds tuned for a high refresh display, warn below 120 FPS and flag below 60
FPS_CRIT, FPS_WARN = 60, 120
FT_WARN, FT_CRIT = 8.4, 16.7                 # ms, mirrors 120 and 60 FPS
GPU_WARN, GPU_CRIT = 75, 83                  # degrees C
CPU_WARN, CPU_CRIT = 80, 90                  # degrees C

SS = 8  # supersampling factor for icon drawing, icons are designed on a 14 unit grid

def canvas():
    s = 14 * SS
    return Image.new("L", (s, s), 0), s

def W(px):
    return max(1, round(px * SS))

def icon_fps():
    im, s = canvas()
    d = ImageDraw.Draw(im)
    # speedometer: 240 degree arc and needle, content centered on the grid
    pad = 1.0 * SS
    box = [pad, pad + 1.5 * SS, s - pad, s - pad + 1.5 * SS]
    d.arc(box, 150, 390, fill=255, width=W(1.6))
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    a = math.radians(-50)
    r = (box[2] - box[0]) / 2 - 2.2 * SS
    d.line([cx, cy, cx + r * math.cos(a), cy + r * math.sin(a)], fill=255, width=W(1.6))
    rr = 1.6 * SS
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=255)
    return im

def icon_ft():
    im, s = canvas()
    d = ImageDraw.Draw(im)
    # pulse line: frame pacing trace
    y = s * 0.5
    pts = [(0.6, y), (4.0, y), (5.6, y - 4.6 * SS), (7.6, y + 4.2 * SS), (9.2, y - 1.6 * SS), (10.2, y), (13.4, y)]
    d.line([(x * SS, yy) for x, yy in pts], fill=255, width=W(1.6), joint="curve")
    return im

def icon_gpu():
    im, s = canvas()
    d = ImageDraw.Draw(im)
    # graphics card: body with fan, bracket and slot pins
    d.rounded_rectangle([1.6 * SS, 3.0 * SS, 13.2 * SS, 10.6 * SS], radius=1.2 * SS, outline=255, width=W(1.4))
    cx, cy, r = 8.4 * SS, 6.8 * SS, 2.4 * SS
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=255, width=W(1.3))
    d.ellipse([cx - 0.7 * SS, cy - 0.7 * SS, cx + 0.7 * SS, cy + 0.7 * SS], fill=255)
    d.rectangle([0.2 * SS, 1.8 * SS, 1.4 * SS, 12.6 * SS], fill=255)
    for x in (4.0, 6.0, 8.0, 10.0):
        d.rectangle([x * SS, 10.6 * SS, (x + 1.1) * SS, 12.4 * SS], fill=255)
    return im

def icon_cpu():
    im, s = canvas()
    d = ImageDraw.Draw(im)
    # chip: package, die, pins on four sides
    d.rounded_rectangle([3.0 * SS, 3.0 * SS, 11.0 * SS, 11.0 * SS], radius=1.0 * SS, outline=255, width=W(1.4))
    d.rectangle([5.5 * SS, 5.5 * SS, 8.5 * SS, 8.5 * SS], fill=255)
    for p in (5.0, 8.0):
        a, b = p * SS, (p + 1.0) * SS
        d.rectangle([a, 0.6 * SS, b, 3.0 * SS], fill=255)
        d.rectangle([a, 11.0 * SS, b, 13.4 * SS], fill=255)
        d.rectangle([0.6 * SS, a, 3.0 * SS, b], fill=255)
        d.rectangle([11.0 * SS, a, 13.4 * SS, b], fill=255)
    return im

def icon_ram():
    im, s = canvas()
    d = ImageDraw.Draw(im)
    # memory module: board, chips, contacts
    d.rounded_rectangle([0.6 * SS, 3.4 * SS, 13.4 * SS, 10.0 * SS], radius=0.8 * SS, outline=255, width=W(1.3))
    for x in (2.4, 5.6, 8.8):
        d.rectangle([x * SS, 5.0 * SS, (x + 2.4) * SS, 8.2 * SS], fill=255)
    for x in (1.6, 3.4, 5.2, 8.0, 9.8, 11.6):
        d.rectangle([x * SS, 10.0 * SS, (x + 0.9) * SS, 12.2 * SS], fill=255)
    return im

def icon_clock():
    im, s = canvas()
    d = ImageDraw.Draw(im)
    pad = 1.0 * SS
    d.ellipse([pad, pad, s - pad, s - pad], outline=255, width=W(1.5))
    c = s / 2
    d.line([c, c, c, 3.6 * SS], fill=255, width=W(1.5))
    d.line([c, c, c + 3.0 * SS, c + 1.6 * SS], fill=255, width=W(1.5))
    return im

ICONS = [("fps", icon_fps), ("ft", icon_ft), ("gpu", icon_gpu), ("cpu", icon_cpu), ("ram", icon_ram), ("time", icon_clock)]

# RTSS draws sprites top-aligned to the text line, so each sprite is a full line tall with the
# icon offset to sit on the digit center. Cells keep a transparent gutter, and the atlas width
# stays a multiple of 16 (a 90px wide atlas rendered sliced icons in testing).
CW = 24
CH = 32

def build_atlas():
    assert ICON + 2 <= CW and LINE + 2 <= CH
    atlas = Image.new("RGBA", (CW * len(ICONS), CH), (0, 0, 0, 0))
    assert atlas.width % 16 == 0
    pos = {}
    for i, (key, fn) in enumerate(ICONS):
        mask = fn().resize((ICON, ICON), Image.LANCZOS)
        tile = Image.new("RGBA", (ICON, ICON), ACCENT + (0,))
        tile.putalpha(mask)
        x, y = i * CW + 1, 1
        atlas.alpha_composite(tile, (x, y + ICON_TOP))
        pos[key] = (x, y)
    # A running game keeps the first image it loaded for a given file name, so the name carries a
    # content hash. Any change to the icons then reaches games that are already running.
    global PNG
    buf = io.BytesIO()
    atlas.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()
    PNG = f"{NAME}_Icons_{hashlib.sha1(data).hexdigest()[:8]}.png"
    for old in OUT.glob(f"{NAME}_Icons*.png"):
        old.unlink()
    (OUT / PNG).write_bytes(data)
    big =atlas.resize((atlas.width * 8, atlas.height * 8), Image.NEAREST)
    bg = Image.new("RGBA", big.size, (11, 14, 20, 255))
    bg.alpha_composite(big)
    docs = OUT.parent / "docs"
    if docs.is_dir():
        bg.save(docs / "icons.png")
    return pos

def img(pos, key):
    x, y = pos[key]
    return f"<I={ICON},{LINE},{x},{y},{ICON},{LINE}>"

def dyn(ranges, src):
    """Dynamic color tag. ranges = [(color, min, max)], empty string for open ends."""
    body = ",".join(f"{c},{lo},{hi}" for c, lo, hi in ranges)
    return f"<C={body}({src},0)>"

def build_text(pos):
    unit = lambda u: f"<C={UNIT}><S=-75>{u}<S><C>"
    val = lambda v: f"<C={VALUE}>{v}<C>"
    gap = "  "
    deg = "°C"
    fps = dyn([(CRIT, "", FPS_CRIT), (WARN, FPS_CRIT, FPS_WARN), (VALUE, FPS_WARN, "")], "FR")
    ft = dyn([(VALUE, "", FT_WARN), (WARN, FT_WARN, FT_CRIT), (CRIT, FT_CRIT, "")], "FT")
    gpu_t = dyn([(VALUE, "", GPU_WARN), (WARN, GPU_WARN, GPU_CRIT), (CRIT, GPU_CRIT, "")], "%GPU temp%")
    cpu_t = dyn([(VALUE, "", CPU_WARN), (WARN, CPU_WARN, CPU_CRIT), (CRIT, CPU_CRIT, "")], "%CPU temp%")
    graph = f"<C={ACCENT_HEX}><G=Frametime,{GRAPH_W},{GRAPH_H},{GRAPH_M},0,{GRAPH_MAX_MS:g},{GRAPH_FLAGS}><C>"
    parts = [
        f"{img(pos, 'fps')} {fps}<FR><C> {unit('FPS')}",
        f"{img(pos, 'ft')} {ft}<FT><C> {unit('ms')} {graph}",
        f"{img(pos, 'gpu')} {gpu_t}%GPU temp%<C>{unit(deg)} {val('%GPU usage%')}{unit('%')} {val('%VRAM%')} {unit('GB')}",
        f"{img(pos, 'cpu')} {cpu_t}%CPU temp%<C>{unit(deg)} {val('%CPU usage%')}{unit('%')}",
        f"{img(pos, 'ram')} {val('%RAM%')} {unit('GB')}",
        f"{img(pos, 'time')} {val('<TIME=%I:%M>')} {unit('<TIME=%p>')}",
    ]
    return gap.join(parts)

# RTSS built-in sensors (HAL), so the bar works without MSI Afterburner running.
# Checked against Afterburner on this PC, readings matched within one sampling step.
SOURCES = [
    ("GPU temp", "°C", "", "", "GPU1 temperature"),
    ("GPU usage", "%", "", "", "GPU1 usage"),
    ("VRAM", "GB", "%.1f", "x/1024", "GPU1 memory usage"),
    ("CPU temp", "°C", "", "", "CPU temperature"),
    ("CPU usage", "%", "", "", "CPU usage"),
    ("RAM", "GB", "%.1f", "x/1024", "RAM usage"),
]

def build_ovl(text):
    L = [
        "[Master]", "Implementation=2", f"FontFace={FONT_FACE}", f"FontHeight=-{FONT_HEIGHT}",
        f"FontWeight={FONT_WEIGHT}", "ZoomRatio=1",
        "[Settings]", "Name=Kkthnx OSD Bar", "EnvVars=", "RefreshPeriod=1000", "LockUserSettings=1",
        f"EmbeddedImage={PNG}", "PingAddr=",
        "[General]", f"Sources={len(SOURCES)}", "Tables=0", "Layers=1",
    ]
    for i, (n, u, f, fx, hal) in enumerate(SOURCES):
        L += [f"[Source{i}]", f"Name={n}", f"Units={u}", f"Format={f}", f"Formula={fx}",
              "Provider=HAL", f"ID={hal}"]
    # A left margin shifts the centered bar sideways in RTSS. A negative right margin alone pads
    # both sides evenly and keeps it centered (measured). MarginBottom -1 balances top and bottom.
    L += ["[Layer0]", "Name=Bar", f"Text={text}", "PositionSticky=1", "ExtentX=-1", "ExtentY=-1",
          "ExtentOrigin=4", "FixedAlignment=1", f"BgndColor={PLATE}",
          "MarginLeft=0", "MarginTop=0", f"MarginRight={env('MR', -24)}", f"MarginBottom={env('MB', -1)}"]
    data = ("\r\n".join(L) + "\r\n").encode("cp1252")
    (OUT / f"{NAME}.ovl").write_bytes(data)
    return data

def build_ovx(files):
    """Uncompressed SZA0 container, same layout the editor's Import reads. First entry must be the OVL."""
    body = b""
    for name, data in files:
        s = name.encode("ascii") + b"\0"
        body += struct.pack("<II", len(data) + len(s), len(data)) + data + s
    total = 12 + len(body)
    blob = struct.pack("<III", 0x535A4130, total, len(files)) + body
    (OUT / f"{NAME}.ovx").write_bytes(blob)
    return blob

def parse_ovx(blob):
    sign, size, n = struct.unpack_from("<III", blob, 0)
    assert sign == 0x535A4130 and size == len(blob), (hex(sign), size, len(blob))
    off, out = 12, []
    for _ in range(n):
        esz, dsz = struct.unpack_from("<II", blob, off)
        data = blob[off + 8: off + 8 + dsz]
        name = blob[off + 8 + dsz: off + 8 + esz].rstrip(b"\0").decode()
        out.append((name, len(data)))
        off += 8 + esz
    assert off == len(blob)
    return out

pos = build_atlas()
text = build_text(pos)
ovl = build_ovl(text)
blob = build_ovx([(f"{NAME}.ovl", ovl), (PNG, (OUT / PNG).read_bytes())])
print("entries", parse_ovx(blob))
