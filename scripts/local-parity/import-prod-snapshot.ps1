param(
  [Parameter(Mandatory = $true)]
  [string]$DumpPath,
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

function Query-Db([string]$Sql) {
  $value = docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T postgres `
    psql -h localhost -U aifood -d aifood -tAc $Sql
  if ($LASTEXITCODE -ne 0) {
    throw "DB query failed: $Sql"
  }
  return $value.Trim()
}

function Assert-SnapshotCounts() {
  $recipesTotal = [int](Query-Db "select count(*) from recipes;")
  $maxRecipeId = [int](Query-Db "select coalesce(max(id),0) from recipes;")
  $usersCount = [int](Query-Db "select count(*) from users;")
  $menuSelectionsCount = [int](Query-Db "select count(*) from family_menu_selections;")
  $shoppingListsCount = [int](Query-Db "select count(*) from family_shopping_lists;")

  Write-Host "recipes_total: $recipesTotal"
  Write-Host "max_recipe_id: $maxRecipeId"
  Write-Host "users_count: $usersCount"
  Write-Host "family_menu_selections_count: $menuSelectionsCount"
  Write-Host "family_shopping_lists_count: $shoppingListsCount"

  if ($recipesTotal -lt 250 -or $maxRecipeId -lt 265 -or $usersCount -le 0 -or $menuSelectionsCount -le 0 -or $shoppingListsCount -lt 0) {
    throw "Snapshot validation failed: recipes_total=$recipesTotal max_recipe_id=$maxRecipeId users_count=$usersCount family_menu_selections_count=$menuSelectionsCount family_shopping_lists_count=$shoppingListsCount"
  }
}

$resolvedDump = (Resolve-Path $DumpPath).Path
if (!(Test-Path $resolvedDump)) {
  throw "Dump file not found: $DumpPath"
}
if (!(Test-Path $EnvFile)) {
  throw "Missing $EnvFile. Copy .env.local-parity.example to .env.local-parity first."
}

Invoke-Checked {
  docker compose --env-file $EnvFile -f docker-compose.local-parity.yml up -d postgres
} "Starting local parity postgres"

$containerDump = "/tmp/planam_local_parity_snapshot.dump"
Invoke-Checked {
  docker compose --env-file $EnvFile -f docker-compose.local-parity.yml cp $resolvedDump "postgres:$containerDump"
} "Copying snapshot into postgres container"

$restoreScript = @'
set -e
until pg_isready -h localhost -U "$POSTGRES_USER" -d postgres; do
  sleep 1
done
psql -h localhost -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '$POSTGRES_DB' and pid <> pg_backend_pid();"
dropdb --if-exists -h localhost -U "$POSTGRES_USER" "$POSTGRES_DB"
createdb -h localhost -U "$POSTGRES_USER" "$POSTGRES_DB"
pg_restore --no-owner --no-acl -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" /tmp/planam_local_parity_snapshot.dump
'@

Invoke-Checked {
  docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T postgres sh -lc $restoreScript
} "Restoring local parity snapshot"

Assert-SnapshotCounts

Invoke-Checked {
  docker compose --env-file $EnvFile -f docker-compose.local-parity.yml up -d api
} "Starting local parity api"

Invoke-Checked {
  docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T api python -c "from app.database import init_db; init_db(); print('schema checked')"
} "Running schema check"

Assert-SnapshotCounts
Write-Host "Local parity import complete."
