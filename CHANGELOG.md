# Changelog

## Unreleased

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
