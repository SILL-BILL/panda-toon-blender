# SPDX-License-Identifier: GPL-3.0-or-later
# Review and explicit Blender execution approval required before use.
param(
    [Parameter(Mandatory=$true)][guid]$RunId,
    [Parameter(Mandatory=$true)][ValidateSet('5.1.1','5.2.3')][string]$ExpectedVersion,
    [Parameter(Mandatory=$true)]
    [ValidateSet('prepare','structure','first','remaining','save','install','restart','gui','gui-retry','softness','softness-gui')]
    [string]$Stage
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$run = Join-Path $root ('lab\temp\migration-' + $RunId.ToString('N'))
$stages = @('prepare','structure','first','remaining','save','install','restart','gui')
$paths = @('BLENDER_USER_RESOURCES','BLENDER_USER_CONFIG','BLENDER_USER_EXTENSIONS',
    'BLENDER_USER_SCRIPTS','BLENDER_USER_DATAFILES','TEMP','TMP','APPDATA','LOCALAPPDATA',
    'MESA_SHADER_CACHE_DIR','__GL_SHADER_DISK_CACHE_PATH')
$flags = @('PYTHONDONTWRITEBYTECODE','PYTHONNOUSERSITE')
$series = if ($ExpectedVersion -eq '5.2.3') { '5.2' } else { '5.1' }
$blender = "C:\Program Files\Blender Foundation\Blender $series\blender.exe"

function Assert-PlainPath([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        if ((Get-Item -LiteralPath $Path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Reparse point rejected: $Path"
        }
    }
}

Assert-PlainPath $root
Assert-PlainPath (Join-Path $root 'lab')
Assert-PlainPath (Join-Path $root 'lab\temp')
Assert-PlainPath $run
if ($Stage -eq 'prepare') {
    if (Test-Path -LiteralPath $run) { throw 'Use a fresh UUID.' }
    New-Item -ItemType Directory -Path $run | Out-Null
    foreach ($dir in (@('scenes','renders','logs') + ($paths | ForEach-Object { "env\$_" }))) {
        New-Item -ItemType Directory -Path (Join-Path $run $dir) | Out-Null
    }
    & python -I -B (Join-Path $root 'tools\build_extension.py') --output (Join-Path $run 'panda_toon.zip')
    if ($LASTEXITCODE -ne 0) { throw 'ZIP build failed.' }
    [IO.File]::WriteAllText((Join-Path $run 'logs\prepare.ok'), $ExpectedVersion)
    return
}

foreach ($item in Get-ChildItem -LiteralPath $run -Force -Recurse) {
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw "Reparse point rejected: $($item.FullName)"
    }
}
if ((Get-Content -LiteralPath (Join-Path $run 'logs\prepare.ok') -Raw) -ne $ExpectedVersion) {
    throw 'Version differs from preparation.'
}
$previousStage = $stages[[array]::IndexOf($stages, $Stage) - 1]
if ($Stage -eq 'gui-retry') { $previousStage = 'restart' }
if ($Stage -eq 'softness') { $previousStage = 'structure' }
if ($Stage -eq 'softness-gui') { $previousStage = 'softness' }
if ($Stage -like 'softness*' -and $ExpectedVersion -ne '5.2.3') { throw 'Softness review requires Blender 5.2.3.' }
if (-not (Test-Path -LiteralPath (Join-Path $run "logs\$previousStage.ok") -PathType Leaf)) {
    throw "Previous stage has not passed: $previousStage"
}
$log = Join-Path $run "logs\$Stage.log"
$result = Join-Path $run "logs\$Stage.json"
$complete = Join-Path $run "logs\$Stage.ok"
foreach ($file in @($log,$result,$complete)) {
    if (Test-Path -LiteralPath $file) { throw "Output already exists: $file" }
}
$gui = $Stage -in @('gui','gui-retry','softness-gui')
$entry = if ($Stage -in @('gui','gui-retry','install','restart')) { 'verify_install.py' } else { 'phase1a.py' }
$arguments = @('--offline-mode','--disable-autoexec')
if (-not $gui) { $arguments += '--background' }
if ($Stage -notin @('gui','gui-retry','restart')) { $arguments += '--factory-startup' }
$arguments += @('--python-exit-code','1','--python',(Join-Path $root "tests\blender\$entry"),'--',$run,$Stage,$ExpectedVersion)
if ($Stage -eq 'softness-gui') {
    [IO.File]::Copy((Join-Path $run 'scenes\softness.blend'),
        (Join-Path $run 'scenes\softness-review.blend'), $false)
} elseif ($gui) {
    $sceneName = if ($Stage -eq 'gui-retry') { 'gui-review-retry.blend' } else { 'gui-review.blend' }
    $copy = Join-Path $run "scenes\$sceneName"
    [IO.File]::Copy((Join-Path $run 'scenes\phase1a.blend'), $copy, $false)
}
$previous = @{}
foreach ($key in ($paths + $flags)) {
    $previous[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
}
try {
    foreach ($key in $paths) {
        [Environment]::SetEnvironmentVariable($key, (Join-Path $run "env\$key"), 'Process')
    }
    foreach ($key in $flags) { [Environment]::SetEnvironmentVariable($key, '1', 'Process') }
    Push-Location $run
    try {
        & $blender @arguments 2>&1 | Tee-Object -FilePath $log
        if ($LASTEXITCODE -ne 0) { throw "Blender failed: $LASTEXITCODE" }
        if (-not (Test-Path -LiteralPath $result -PathType Leaf)) { throw 'No Python success report.' }
        if (Select-String -LiteralPath $log -Quiet -Pattern 'Traceback|Package was expected to be installed but not found|\.thumbnails') {
            throw 'Unexpected Blender diagnostics. Inspect the log before continuing.'
        }
        New-Item -ItemType File -Path $complete | Out-Null
    } finally { Pop-Location }
} finally {
    foreach ($key in ($paths + $flags)) {
        [Environment]::SetEnvironmentVariable($key, $previous[$key], 'Process')
    }
}
