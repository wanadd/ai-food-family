param(
  [string]$EnvFile = ".env.local-parity"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

docker compose --env-file $EnvFile -f docker-compose.local-parity.yml down
