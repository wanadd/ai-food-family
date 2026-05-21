#!/bin/sh
set -e

TEMPLATE="${NGINX_TEMPLATE:-app-init.conf.template}"
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"

if [ -f "$CERT_PATH" ]; then
  TEMPLATE="app-ssl.conf.template"
fi

if [ -z "$DOMAIN" ]; then
  echo "ERROR: DOMAIN environment variable is required for nginx"
  exit 1
fi

envsubst '$DOMAIN' < "/etc/nginx/templates/${TEMPLATE}" > /etc/nginx/conf.d/default.conf
echo "nginx: using template ${TEMPLATE} for domain ${DOMAIN}"

exec nginx -g 'daemon off;'
