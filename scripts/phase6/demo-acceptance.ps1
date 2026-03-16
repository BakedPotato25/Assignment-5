param(
    [switch]$Build = $true,
    [int]$WaitSeconds = 20
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[PHASE6][ACCEPTANCE] $Message"
}

function Invoke-Compose {
    param([Parameter(Mandatory = $true)][string[]]$Args)

    & docker compose @Args | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($Args -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Invoke-ManagePy {
    param(
        [Parameter(Mandatory = $true)][string]$Service,
        [Parameter(Mandatory = $true)][string[]]$Args
    )

    & docker compose exec -T $Service python manage.py @Args | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "manage.py $($Args -join ' ') failed for $Service with exit code $LASTEXITCODE"
    }
}

function Wait-For {
    param([Parameter(Mandatory = $true)][string]$Name, [int]$Seconds = 8)
    Write-Step "Waiting $Seconds seconds for $Name"
    Start-Sleep -Seconds $Seconds
}

function Parse-CsrfToken {
    param([Parameter(Mandatory = $true)][string]$Html)

    $pattern = 'name="csrfmiddlewaretoken"\s+value="([^"]+)"'
    $match = [System.Text.RegularExpressions.Regex]::Match($Html, $pattern)
    if (-not $match.Success) {
        throw "Cannot find csrfmiddlewaretoken in HTML form."
    }
    return $match.Groups[1].Value
}

function Get-PropertyValue {
    param(
        [object]$Object,
        [Parameter(Mandatory = $true)][string]$Name,
        $Default = $null
    )

    if ($null -eq $Object) {
        return $Default
    }
    if ($Object.PSObject -and ($Object.PSObject.Properties.Name -contains $Name)) {
        return $Object.$Name
    }
    return $Default
}

function Invoke-JsonRequest {
    param(
        [Parameter(Mandatory = $true)][ValidateSet("GET", "POST")][string]$Method,
        [Parameter(Mandatory = $true)][string]$Uri,
        [object]$Body = $null,
        [int]$TimeoutSec = 30
    )

    $tmpBody = [System.IO.Path]::GetTempFileName()
    $tmpPayload = $null

    try {
        $args = @(
            "-s",
            "-o", $tmpBody,
            "-w", "%{http_code}",
            "--max-time", "$TimeoutSec",
            "-X", $Method,
            "-H", "Content-Type: application/json"
        )

        if ($null -ne $Body) {
            $tmpPayload = [System.IO.Path]::GetTempFileName()
            $json = $Body | ConvertTo-Json -Depth 10 -Compress
            $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
            [System.IO.File]::WriteAllText($tmpPayload, $json, $utf8NoBom)
            $args += @("--data-binary", "@$tmpPayload")
        }

        $args += $Uri
        $statusRaw = & curl.exe @args

        $statusCode = 0
        [void][int]::TryParse((($statusRaw -join "").Trim()), [ref]$statusCode)

        $raw = ""
        if (Test-Path $tmpBody) {
            $raw = Get-Content -Path $tmpBody -Raw
        }

        $obj = $null
        if ($raw) {
            try {
                $obj = $raw | ConvertFrom-Json
            }
            catch {
                $obj = [pscustomobject]@{ raw = $raw }
            }
        }

        return [pscustomobject]@{
            uri = $Uri
            status_code = $statusCode
            ok = ($statusCode -ge 200 -and $statusCode -lt 300)
            body = $obj
            raw = $raw
        }
    }
    finally {
        if ($tmpPayload -and (Test-Path $tmpPayload)) {
            Remove-Item -Path $tmpPayload -Force
        }
        if (Test-Path $tmpBody) {
            Remove-Item -Path $tmpBody -Force
        }
    }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Push-Location $repoRoot

try {
    Write-Step "Starting Assignment 06 acceptance demo"

    if ($Build) {
        Write-Step "Bringing up full stack from clean build"
        Invoke-Compose -Args @("up", "-d", "--build")
    }
    else {
        Write-Step "Bringing up stack without build"
        Invoke-Compose -Args @("up", "-d")
    }

    Wait-For -Name "services to warm up" -Seconds $WaitSeconds

    Write-Step "Applying migrations for clean environment"
    $migrationServices = @(
        "api-gateway",
        "auth-service",
        "book-service",
        "customer-service",
        "cart-service",
        "order-service",
        "pay-service",
        "ship-service"
    )
    foreach ($svc in $migrationServices) {
        Invoke-ManagePy -Service $svc -Args @("migrate")
    }

    Write-Step "Seeding baseline data (books)"
    try {
        Invoke-ManagePy -Service "book-service" -Args @("seed_books")
    }
    catch {
        Write-Step "seed_books failed. Attempting fallback migration bootstrap for book-service"
        try {
            Invoke-ManagePy -Service "book-service" -Args @("makemigrations", "app")
            Invoke-ManagePy -Service "book-service" -Args @("migrate")
            Invoke-ManagePy -Service "book-service" -Args @("seed_books")
            Write-Step "seed_books recovered after fallback migration"
        }
        catch {
            Write-Step "seed_books skipped: $($_.Exception.Message)"
        }
    }

    $summary = [ordered]@{
        generated_at = (Get-Date).ToString("s")
        criteria = [ordered]@{
            jwt_login_and_protected_api = $false
            saga_transition_and_compensation = $false
            rabbitmq_event_flow_observable = $false
            health_and_metrics_reachable = $false
            demo_reproducible_from_clean_build = $Build.IsPresent
        }
        evidence = [ordered]@{}
        done = $false
    }

    # 1) JWT login + protected API
    Write-Step "Checking JWT login and protected API"
    $username = "phase6_" + (Get-Date -Format "MMddHHmmss")
    $email = "$username@example.com"
    $password = "Phase6Pass!123"

    $registerPage = Invoke-WebRequest -Uri "http://localhost:8000/register/" -SessionVariable gwSession -MaximumRedirection 5 -TimeoutSec 20 -UseBasicParsing
    $csrf = Parse-CsrfToken -Html $registerPage.Content

    $registerForm = @{
        csrfmiddlewaretoken = $csrf
        username = $username
        email = $email
        password = $password
    }

    [void](Invoke-WebRequest -Uri "http://localhost:8000/register/" -Method Post -Body $registerForm -WebSession $gwSession -MaximumRedirection 5 -Headers @{ Referer = "http://localhost:8000/register/" } -TimeoutSec 30 -UseBasicParsing)

    $cartResp = Invoke-WebRequest -Uri "http://localhost:8000/cart/" -WebSession $gwSession -MaximumRedirection 3 -TimeoutSec 20 -UseBasicParsing
    $cartProtectedOk = ($cartResp.StatusCode -eq 200)

    $authLoginResp = Invoke-JsonRequest -Method "POST" -Uri "http://localhost:8012/auth/login/" -Body @{ username = $username; password = $password } -TimeoutSec 20
    $tokenValid = $false
    if ($authLoginResp.ok -and $authLoginResp.body -and ($authLoginResp.body.PSObject.Properties.Name -contains "access_token")) {
        $validateResp = Invoke-JsonRequest -Method "POST" -Uri "http://localhost:8012/auth/validate/" -Body @{ token = $authLoginResp.body.access_token } -TimeoutSec 20
        if ($validateResp.ok -and $validateResp.body -and ($validateResp.body.PSObject.Properties.Name -contains "valid")) {
            $tokenValid = [bool]$validateResp.body.valid
        }
    }

    $summary.criteria.jwt_login_and_protected_api = ($cartProtectedOk -and $tokenValid)
    $summary.evidence.jwt = [ordered]@{
        username = $username
        cart_status = $cartResp.StatusCode
        auth_login_status = $authLoginResp.status_code
        token_valid = $tokenValid
    }

    # 2) Saga transitions + compensation
    Write-Step "Checking saga transitions and compensation"
    $orderPayload = @{
        customer_id = 1
        total_amount = "199000"
        payment_method = "COD"
        shipping_method = "Standard"
        shipping_address = "Phase6 Acceptance Address"
        items = @(
            @{ book_id = 1; quantity = 1 },
            @{ book_id = 2; quantity = 1 }
        )
    }

    $successOrder = Invoke-JsonRequest -Method "POST" -Uri "http://localhost:8007/orders/" -Body $orderPayload -TimeoutSec 90
    $successSagaVisible = $false
    if ($successOrder.status_code -eq 201 -and $successOrder.body) {
        $hasConfirmed = ($successOrder.body.PSObject.Properties.Name -contains "status") -and ($successOrder.body.status -eq "Confirmed")
        $hasSagaLogs = ($successOrder.body.PSObject.Properties.Name -contains "saga_logs") -and (@($successOrder.body.saga_logs).Count -ge 4)
        $successSagaVisible = ($hasConfirmed -and $hasSagaLogs)
    }

    Invoke-Compose -Args @("stop", "ship-service")
    Wait-For -Name "ship-service stop" -Seconds 4
    $failedShippingOrder = Invoke-JsonRequest -Method "POST" -Uri "http://localhost:8007/orders/" -Body $orderPayload -TimeoutSec 90
    Invoke-Compose -Args @("start", "ship-service")
    Wait-For -Name "ship-service start" -Seconds 10

    $compensated = $false
    if ($failedShippingOrder.body -and ($failedShippingOrder.body.PSObject.Properties.Name -contains "status")) {
        $compensated = ($failedShippingOrder.status_code -eq 502 -and $failedShippingOrder.body.status -eq "Compensated")
    }

    $summary.criteria.saga_transition_and_compensation = ($successSagaVisible -and $compensated)
    $summary.evidence.saga = [ordered]@{
        success_order_status = $successOrder.status_code
        success_order_final_status = (Get-PropertyValue -Object $successOrder.body -Name "status")
        success_order_saga_log_count = if ($successOrder.body -and ($successOrder.body.PSObject.Properties.Name -contains "saga_logs")) { @($successOrder.body.saga_logs).Count } else { 0 }
        ship_down_order_status = $failedShippingOrder.status_code
        ship_down_order_final_status = (Get-PropertyValue -Object $failedShippingOrder.body -Name "status")
    }

    # 3) RabbitMQ event flow logs
    Write-Step "Checking event flow markers in logs"
    $serviceLogs = docker compose logs --tail=400 order-service pay-service ship-service | Out-String
    $logLines = $serviceLogs -split "`r?`n"
    $publishedLines = @($logLines | Where-Object { $_ -match "EVENT_PUBLISHED" })
    $consumedLines = @($logLines | Where-Object { $_ -match "EVENT_CONSUMED" })

    $summary.criteria.rabbitmq_event_flow_observable = ($publishedLines.Count -gt 0 -and $consumedLines.Count -gt 0)
    $summary.evidence.events = [ordered]@{
        event_published_count = $publishedLines.Count
        event_consumed_count = $consumedLines.Count
        sample_published = if ($publishedLines.Count -gt 0) { $publishedLines[0] } else { $null }
        sample_consumed = if ($consumedLines.Count -gt 0) { $consumedLines[0] } else { $null }
    }

    # 4) Health + metrics
    Write-Step "Checking health and metrics endpoints"
    $endpointChecks = @(
        @{ name = "gateway_health"; uri = "http://localhost:8000/health/"; expect = "json" },
        @{ name = "gateway_metrics"; uri = "http://localhost:8000/metrics/"; expect = "metrics" },
        @{ name = "auth_health"; uri = "http://localhost:8012/health/"; expect = "json" },
        @{ name = "auth_metrics"; uri = "http://localhost:8012/metrics/"; expect = "metrics" },
        @{ name = "order_health"; uri = "http://localhost:8007/health/"; expect = "json" },
        @{ name = "order_metrics"; uri = "http://localhost:8007/metrics/"; expect = "metrics" },
        @{ name = "pay_health"; uri = "http://localhost:8009/health/"; expect = "json" },
        @{ name = "pay_metrics"; uri = "http://localhost:8009/metrics/"; expect = "metrics" },
        @{ name = "ship_health"; uri = "http://localhost:8008/health/"; expect = "json" },
        @{ name = "ship_metrics"; uri = "http://localhost:8008/metrics/"; expect = "metrics" }
    )

    $healthMetricResults = @()
    foreach ($check in $endpointChecks) {
        try {
            $resp = Invoke-WebRequest -Uri $check.uri -Method Get -TimeoutSec 20 -UseBasicParsing
            $content = if ($resp.Content) { [string]$resp.Content } else { "" }
            $ok = $resp.StatusCode -eq 200
            if ($check.expect -eq "metrics") {
                $ok = $ok -and ($content -match "_total|_seconds")
            }
            $healthMetricResults += [pscustomobject]@{
                name = $check.name
                uri = $check.uri
                status_code = $resp.StatusCode
                ok = $ok
            }
        }
        catch {
            $healthMetricResults += [pscustomobject]@{
                name = $check.name
                uri = $check.uri
                status_code = 0
                ok = $false
                error = $_.Exception.Message
            }
        }
    }

    $summary.criteria.health_and_metrics_reachable = (@($healthMetricResults | Where-Object { -not $_.ok }).Count -eq 0)
    $summary.evidence.health_metrics = $healthMetricResults

    $summary.done = (@($summary.criteria.GetEnumerator() | Where-Object { -not $_.Value }).Count -eq 0)

    $artifactDir = Join-Path $PSScriptRoot "artifacts"
    if (-not (Test-Path $artifactDir)) {
        New-Item -Path $artifactDir -ItemType Directory | Out-Null
    }

    $artifactFile = Join-Path $artifactDir ("acceptance-summary-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json")
    $summaryJson = $summary | ConvertTo-Json -Depth 10
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($artifactFile, $summaryJson, $utf8NoBom)

    Write-Step "Acceptance summary saved: $artifactFile"
    $summaryJson
}
finally {
    Pop-Location
}
