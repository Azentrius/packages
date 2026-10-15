#!/bin/sh
# Sets up or updates packages.azentrius.de on a Debian or Ubuntu server with nginx and certbot.
#
#   sudo sh server/setup.sh        (from a checkout or the source archive of this repository)
#
# Idempotent: an existing signing key, certificate and repository stay; tools, units, the web
# page and the nginx site are brought up to date. Ends with one sync run.
# SPDX-License-Identifier: Apache-2.0
set -eu
# Files this script writes must be readable for others (apt reads keys as the user _apt, nginx
# serves as www-data), whatever root's own umask is.
umask 022
cd "$(dirname "$0")/.."

user=azentrius-packages
home=/var/lib/azentrius-packages
web=/var/www/packages.azentrius.de
site=/etc/nginx/sites-available/packages.azentrius.de
domain=packages.azentrius.de

[ "$(id -u)" = 0 ] || { echo "Run as root." >&2; exit 77; }

echo "== tools"
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq apt-utils createrepo-c rpm gnupg xz-utils curl > /dev/null
if ! gh attestation verify --help > /dev/null 2>&1; then
    # GitHub CLI from its own signed APT repository (the distribution's gh may be too old).
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        -o /usr/share/keyrings/githubcli-archive-keyring.gpg
    chmod 644 /usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        > /etc/apt/sources.list.d/github-cli.list
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq gh > /dev/null
fi

echo "== user and signing key"
if ! id "$user" > /dev/null 2>&1; then
    useradd --system --home-dir "$home" --create-home --shell /usr/sbin/nologin "$user"
fi
install -d -m 700 -o "$user" -g "$user" "$home" "$home/gnupg"
install -d -m 755 -o "$user" -g "$user" "$web"
g() { runuser -u "$user" -- env GNUPGHOME="$home/gnupg" gpg --batch "$@"; }
if [ -z "$(g --list-secret-keys --with-colons 2> /dev/null | grep '^sec' || true)" ]; then
    g --passphrase '' --quick-gen-key "Azentrius Packages <packages@azentrius.de>" rsa4096 sign never
fi
fpr=$(g --list-secret-keys --with-colons | awk -F: '/^fpr:/ {print $10; exit}')
if [ "$fpr" != "$(gpg --show-keys --with-colons repository/azentrius.asc | awk -F: '/^fpr:/ {print $10; exit}')" ]; then
    echo "The key on this server ($fpr) is not repository/azentrius.asc." >&2
    exit 1
fi

echo "== files"
install -m 755 server/azentrius-packages.py /usr/local/bin/azentrius-packages
install -m 644 server/azentrius-packages.service server/azentrius-packages.timer /etc/systemd/system/
install -m 644 -o "$user" -g "$user" server/index.html repository/azentrius.asc "$web/"

echo "== nginx and certificate"
if [ ! -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
    # First the challenge over plain HTTP, then the full site.
    printf 'server {\n    listen 80;\n    listen [::]:80;\n    server_name %s;\n    root %s;\n}\n' \
        "$domain" "$web" > "$site"
    ln -sf "$site" "/etc/nginx/sites-enabled/$domain"
    nginx -t -q && systemctl reload nginx
    certbot certonly --webroot -w "$web" -d "$domain" --non-interactive --agree-tos \
        --register-unsafely-without-email --keep-until-expiring
fi
install -m 644 server/nginx.conf "$site"
ln -sf "$site" "/etc/nginx/sites-enabled/$domain"
nginx -t -q && systemctl reload nginx

echo "== timer and first run"
systemctl daemon-reload
systemctl enable --now azentrius-packages.timer
systemctl start azentrius-packages.service
journalctl -u azentrius-packages.service -n 20 --no-pager -o cat
echo "Done: https://$domain/"
