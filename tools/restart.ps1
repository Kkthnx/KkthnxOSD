param(
    [Parameter(Mandatory)][string]$Layout,
    [switch]$Preview
)
# Point the overlay editor at $Layout and restart RTSS so it reloads the layout.
# With -Preview, also open the desktop overlay host full screen on the primary monitor.
$ErrorActionPreference = "Stop"
$rtss = (Get-ItemProperty "HKLM:\SOFTWARE\WOW6432Node\Unwinder\RTSS").InstallDir
if (-not $rtss) { throw "RTSS install folder not found in the registry" }

$running = Get-Process RTSS -ErrorAction SilentlyContinue
if ($running) { $running | Stop-Process -Force; $running | Wait-Process -Timeout 10 }
Set-Content "$rtss\Plugins\Client\OverlayEditor.cfg" "[Settings]`r`nLayout=$Layout" -Encoding ascii
Start-Sleep -Milliseconds 500
Start-Process "$rtss\RTSS.exe" -WorkingDirectory $rtss
for ($i = 0; $i -lt 20 -and -not (Get-Process RTSS -ErrorAction SilentlyContinue); $i++) { Start-Sleep -Milliseconds 250 }
if (-not (Get-Process RTSS -ErrorAction SilentlyContinue)) { throw "RTSS did not start" }

# The host caches the embedded image, so it is always restarted rather than reused.
Get-Process DesktopOverlayHost64 -ErrorAction SilentlyContinue | Stop-Process -Force -PassThru |
    Wait-Process -Timeout 5 -ErrorAction SilentlyContinue
if (-not $Preview) { return }

Start-Sleep 2
Start-Process "$rtss\DesktopOverlayHost64.exe"
Start-Sleep 2
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System; using System.Runtime.InteropServices;
public static class OsdWin {
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
    [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int hh, bool r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
}
"@ -ErrorAction SilentlyContinue
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$h = (Get-Process DesktopOverlayHost64).MainWindowHandle
[OsdWin]::ShowWindow($h, 9) | Out-Null
[OsdWin]::MoveWindow($h, $screen.X, $screen.Y, $screen.Width, $screen.Height, $true) | Out-Null
[OsdWin]::SetForegroundWindow($h) | Out-Null
Start-Sleep 3
