# APPROVAL REQUIRED. Does not install or enable extensions in user preferences.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runId = 'phase1a-' + [guid]::NewGuid().ToString('N')
$sandboxDir = Join-Path $projectRoot "lab\temp\$runId"
New-Item -ItemType Directory -Path $sandboxDir | Out-Null
$envNames = @('BLENDER_USER_RESOURCES', 'BLENDER_USER_CONFIG', 'BLENDER_USER_SCRIPTS', 'BLENDER_USER_EXTENSIONS', 'BLENDER_USER_DATAFILES', 'TEMP', 'TMP', 'PYTHONDONTWRITEBYTECODE')
$previous = @{}
try {
    foreach ($key in $envNames) {
        $previous[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
        $value = if ($key -eq 'PYTHONDONTWRITEBYTECODE') { '1' } else { Join-Path $sandboxDir $key }
        if ($key -ne 'PYTHONDONTWRITEBYTECODE') { New-Item -ItemType Directory -Path $value | Out-Null }
        [Environment]::SetEnvironmentVariable($key, $value, 'Process')
    }
    & 'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python (Join-Path $projectRoot 'tests\blender\phase1a.py') -- $runId
    if ($LASTEXITCODE -ne 0) { throw "Blender tests failed: $LASTEXITCODE" }
} finally {
    foreach ($key in $envNames) { [Environment]::SetEnvironmentVariable($key, $previous[$key], 'Process') }
}
