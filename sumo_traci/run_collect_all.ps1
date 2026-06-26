param(
    [string]$BaseDir = $PSScriptRoot,
    [string]$CollectorScript = "collect_latency_throughput.py",
    [string]$RSUFile = "rsu_positions.json",
    [string]$ScenarioRoot = "scenarios",
    [string]$OutFile = "..\results\latency_throughput_raw_10runs.csv"
)

$ErrorActionPreference = "Stop"

$BaseDir = (Resolve-Path $BaseDir).Path
$CollectorPath = Join-Path $BaseDir $CollectorScript
$RSUPath = Join-Path $BaseDir $RSUFile
$ScenarioRootPath = Join-Path $BaseDir $ScenarioRoot
$OutPath = Join-Path $BaseDir $OutFile
$OutDir = Split-Path $OutPath -Parent

if (-not (Test-Path $CollectorPath)) {
    throw "Collector script not found: $CollectorPath"
}
if (-not (Test-Path $RSUPath)) {
    throw "RSU file not found: $RSUPath"
}
if (-not (Test-Path $ScenarioRootPath)) {
    throw "Scenario root not found: $ScenarioRootPath"
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# Remove the previous output file to avoid appending duplicate records.
if (Test-Path $OutPath) {
    Remove-Item $OutPath -Force
}

# Find all SUMO configuration files.
$cfgFiles = Get-ChildItem -Path $ScenarioRootPath -Recurse -Filter *.sumocfg |
    Sort-Object FullName

if ($cfgFiles.Count -eq 0) {
    throw "No .sumocfg files found under: $ScenarioRootPath"
}

Write-Host "Found $($cfgFiles.Count) scenario files."
Write-Host "Output CSV: $OutPath"
Write-Host ""

$failed = @()

foreach ($cfg in $cfgFiles) {
    Write-Host "Running: $($cfg.FullName)"

    try {
        python $CollectorPath `
            --cfg $cfg.FullName `
            --rsu $RSUPath `
            --out $OutPath

        if ($LASTEXITCODE -ne 0) {
            throw "collect_latency_throughput.py exited with code $LASTEXITCODE"
        }
    }
    catch {
        Write-Warning "FAILED: $($cfg.FullName)"
        $failed += $cfg.FullName
    }
}

Write-Host ""
Write-Host "Batch collection finished."
Write-Host "Raw output: $OutPath"

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "Failed scenarios:"
    $failed | ForEach-Object { Write-Host "  $_" }
}
else {
    Write-Host "All scenarios completed successfully."
}
