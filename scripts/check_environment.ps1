[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$result = [ordered]@{
    powershell = $PSVersionTable.PSVersion.ToString()
    python = $null
    pillow = $false
    pyyaml = $false
    visioExe = $null
    visioComRegistered = $false
    visioComLaunch = $false
}

try {
    $result.python = (& python --version 2>&1).ToString()
    $mods = (& python -c "import importlib.util as u; print('PIL', bool(u.find_spec('PIL'))); print('yaml', bool(u.find_spec('yaml')))" 2>&1)
    foreach ($line in $mods) {
        if ($line -match '^PIL\s+True') { $result.pillow = $true }
        if ($line -match '^yaml\s+True') { $result.pyyaml = $true }
    }
} catch { }

$cmd = Get-Command VISIO.EXE -ErrorAction SilentlyContinue
if ($cmd) { $result.visioExe = $cmd.Source }

$clsid = Get-ItemProperty HKLM:\Software\Classes\Visio.Application\CLSID -ErrorAction SilentlyContinue
if ($clsid) { $result.visioComRegistered = $true }

try {
    $visio = New-Object -ComObject Visio.Application
    $visio.Visible = $false
    $result.visioComLaunch = $true
    $visio.Quit() | Out-Null
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($visio) | Out-Null
} catch { }

$result | ConvertTo-Json -Depth 3
