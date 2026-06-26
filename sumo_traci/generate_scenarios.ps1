param(
    [string]$BaseDir = $PSScriptRoot,
    [string]$NetFile = "chaoyang.net.xml",
    [string]$VTypeFile = "vtype.xml",
    [int[]]$VehicleCounts = @(100,200,300,400,500,600,700,800,900,1000),
    [int]$RunsPerCount = 10,
    [double]$BeginTime = 0,
    [double]$EndTime = 1000,
    [double]$StepLength = 1.0
)

$ErrorActionPreference = "Stop"

if (-not $env:SUMO_HOME) {
    throw "SUMO_HOME is not set. Please set SUMO_HOME first."
}

$RandomTrips = Join-Path $env:SUMO_HOME "tools\randomTrips.py"
if (-not (Test-Path $RandomTrips)) {
    throw "randomTrips.py not found: $RandomTrips"
}

$BaseDir = (Resolve-Path $BaseDir).Path
$NetPath = Join-Path $BaseDir $NetFile
$VTypePath = Join-Path $BaseDir $VTypeFile
$ScenarioRoot = Join-Path $BaseDir "scenarios"

if (-not (Test-Path $NetPath)) {
    throw "Net file not found: $NetPath"
}
if (-not (Test-Path $VTypePath)) {
    throw "Vehicle type file not found: $VTypePath"
}

New-Item -ItemType Directory -Force -Path $ScenarioRoot | Out-Null

foreach ($N in $VehicleCounts) {
    $CountDir = Join-Path $ScenarioRoot "$N"
    New-Item -ItemType Directory -Force -Path $CountDir | Out-Null

    $duration = $EndTime - $BeginTime
    $period = $duration / $N

    foreach ($run in 1..$RunsPerCount) {
        $RunDir = Join-Path $CountDir "run$run"
        New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

        $TripName  = "chaoyang_${N}_run${run}.trips.xml"
        $RouteName = "chaoyang_${N}_run${run}.rou.xml"
        $CfgName   = "chaoyang_${N}_run${run}.sumocfg"

        $TripPath  = Join-Path $RunDir $TripName
        $RoutePath = Join-Path $RunDir $RouteName
        $CfgPath   = Join-Path $RunDir $CfgName

        $seed = $N * 100 + $run

        Write-Host "Generating scenario: N=$N, run=$run, seed=$seed"

        foreach ($p in @($TripPath, $RoutePath, $CfgPath)) {
            if (Test-Path $p) {
                Remove-Item $p -Force
            }
        }

        python -X utf8 $RandomTrips `
            -n $NetPath `
            -o $TripPath `
            -r $RoutePath `
            --seed $seed `
            --begin $BeginTime `
            --end $EndTime `
            --period $period `
            --validate

        if (-not (Test-Path $RoutePath)) {
            throw "Failed to generate route file: $RoutePath"
        }

        $cfgText = @"
<configuration>
    <input>
        <net-file value="$NetPath"/>
        <route-files value="$RoutePath"/>
        <additional-files value="$VTypePath"/>
    </input>

    <time>
        <begin value="$BeginTime"/>
        <end value="$EndTime"/>
        <step-length value="$StepLength"/>
    </time>

    <processing>
        <time-to-teleport value="120"/>
    </processing>

    <report>
        <no-step-log value="true"/>
    </report>
</configuration>
"@

        $cfgText | Set-Content -Encoding UTF8 $CfgPath
    }
}

Write-Host ""
Write-Host "All scenarios generated successfully."
Write-Host "Output root: $ScenarioRoot"
