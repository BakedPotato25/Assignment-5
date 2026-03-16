param(
    [switch]$EnsureUp = $true,
    [int]$WaitSeconds = 8
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[PHASE5][FAULT] $Message"
}

function Wait-ForService {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [int]$Seconds = 8
    )
    Write-Step "Waiting $Seconds seconds for $Name ..."
    Start-Sleep -Seconds $Seconds
}

function Invoke-OrderCase {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][hashtable]$Payload
    )

    $uri = "http://localhost:8007/orders/"
    $json = $Payload | ConvertTo-Json -Depth 8 -Compress

    $tmpBody = [System.IO.Path]::GetTempFileName()
    $tmpPayload = [System.IO.Path]::GetTempFileName()
    try {
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($tmpPayload, $json, $utf8NoBom)

        $statusRaw = & curl.exe -s -o $tmpBody -w "%{http_code}" --max-time 120 -H "Content-Type: application/json" --data-binary "@$tmpPayload" $uri
        $statusCode = 0
        [void][int]::TryParse((($statusRaw -join "").Trim()), [ref]$statusCode)
        $content = Get-Content -Path $tmpBody -Raw
        $bodyObj = $null
        if ($content) {
            try {
                $bodyObj = $content | ConvertFrom-Json
            }
            catch {
                $bodyObj = [pscustomobject]@{ raw = $content }
            }
        }

        $orderId = $null
        if ($bodyObj) {
            if ($bodyObj.PSObject.Properties.Name -contains "id") {
                $orderId = $bodyObj.id
            }
            elseif ($bodyObj.PSObject.Properties.Name -contains "order_id") {
                $orderId = $bodyObj.order_id
            }
        }

        $orderStatus = $null
        if ($bodyObj -and ($bodyObj.PSObject.Properties.Name -contains "status")) {
            $orderStatus = $bodyObj.status
        }

        return [pscustomobject]@{
            case_name = $Name
            http_status = $statusCode
            ok = ($statusCode -ge 200 -and $statusCode -lt 300)
            order_id = $orderId
            order_status = $orderStatus
            response = $bodyObj
        }
    }
    finally {
        if (Test-Path $tmpBody) {
            Remove-Item -Path $tmpBody -Force
        }
        if (Test-Path $tmpPayload) {
            Remove-Item -Path $tmpPayload -Force
        }
    }
}

Write-Step "Starting Phase 5 fault simulations"

if ($EnsureUp) {
    Write-Step "Ensuring required containers are up"
    docker compose up -d order-service pay-service ship-service rabbitmq | Out-Host
    Wait-ForService -Name "core services" -Seconds $WaitSeconds
}

$basePayload = @{
    customer_id = 1
    total_amount = "199000"
    payment_method = "COD"
    shipping_method = "Standard"
    shipping_address = "Phase5 Test Address"
    items = @(
        @{ book_id = 1; quantity = 1 },
        @{ book_id = 2; quantity = 1 }
    )
}

$results = @()

Write-Step "Case 1 - Simulate pay-service unavailable"
docker compose stop pay-service | Out-Host
Wait-ForService -Name "pay-service stop" -Seconds 3
$results += Invoke-OrderCase -Name "pay_service_down" -Payload $basePayload
docker compose start pay-service | Out-Host
Wait-ForService -Name "pay-service start" -Seconds $WaitSeconds

Write-Step "Case 2 - Simulate ship-service unavailable"
docker compose stop ship-service | Out-Host
Wait-ForService -Name "ship-service stop" -Seconds 3
$results += Invoke-OrderCase -Name "ship_service_down" -Payload $basePayload
docker compose start ship-service | Out-Host
Wait-ForService -Name "ship-service start" -Seconds $WaitSeconds

Write-Step "Case 3 - Simulate RabbitMQ unavailable"
docker compose stop rabbitmq | Out-Host
Wait-ForService -Name "rabbitmq stop" -Seconds 3
$results += Invoke-OrderCase -Name "rabbitmq_down" -Payload $basePayload
docker compose start rabbitmq | Out-Host
Wait-ForService -Name "rabbitmq start" -Seconds $WaitSeconds

Write-Step "Collecting order-service event publish failure logs"
$publishFailLogs = docker compose logs --tail=200 order-service | Select-String "EVENT_PUBLISH_FAILED" | ForEach-Object { $_.Line }

$summary = [pscustomobject]@{
    generated_at = (Get-Date).ToString("s")
    cases = $results
    event_publish_failed_log_count = @($publishFailLogs).Count
    event_publish_failed_logs = $publishFailLogs
}

$outDir = Join-Path $PSScriptRoot "artifacts"
if (-not (Test-Path $outDir)) {
    New-Item -Path $outDir -ItemType Directory | Out-Null
}
$outFile = Join-Path $outDir ("fault-summary-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json")
$summary | ConvertTo-Json -Depth 8 | Set-Content -Path $outFile -Encoding UTF8

Write-Step "Done. Summary saved to: $outFile"
$summary | ConvertTo-Json -Depth 8
