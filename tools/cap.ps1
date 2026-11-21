# Capture a screen region, saving a nearest-neighbor enlarged copy and a 1x copy for the measure scripts.
param([string]$Out, [int]$X = 1000, [int]$Y = 0, [int]$W = 600, [int]$H = 30, [int]$Scale = 4)
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap $W, $H
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($X, $Y, 0, 0, $bmp.Size)
$big = New-Object System.Drawing.Bitmap ($W * $Scale), ($H * $Scale)
$g2 = [System.Drawing.Graphics]::FromImage($big)
$g2.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
$g2.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
$g2.DrawImage($bmp, 0, 0, $W * $Scale, $H * $Scale)
$big.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Save($Out.Replace('.png', '_1x.png'), [System.Drawing.Imaging.ImageFormat]::Png)
foreach ($o in $g, $g2, $bmp, $big) { $o.Dispose() }
