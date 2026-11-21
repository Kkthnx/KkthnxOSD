param([switch]$Preview)
# Build the layout into ..\layout, install it into the RTSS overlays folder and reload RTSS with it.
# Needs an elevated shell, since RTSS lives under Program Files.
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Join-Path (Split-Path -Parent $here) "layout"
$rtss = (Get-ItemProperty "HKLM:\SOFTWARE\WOW6432Node\Unwinder\RTSS").InstallDir
if (-not $rtss) { throw "RTSS install folder not found in the registry" }
$overlays = "$rtss\Plugins\Client\Overlays"

python -I "$here\build_osd.py" $out
if ($LASTEXITCODE) { throw "build failed" }

$png = Get-ChildItem "$out\Kkthnx_OSD_Bar_Icons_*.png" | Select-Object -First 1
if (-not $png) { throw "icon atlas missing" }
# Remove only this bar's older atlases, then install the current files.
Get-ChildItem "$overlays\Kkthnx_OSD_Bar_Icons*.png" | Where-Object Name -ne $png.Name | Remove-Item
Copy-Item $png.FullName, "$out\Kkthnx_OSD_Bar.ovl" $overlays -Force

& "$here\restart.ps1" -Layout "$overlays\Kkthnx_OSD_Bar.ovl" -Preview:$Preview
