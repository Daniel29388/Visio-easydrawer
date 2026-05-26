[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SpecPath,

    [string]$OutVsdx,

    [switch]$Visible
)

$ErrorActionPreference = 'Stop'

function Has-Prop { param($Obj, [string]$Name) return ($null -ne $Obj -and $Obj.PSObject.Properties.Name -contains $Name) }
function Get-Prop { param($Obj, [string]$Name, $Default) if (Has-Prop $Obj $Name) { return $Obj.$Name } return $Default }

function Color-Formula {
    param([string]$Color, [string]$Default = '#000000')
    if ([string]::IsNullOrWhiteSpace($Color)) { $Color = $Default }
    if ($Color -eq 'none') { return $null }
    if ($Color.StartsWith('#') -and $Color.Length -eq 7) {
        $r = [Convert]::ToInt32($Color.Substring(1, 2), 16)
        $g = [Convert]::ToInt32($Color.Substring(3, 2), 16)
        $b = [Convert]::ToInt32($Color.Substring(5, 2), 16)
        return "RGB($r,$g,$b)"
    }
    return $Color
}

function Set-CellFormula {
    param($Shape, [string]$Cell, [string]$Formula)
    try { $Shape.CellsU($Cell).FormulaU = $Formula } catch { }
}

function Set-ShapeStyle {
    param(
        $Shape,
        [string]$Fill = '#FFFFFF',
        [string]$Line = '#2B2B2B',
        [double]$LineWeight = 1.1,
        [string]$Font = 'Times New Roman',
        [double]$FontSize = 10,
        [bool]$Bold = $false,
        [bool]$Italic = $false,
        [double]$Rounding = 0.06,
        [bool]$Dashed = $false
    )

    $fillFormula = Color-Formula $Fill '#FFFFFF'
    if ($null -eq $fillFormula) {
        Set-CellFormula $Shape 'FillPattern' '0'
    } else {
        Set-CellFormula $Shape 'FillForegnd' $fillFormula
        Set-CellFormula $Shape 'FillPattern' '1'
    }

    $lineFormula = Color-Formula $Line '#2B2B2B'
    if ($null -eq $lineFormula) {
        Set-CellFormula $Shape 'LinePattern' '0'
    } else {
        Set-CellFormula $Shape 'LineColor' $lineFormula
        Set-CellFormula $Shape 'LineWeight' ("{0} pt" -f $LineWeight)
    }
    if ($Dashed) { Set-CellFormula $Shape 'LinePattern' '2' }

    Set-CellFormula $Shape 'Char.Font' ('FONT("{0}")' -f $Font.Replace('"', ''))
    Set-CellFormula $Shape 'Char.Size' ("{0} pt" -f $FontSize)
    Set-CellFormula $Shape 'Char.Style' ($(if ($Bold -and $Italic) { '17' } elseif ($Bold) { '1' } elseif ($Italic) { '16' } else { '0' }))
    Set-CellFormula $Shape 'Para.HorzAlign' '1'
    Set-CellFormula $Shape 'VerticalAlign' '1'
    Set-CellFormula $Shape 'TxtWidth' 'Width*0.92'
    Set-CellFormula $Shape 'LeftMargin' '0.03 in'
    Set-CellFormula $Shape 'RightMargin' '0.03 in'
    Set-CellFormula $Shape 'TopMargin' '0.02 in'
    Set-CellFormula $Shape 'BottomMargin' '0.02 in'
    Set-CellFormula $Shape 'Rounding' ("{0} in" -f $Rounding)
}

function New-TextShape {
    param($Page, $Item, $Defaults)
    $s = $Page.DrawRectangle($Item.x, $Item.y, $Item.x + $Item.w, $Item.y + $Item.h)
    $s.Text = [string](Get-Prop $Item 'text' '')
    Set-ShapeStyle $s `
        (Get-Prop $Item 'fill' 'none') `
        (Get-Prop $Item 'line' 'none') `
        0 `
        (Get-Prop $Item 'font' (Get-Prop $Defaults 'font' 'Times New Roman')) `
        (Get-Prop $Item 'fontSize' 10) `
        (Get-Prop $Item 'bold' $false) `
        (Get-Prop $Item 'italic' $false) `
        0
    if (Has-Prop $Item 'angle') { Set-CellFormula $s 'Angle' ("{0} deg" -f $Item.angle) }
    return $s
}

