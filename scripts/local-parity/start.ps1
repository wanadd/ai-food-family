param(
  [string]$EnvFile = ".env.local-parity"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

function Invoke-Checked([scriptblock]$Command, [string]$Label) {
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "$Label failed with exit code $LASTEXITCODE"
  }
}

function Get-EnvValue([string]$Key) {
  $line = Get-Content $EnvFile | Where-Object { $_ -match "^$([regex]::Escape($Key))=" } | Select-Object -First 1
  if (!$line) { return "" }
  return ($line -split "=", 2)[1].Trim()
}

function Wait-Until([string]$Label, [scriptblock]$Probe, [int]$TimeoutSeconds = 120) {
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  do {
    try {
      $global:LASTEXITCODE = 0
      & $Probe
      if ($LASTEXITCODE -eq 0) {
        Write-Host "${Label}: ready"
        return
      }
    } catch {
      Start-Sleep -Seconds 2
      continue
    }
    Start-Sleep -Seconds 2
  } while ((Get-Date) -lt $deadline)
  throw "$Label did not become ready within ${TimeoutSeconds}s"
}

if (!(Test-Path $EnvFile)) {
  throw "Missing $EnvFile. Copy .env.local-parity.example to .env.local-parity first."
}

$commit = git rev-parse --short HEAD
$telegramOutbound = Get-EnvValue "TELEGRAM_OUTBOUND_ENABLED"
$careScheduler = Get-EnvValue "CARE_SCHEDULER_ENABLED"
$notificationScheduler = Get-EnvValue "NOTIFICATION_SCHEDULER_ENABLED"
$disableExternal = Get-EnvValue "DISABLE_EXTERNAL_SIDE_EFFECTS"

Write-Host "Current git commit: $commit"
Write-Host "TELEGRAM_OUTBOUND_ENABLED=$telegramOutbound"
Write-Host "CARE_SCHEDULER_ENABLED=$careScheduler"
Write-Host "NOTIFICATION_SCHEDULER_ENABLED=$notificationScheduler"
Write-Host "DISABLE_EXTERNAL_SIDE_EFFECTS=$disableExternal"

Invoke-Checked {
  docker compose --env-file $EnvFile -f docker-compose.local-parity.yml up -d --build postgres redis api web
} "Starting local parity services"

Wait-Until "postgres" {
  docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T postgres pg_isready -h localhost -U aifood -d aifood | Out-Null
}

Wait-Until "redis" {
  $pong = (docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T redis redis-cli ping).Trim()
  if ($pong -ne "PONG") { throw "redis returned $pong" }
}

Wait-Until "api health" {
  $health = Invoke-RestMethod -Uri "http://localhost:8000/health/live" -TimeoutSec 5
  if ($health.status -ne "ok") { throw "api health returned $($health | ConvertTo-Json -Compress)" }
}

Wait-Until "web" {
  $web = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
  if ($web.StatusCode -lt 200 -or $web.StatusCode -ge 500) { throw "web returned $($web.StatusCode)" }
}

function Query-DbValue([string]$Sql) {
  return (docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T postgres psql -h localhost -U aifood -d aifood -tAc $Sql).Trim()
}

$recipesTotal = Query-DbValue "select count(*) from recipes;"
$maxRecipeId = Query-DbValue "select coalesce(max(id),0) from recipes;"

Write-Host ""
Write-Host "WEB: http://localhost:3000"
Write-Host "API: http://localhost:8000"
Write-Host "API health: http://localhost:8000/health/live"
Write-Host "Mode: local-parity"
Write-Host "Current git commit: $commit"
Write-Host "DB recipes_total: $recipesTotal"
Write-Host "DB max_recipe_id: $maxRecipeId"
Write-Host "Care scheduler: disabled"
Write-Host "Telegram outbound: disabled"
