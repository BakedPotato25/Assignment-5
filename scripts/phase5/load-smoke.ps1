param(
    [int]$TotalRequests = 120,
    [string]$TargetUrl = "http://localhost:8000/books/"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[PHASE5][LOAD] $Message"
}

Write-Step "Starting load smoke: $TotalRequests requests to $TargetUrl"

$latencies = New-Object System.Collections.Generic.List[double]
$statusMap = @{}
$errors = 0

for ($i = 1; $i -le $TotalRequests; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $tmpBody = [System.IO.Path]::GetTempFileName()
    try {
        $statusRaw = & curl.exe -s -o $tmpBody -w "%{http_code}" --max-time 15 -L $TargetUrl
        $sw.Stop()
        $latencies.Add($sw.Elapsed.TotalMilliseconds)

        $statusCode = "ERR"
        if ($statusRaw) {
            $parsed = 0
            if ([int]::TryParse(($statusRaw -join ""), [ref]$parsed)) {
                $statusCode = [string]$parsed
            }
        }
        if (-not $statusMap.ContainsKey($statusCode)) {
            $statusMap[$statusCode] = 0
        }
        $statusMap[$statusCode] += 1
        if ($statusCode -eq "ERR" -or [int]$statusCode -ge 400) {
            $errors += 1
        }
    }
    finally {
        if (Test-Path $tmpBody) {
            Remove-Item -Path $tmpBody -Force
        }
    }
}

$orderedStatus = $statusMap.GetEnumerator() | Sort-Object Name | ForEach-Object {
    [pscustomobject]@{
        status = $_.Name
        count = $_.Value
    }
}

$avgMs = [math]::Round((($latencies | Measure-Object -Average).Average), 2)
$minMs = [math]::Round((($latencies | Measure-Object -Minimum).Minimum), 2)
$maxMs = [math]::Round((($latencies | Measure-Object -Maximum).Maximum), 2)

$summary = [pscustomobject]@{
    generated_at = (Get-Date).ToString("s")
    target_url = $TargetUrl
    total_requests = $TotalRequests
    error_count = $errors
    latency_ms = [pscustomobject]@{
        avg = $avgMs
        min = $minMs
        max = $maxMs
    }
    statuses = $orderedStatus
}

$outDir = Join-Path $PSScriptRoot "artifacts"
if (-not (Test-Path $outDir)) {
    New-Item -Path $outDir -ItemType Directory | Out-Null
}
$outFile = Join-Path $outDir ("load-summary-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json")
$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $outFile -Encoding UTF8

Write-Step "Done. Summary saved to: $outFile"
$summary | ConvertTo-Json -Depth 6
