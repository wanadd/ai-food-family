#!/bin/sh
# Issue or renew Let's Encrypt certificate for production deploy.
# Usage (on the server, from project root):
#   chmod +x deploy/init-letsencrypt.sh
#   export DOMAIN=your-domain.com
#   export CERTBOT_EMAIL=admin@your-domain.com
#   ./deploy/init-letsencrypt.sh

set -e

if [ -z "$DOMAIN" ] || [ -z "$CERTBOT_EMAIL" ]; then
  echo "Set DOMAIN and CERTBOT_EMAIL before running this script."
  exit 1
fi

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

echo ">> Requesting certificate for ${DOMAIN}"

docker compose -f "$COMPOSE_FILE" run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$CERTBOT_EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

echo ">> Reloading nginx (entrypoint switches to HTTPS when cert exists)"
docker compose -f "$COMPOSE_FILE" restart nginx

echo ">> Done. Open https://${DOMAIN}"
