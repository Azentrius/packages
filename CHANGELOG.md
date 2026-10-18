# Changelog

## 1.2.0 – 2026-10-18

The repository has a new address: **https://packages.azentrius.com**.

- **`azentrius-repository`** points apt and dnf at `https://packages.azentrius.com/apt` and
  `https://packages.azentrius.com/rpm`. Servers that installed an earlier version move over with
  this update; until then packages.azentrius.de keeps serving the same files, without a redirect.
- The signing key stays the same (fingerprint `D264 AD8E ABB3 6515 FCD4 FA58 6076 85C4 2A3F C9E7`),
  including its user ID `packages@azentrius.de`.
- Maintainer address: support@azentrius.com.
- **Server:** the nginx site answers under both names; paths and the certificate keep the first
  name, so `server/setup.sh` updates an existing set-up in place. README, SECURITY, NOTICE and the
  web page name the new address.

## 1.1.0 – 2026-10-16

Image Update Monitor has a new package name.

- **Catalog:** the add-on is listed as Image Update Monitor, the same in every language, with the
  package `cockpit-image-update-monitor`, which replaces `cockpit-image-updates`. README and the web page
  say the same.
- `tools/build-packages.sh` is the new shared version, which can name packages a package replaces
  (`CONFLICTS`); `azentrius-repository` sets none.

## 1.0.0 – 2026-10-16

The package repository of the Azentrius Cockpit add-ons, packages.azentrius.de.

- `azentrius-repository` (`.deb` and `.rpm`) adds the repository to apt or dnf with its signing key
  (`/usr/share/keyrings/azentrius.asc`) and installs an AppStream catalog
  (`/usr/share/swcatalog/xml/azentrius.xml`), so Cockpit lists Cron Jobs (`cockpit-cronjobs`) and
  Image updates (`cockpit-image-updates`) under Applications. Removing it takes the repository out
  of apt and dnf again.
- `server/azentrius-packages.py` fills the repository from the GitHub releases of the add-ons: it adds a
  package only if its SHA-256 matches `SHA256SUMS` and the digest GitHub reports, and if
  `gh attestation verify` confirms that the release workflow of its own repository built it. It
  signs the RPMs and the APT metadata with a key that stays on the server.
- `server/setup.sh` sets up the server: tools, service user, signing key, nginx with a Let's Encrypt
  certificate, and an hourly timer.
