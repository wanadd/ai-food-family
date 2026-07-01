param(
  [string]$EnvFile = ".env.local-parity",
  [string]$Database = "aifood",
  [string]$User = "aifood"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

if (!(Test-Path $EnvFile)) {
  throw "Missing $EnvFile. Copy .env.local-parity.example to .env.local-parity first."
}

docker compose --env-file $EnvFile -f docker-compose.local-parity.yml up -d --build

$commit = git rev-parse --short HEAD

function Query-DbValue([string]$Sql) {
  return (docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T postgres psql -U $User -d $Database -tAc $Sql).Trim()
}

$recipesTotal = "n/a"
$maxRecipeId = "n/a"
try {
  $recipesTotal = Query-DbValue "select count(*) from recipes;"
  $maxRecipeId = Query-DbValue "select coalesce(max(id),0) from recipes;"
} catch {
  Write-Warning "DB stats unavailable yet: $($_.Exception.Message)"
}

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
