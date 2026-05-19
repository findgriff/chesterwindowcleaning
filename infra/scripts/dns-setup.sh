#!/bin/bash
# Creates A records via Cloudflare API.
# Requires: $CF_API_TOKEN and a $CF_ZONE_ID for chesterwindowcleaner.co.uk.
set -euo pipefail
: "${CF_API_TOKEN:?need CF_API_TOKEN}"
: "${CF_ZONE_ID:?need CF_ZONE_ID for chesterwindowcleaner.co.uk}"

DEV_BOX_IP="178.104.242.211"

cf() {
  curl -sS -X "$1" "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records${2:-}" \
    -H "Authorization: Bearer ${CF_API_TOKEN}" \
    -H "Content-Type: application/json" \
    ${3:+-d "$3"}
}

echo "Creating apex A record..."
cf POST "" "$(printf '{"type":"A","name":"@","content":"%s","proxied":false,"ttl":300}' "$DEV_BOX_IP")"
echo
echo "Creating www A record..."
cf POST "" "$(printf '{"type":"A","name":"www","content":"%s","proxied":false,"ttl":300}' "$DEV_BOX_IP")"
echo
echo "✓ apex + www A records created. Add Resend DKIM/SPF/return-path records via Resend dashboard once domain verification starts."