function New-NodeShape {
    param($Page, $Item, $Defaults)
    $type = (Get-Prop $Item 'type' 'roundedRect').ToString()
    if ($type -eq 'ellipse' -or $type -eq 'circle') {
        $s = $Page.DrawOval($Item.x, $Item.y, $Item.x + $Item.w, $Item.y + $Item.h)
    } else {
        $s = $Page.DrawRectangle($Item.x, $Item.y, $Item.x + $Item.w, $Item.y + $Item.h)
    }
    $s.Text = [string](Get-Prop $Item 'text' '')
    $rounding = if ($type -eq 'rect') { 0 } else { Get-Prop $Item 'rounding' 0.06 }
    Set-ShapeStyle $s `
        (Get-Prop $Item 'fill' '#FFFFFF') `
        (Get-Prop $Item 'line' (Get-Prop $Defaults 'line' '#3F73D1')) `
        (Get-Prop $Item 'lineWeight' 1.1) `
        (Get-Prop $Item 'font' (Get-Prop $Defaults 'font' 'Times New Roman')) `
        (Get-Prop $Item 'fontSize' 10) `
        (Get-Prop $Item 'bold' $false) `
        (Get-Prop $Item 'italic' $false) `
        $rounding `
        (Get-Prop $Item 'dashed' $false)
    if (Has-Prop $Item 'angle') { Set-CellFormula $s 'Angle' ("{0} deg" -f $Item.angle) }
    return $s
}

function New-ContainerShape {
    param($Page, $Item, $Defaults)
    $s = $Page.DrawRectangle($Item.x, $Item.y, $Item.x + $Item.w, $Item.y + $Item.h)
    $s.Text = ''
    Set-ShapeStyle $s 'none' (Get-Prop $Item 'line' '#000000') (Get-Prop $Item 'lineWeight' 1.25) (Get-Prop $Defaults 'font' 'Times New Roman') 10 $false $false (Get-Prop $Item 'rounding' 0.16) $true
    $s.SendToBack()

    $top = Get-Prop $Item 'topLabel' ''
    if ($top -ne '') {
        New-TextShape $Page ([pscustomobject]@{
            x = $Item.x + 0.25; y = $Item.y + $Item.h - 0.42; w = $Item.w - 0.5; h = 0.32
            text = $top; fontSize = (Get-Prop $Item 'titleSize' 13); bold = $true
        }) $Defaults | Out-Null
    }
    $bottom = Get-Prop $Item 'bottomLabel' ''
    if ($bottom -ne '') {
        New-TextShape $Page ([pscustomobject]@{
            x = $Item.x + 0.25; y = $Item.y + 0.03; w = $Item.w - 0.5; h = 0.30
            text = $bottom; fontSize = (Get-Prop $Item 'labelSize' 13); bold = $true; italic = $true
        }) $Defaults | Out-Null
    }
    return $s
}

function New-ConnectorShape {
    param($Page, $Item, $Defaults)
    $pts = Get-Prop $Item 'points' @()
    if ($pts.Count -lt 2) { return }
    $color = Color-Formula (Get-Prop $Item 'color' (Get-Prop $Defaults 'arrow' '#3F73D1')) '#3F73D1'
    $weight = Get-Prop $Item 'weight' 1.35
    $dashed = Get-Prop $Item 'dashed' $false
    $arrow = Get-Prop $Item 'arrow' 'end'
    for ($i = 0; $i -lt $pts.Count - 1; $i++) {
        $p1 = $pts[$i]
        $p2 = $pts[$i + 1]
        $line = $Page.DrawLine([double]$p1[0], [double]$p1[1], [double]$p2[0], [double]$p2[1])
        Set-CellFormula $line 'LineColor' $color
        Set-CellFormula $line 'LineWeight' ("{0} pt" -f $weight)
        Set-CellFormula $line 'BeginArrow' '0'
        Set-CellFormula $line 'EndArrow' ($(if ($i -eq $pts.Count - 2 -and $arrow -ne 'none') { '13' } else { '0' }))
        if ($dashed) { Set-CellFormula $line 'LinePattern' '2' }
    }
}

$resolvedSpec = Resolve-Path -LiteralPath $SpecPath
$spec = Get-Content -LiteralPath $resolvedSpec -Raw | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($OutVsdx)) {
    $OutVsdx = [IO.Path]::ChangeExtension($resolvedSpec.Path, '.vsdx')
}
$OutVsdx = [IO.Path]::GetFullPath($OutVsdx)

$visio = New-Object -ComObject Visio.Application
$visio.Visible = [bool]$Visible
$visio.AlertResponse = 0
$doc = $visio.Documents.Add('')
$page = $visio.ActivePage

$pageWidth = Get-Prop $spec.page 'width' 15
$pageHeight = Get-Prop $spec.page 'height' 8.5
Set-CellFormula $page.PageSheet 'PageWidth' ("{0} in" -f $pageWidth)
Set-CellFormula $page.PageSheet 'PageHeight' ("{0} in" -f $pageHeight)
Set-CellFormula $page.PageSheet 'DrawingScale' '1 in'
Set-CellFormula $page.PageSheet 'PageScale' '1 in'

$defaults = Get-Prop $spec 'style' ([pscustomobject]@{})
foreach ($item in (Get-Prop $spec 'containers' @())) { New-ContainerShape $page $item $defaults | Out-Null }
foreach ($item in (Get-Prop $spec 'connectors' @())) { New-ConnectorShape $page $item $defaults }
foreach ($item in (Get-Prop $spec 'shapes' @())) {
    $type = (Get-Prop $item 'type' 'roundedRect').ToString()
    if ($type -eq 'label') { New-TextShape $page $item $defaults | Out-Null } else { New-NodeShape $page $item $defaults | Out-Null }
}
foreach ($item in (Get-Prop $spec 'labels' @())) { New-TextShape $page $item $defaults | Out-Null }

if (Test-Path -LiteralPath $OutVsdx) { Remove-Item -LiteralPath $OutVsdx -Force }
$doc.SaveAs($OutVsdx) | Out-Null
$doc.Close() | Out-Null
$visio.Quit() | Out-Null

[System.Runtime.InteropServices.Marshal]::ReleaseComObject($page) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($visio) | Out-Null
Write-Host "Saved: $OutVsdx"
