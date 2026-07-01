param(
  [Parameter(Mandatory = $true)]
  [string]$DumpPath,
  [string]$EnvFile = ".env.local-parity",
  [string]$Database = "aifood",
  [string]$User = "aifood"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

$resolvedDump = Resolve-Path $DumpPath
if (!(Test-Path $resolvedDump)) {
  throw "Dump file not found: $DumpPath"
}
if (!(Test-Path $EnvFile)) {
  throw "Missing $EnvFile. Copy .env.local-parity.example to .env.local-parity first."
}

docker compose --env-file $EnvFile -f docker-compose.local-parity.yml up -d postgres

$postgresContainer = (docker compose --env-file $EnvFile -f docker-compose.local-parity.yml ps -q postgres).Trim()
if (!$postgresContainer) {
  throw "Local parity postgres container is not running."
}

$containerDump = "/tmp/planam_local_parity_snapshot.dump"
docker cp $resolvedDump "${postgresContainer}:$containerDump"

$dropSql = "select pg_terminate_backend(pid) from pg_stat_activity where datname = '$Database' and pid <> pg_backend_pid(); drop database if exists $Database; create database $Database;"
docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T postgres psql -U $User -d postgres -v ON_ERROR_STOP=1 -c $dropSql
docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T postgres pg_restore --clean --if-exists --no-owner --no-acl -U $User -d $Database $containerDump

docker compose --env-file $EnvFile -f docker-compose.local-parity.yml up -d api
docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T api python -c "from app.database import init_db; init_db(); print('schema checked')"

function Query([string]$Sql) {
  return (docker compose --env-file $EnvFile -f docker-compose.local-parity.yml exec -T postgres psql -U $User -d $Database -tAc $Sql).Trim()
}

Write-Host "recipes_total: $(Query 'select count(*) from recipes;')"
Write-Host "max_recipe_id: $(Query 'select coalesce(max(id),0) from recipes;')"
Write-Host "users_count: $(Query 'select count(*) from users;')"
Write-Host "latest_menu_selection_count: $(Query 'select count(*) from family_menu_selections;')"
Write-Host "shopping_lists_count: $(Query 'select count(*) from family_shopping_lists;')"
Write-Host "Local parity import complete."
