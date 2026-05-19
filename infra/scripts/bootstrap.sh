#!/bin/bash
# bootstrap.sh — run on dev box ONCE to provision the chesterwc service.
# Idempotent where possible. Run as root.
set -euo pipefail

# 1. Create user + group
id chesterwc >/dev/null 2>&1 || useradd --system --shell /usr/sbin/nologin chesterwc

# 2. Directories
install -d -m 0750 -o chesterwc -g chesterwc /opt/chesterwc
install -d -m 0750 -o chesterwc -g chesterwc /var/lib/chesterwc
install -d -m 0750 -o chesterwc -g chesterwc /var/backups/chesterwc
install -d -m 0750 -o chesterwc -g chesterwc /var/log/chesterwc
install -d -m 0750 -o root -g chesterwc /etc/chesterwc

# 3. Secrets (placeholders — fill in by hand after running)
for f in resend-api-key whatsapp-webhook-url anthropic-api-key admin-creds.txt; do
  if [ ! -f /etc/chesterwc/$f ]; then
    : > /etc/chesterwc/$f
    chmod 0640 /etc/chesterwc/$f
    chown root:chesterwc /etc/chesterwc/$f
  fi
done

# 4. backend.env
cat > /etc/chesterwc/backend.env <<'ENV'
CHESTERWC_DB=/var/lib/chesterwc/app.db
CHESTERWC_HOST=127.0.0.1
CHESTERWC_PORT=8094
CHESTERWC_FROM=hello@chesterwindowcleaner.co.uk
CHESTERWC_ALERT_TO=findgriff@gmail.com
CHESTERWC_RESEND_KEY_PATH=/etc/chesterwc/resend-api-key
CHESTERWC_WHATSAPP_URL_PATH=/etc/chesterwc/whatsapp-webhook-url
CHESTERWC_ANTHROPIC_KEY_PATH=/etc/chesterwc/anthropic-api-key
ENV
chmod 0640 /etc/chesterwc/backend.env
chown root:chesterwc /etc/chesterwc/backend.env

# 5. Install systemd units (copied from repo)
install -m 0644 /opt/chesterwc/infra/systemd/chesterwc-backend.service \
  /etc/systemd/system/chesterwc-backend.service
install -m 0644 /opt/chesterwc/infra/systemd/chesterwc-backup.service \
  /etc/systemd/system/chesterwc-backup.service
install -m 0644 /opt/chesterwc/infra/systemd/chesterwc-backup.timer \
  /etc/systemd/system/chesterwc-backup.timer

# 6. Caddy config
install -m 0644 /opt/chesterwc/infra/caddy/chesterwindowcleaner.caddy \
  /etc/caddy/Caddyfile.d/chesterwindowcleaner.caddy

systemctl daemon-reload
systemctl enable --now chesterwc-backend.service
systemctl enable --now chesterwc-backup.timer
caddy validate --config /etc/caddy/Caddyfile && systemctl reload caddy

echo "✓ bootstrap complete"
echo "Next: fill in /etc/chesterwc/{resend-api-key, whatsapp-webhook-url, anthropic-api-key}"
echo "      and run:  caddy hash-password   then put the hash in the .caddy file"
