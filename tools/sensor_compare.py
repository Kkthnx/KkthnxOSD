"""Write a temporary layout that shows Afterburner and built-in (HAL) readings side by side."""
import sys
from pathlib import Path

out = Path(sys.argv[1])
pairs = [
    ("GPU temp", "GPU1 temperature", "00000000", "00000000", "", ""),
    ("GPU use", "GPU1 usage", "00000030", "00000000", "", ""),
    ("VRAM", "GPU1 memory usage", "00000031", "00000000", "%.1f", "x/1024"),
    ("CPU temp", "CPU temperature", "00000080", "FFFFFFFF", "", ""),
    ("CPU use", "CPU usage", "00000090", "FFFFFFFF", "", ""),
    ("RAM", "RAM usage", "00000091", "00000000", "%.1f", "x/1024"),
]
L = ["[Master]", "Implementation=2", "FontFace=Consolas", "FontHeight=-14", "FontWeight=700", "ZoomRatio=1",
     "[Settings]", "Name=compare", "RefreshPeriod=1000", "LockUserSettings=1", "EmbeddedImage=", "PingAddr=",
     "[General]", f"Sources={len(pairs) * 2}", "Tables=0", "Layers=1"]
i = 0
parts = []
for label, hal_id, sid, gpu, fmt, fx in pairs:
    L += [f"[Source{i}]", f"Name=AB {label}", "Units=", f"Format={fmt}", f"Formula={fx}",
          "Provider=MSI Afterburner", f"SrcId={sid}", f"Gpu={gpu}", "SrcName="]
    i += 1
    L += [f"[Source{i}]", f"Name=HAL {label}", "Units=", f"Format={fmt}", f"Formula={fx}",
          "Provider=HAL", f"ID={hal_id}"]
    i += 1
    parts.append(f"{label} AB=%AB {label}% HAL=%HAL {label}%")
L += ["[Layer0]", "Name=cmp", "Text=" + " | ".join(parts), "PositionSticky=1", "ExtentX=-1", "ExtentY=-1",
      "ExtentOrigin=4", "FixedAlignment=1", "BgndColor=FF000000", "TextColor=FFFFFF"]
out.write_bytes(("\r\n".join(L) + "\r\n").encode("cp1252"))
