param(
  [string]$EnvFile = ".env.local-parity",
  [string]$Service = ""
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

if ($Service) {
  docker compose --env-file $EnvFile -f docker-compose.local-parity.yml logs -f $Service
} else {
  docker compose --env-file $EnvFile -f docker-compose.local-parity.yml logs -f
}
