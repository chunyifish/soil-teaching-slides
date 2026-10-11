param(
  [Parameter(Mandatory = $true)][string]$PptxPath,
  [Parameter(Mandatory = $true)][string]$OutputDirectory,
  [switch]$TestEditability
)

$ErrorActionPreference = 'Stop'
$pptx = (Resolve-Path -LiteralPath $PptxPath).Path
$outDir = [System.IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $outDir) {
  if ((Get-ChildItem -LiteralPath $outDir -Force | Measure-Object).Count -gt 0) {
    throw "Output directory must be empty: $outDir"
  }
} else {
  New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$app = $null
$pres = $null
$editableCopy = $null
$copyPath = Join-Path $outDir 'b-mode-editable-smoke-copy.pptx'
$results = [ordered]@{}
try {
  $app = New-Object -ComObject PowerPoint.Application
  # PowerPoint rejects Visible=false through its automation API.
  $app.Visible = -1
  $app.DisplayAlerts = 2

  $pres = $app.Presentations.Open($pptx, $true, $false, $true)
  $slideCount = $pres.Slides.Count
  $pngCount = 0
  for ($index = 1; $index -le $slideCount; $index++) {
    $pngPath = Join-Path $outDir ('slide-' + $index.ToString('00') + '.png')
    $pres.Slides.Item($index).Export($pngPath, 'PNG', 1600, 900)
    $pngCount++
  }
  $results.openedReadOnly = ($pres.ReadOnly -eq -1)
  $results.slideCount = $slideCount
  $results.renderedPngCount = $pngCount
  $results.pngDirectory = $outDir
  $pres.Close()
  [void][Runtime.InteropServices.Marshal]::ReleaseComObject($pres)
  $pres = $null

  if ($TestEditability) {
    Copy-Item -LiteralPath $pptx -Destination $copyPath
    $editableCopy = $app.Presentations.Open($copyPath, $false, $false, $true)
    $target = $null
    foreach ($shape in $editableCopy.Slides.Item(3).Shapes) {
      if ($shape.Name -eq 'formula-fraction-part-1' -and $shape.HasTextFrame -eq -1) {
        $target = $shape
        break
      }
    }
    if ($null -eq $target) {
      throw 'Editable formula test target formula-fraction-part-1 was not found on slide 3.'
    }
    $originalText = $target.TextFrame.TextRange.Text
    $target.TextFrame.TextRange.Text = 'x'
    $editable = ($target.TextFrame.TextRange.Text -eq 'x')
    $target.TextFrame.TextRange.Text = $originalText
    if (-not $editable) {
      throw 'PowerPoint could not edit and read back a native formula text object.'
    }
    $editableCopy.Saved = $true
    $editableCopy.Close()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($editableCopy)
    $editableCopy = $null
    $results.formulaTextEditSmokeTest = 'PASS; scratch copy only; no changes saved'
    $resolvedCopy = [System.IO.Path]::GetFullPath($copyPath)
    if (-not $resolvedCopy.StartsWith($outDir.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
      throw "Scratch copy escaped the output directory: $resolvedCopy"
    }
    Remove-Item -LiteralPath $resolvedCopy -Force
  }

  $results.powerPointVersion = $app.Version
  $results.status = 'PASS'
  $results | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $outDir 'powerpoint-smoke-report.json') -Encoding utf8
  $results | ConvertTo-Json -Depth 4
} finally {
  if ($editableCopy) {
    $editableCopy.Saved = $true
    $editableCopy.Close()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($editableCopy)
  }
  if ($pres) {
    $pres.Close()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($pres)
  }
  if ($app) {
    $app.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)
  }
}
