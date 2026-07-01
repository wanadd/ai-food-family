param(
  [string]$EnvFile = ".env.local-parity",
  [int]$ExpectedRecipesTotal = 0,
  [string]$Database = "aifood",
  [string]$User = "aifood"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

function Fail([string]$Message) {
  throw "LOCAL PARITY SMOKE: FAIL - $Message"
}

function Query([string]$Sql) {
  return (docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T postgres psql -U $User -d $Database -tAc $Sql).Trim()
}

try {
  $web = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 10
  if ($web.StatusCode -lt 200 -or $web.StatusCode -ge 500) { Fail "web returned $($web.StatusCode)" }

  $health = Invoke-RestMethod -Uri "http://localhost:8000/health/live" -TimeoutSec 10
  if ($health.status -ne "ok") { Fail "api health not ok" }

  $recipesTotal = [int](Query "select count(*) from recipes;")
  if ($ExpectedRecipesTotal -gt 0 -and $recipesTotal -ne $ExpectedRecipesTotal) {
    Fail "recipes count $recipesTotal != expected $ExpectedRecipesTotal"
  }

  $redis = (docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T redis redis-cli ping).Trim()
  if ($redis -ne "PONG") { Fail "redis ping failed" }

  $login = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/local-parity-login" -TimeoutSec 10
  $initData = $login.local_parity_init_data
  if (!$initData) { Fail "local parity auth did not return init data" }
  $headers = @{
    "X-Telegram-Init-Data" = $initData
    "X-App-Mode" = "personal"
  }

  Invoke-RestMethod -Uri "http://localhost:8000/menus/selected" -Headers $headers -TimeoutSec 10 | Out-Null
  Invoke-RestMethod -Uri "http://localhost:8000/menus/overview" -Headers $headers -TimeoutSec 10 | Out-Null
  Invoke-RestMethod -Uri "http://localhost:8000/shopping-lists/current" -Headers $headers -TimeoutSec 10 | Out-Null
  Invoke-RestMethod -Uri "http://localhost:8000/notifications/settings" -Headers $headers -TimeoutSec 10 | Out-Null

  $careSending = [int](Query "select count(*) from care_notifications where status in ('pending','sending');")
  Write-Host "recipes_total: $recipesTotal"
  Write-Host "care_pending_or_sending: $careSending"
  Write-Host "LOCAL PARITY SMOKE: PASS"
} catch {
  Fail $_.Exception.Message
}
