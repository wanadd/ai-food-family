param(
  [string]$EnvFile = ".env.local-parity"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

function Fail([string]$Message) {
  throw "LOCAL PARITY SMOKE: FAIL - $Message"
}

function Invoke-Checked([scriptblock]$Command, [string]$Label) {
  & $Command
  if ($LASTEXITCODE -ne 0) {
    Fail "$Label failed with exit code $LASTEXITCODE"
  }
}

function Wait-For([string]$Label, [scriptblock]$Probe, [int]$TimeoutSeconds = 90) {
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  do {
    try {
      & $Probe
      return
    } catch {
      Start-Sleep -Seconds 2
    }
  } while ((Get-Date) -lt $deadline)
  Fail "$Label did not become reachable within ${TimeoutSeconds}s"
}

function Query([string]$Sql) {
  $value = docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T postgres `
    psql -h localhost -U aifood -d aifood -tAc $Sql
  if ($LASTEXITCODE -ne 0) {
    Fail "DB query failed: $Sql"
  }
  return $value.Trim()
}

try {
  if (!(Test-Path $EnvFile)) {
    Fail "missing $EnvFile"
  }

  Wait-For "web" {
    $web = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 10
    if ($web.StatusCode -lt 200 -or $web.StatusCode -ge 500) {
      throw "web returned $($web.StatusCode)"
    }
  }

  Wait-For "api" {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health/live" -TimeoutSec 10
    if ($health.status -ne "ok") {
      throw "api health not ok"
    }
  }

  $recipesTotal = [int](Query "select count(*) from recipes;")
  $maxRecipeId = [int](Query "select coalesce(max(id),0) from recipes;")
  $usersCount = [int](Query "select count(*) from users;")
  $menuSelectionsCount = [int](Query "select count(*) from family_menu_selections;")
  $shoppingListsCount = [int](Query "select count(*) from family_shopping_lists;")
  if ($recipesTotal -lt 250 -or $maxRecipeId -lt 265 -or $usersCount -le 0) {
    Fail "snapshot counts are not prod-compatible: recipes_total=$recipesTotal max_recipe_id=$maxRecipeId users_count=$usersCount"
  }

  $redis = (docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T redis redis-cli ping).Trim()
  if ($redis -ne "PONG") {
    Fail "redis ping failed"
  }

  $settingsCheck = "from app.config import settings; assert settings.is_local_parity; assert not settings.telegram_outbound_allowed; assert not settings.notification_scheduler_allowed; assert not settings.care_scheduler_allowed; print('side_effects_disabled')"
  Invoke-Checked {
    docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T api python -c $settingsCheck
  } "Checking side-effect flags"

  $login = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/local-parity-login" -TimeoutSec 10
  $initData = $login.local_parity_init_data
  if (!$initData -or !$initData.StartsWith("planam-local-parity-v1:")) {
    Fail "local parity auth did not return a local parity init token"
  }
  $headers = @{
    "X-Telegram-Init-Data" = $initData
    "X-App-Mode" = "personal"
  }

  Invoke-RestMethod -Uri "http://localhost:8000/menus/selected" -Headers $headers -TimeoutSec 10 | Out-Null
  Invoke-RestMethod -Uri "http://localhost:8000/menus/overview" -Headers $headers -TimeoutSec 10 | Out-Null
  Invoke-RestMethod -Uri "http://localhost:8000/shopping-lists/me" -Headers $headers -TimeoutSec 10 | Out-Null
  Invoke-RestMethod -Uri "http://localhost:8000/notifications/settings" -Headers $headers -TimeoutSec 10 | Out-Null

  $careSending = [int](Query "select count(*) from care_notifications where status in ('pending','sending');")
  Write-Host "recipes_total: $recipesTotal"
  Write-Host "max_recipe_id: $maxRecipeId"
  Write-Host "users_count: $usersCount"
  Write-Host "family_menu_selections_count: $menuSelectionsCount"
  Write-Host "family_shopping_lists_count: $shoppingListsCount"
  Write-Host "care_pending_or_sending: $careSending"
  Write-Host "LOCAL PARITY SMOKE: PASS"
} catch {
  Fail $_.Exception.Message
}
