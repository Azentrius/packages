# Changelog

## 1.6.0 – 2026-10-23

The repository serves Host Settings.

- **Server:** the sync takes the releases of
  [Azentrius/cockpit-host-settings](https://github.com/Azentrius/cockpit-host-settings), with the
  same checks as for every add-on (SHA256SUMS, the digest GitHub reports, the build provenance of
  its own release workflow). Its releases carry a `.deb` and a `.rpm`.
- **Catalog:** Cockpit lists Host Settings (`cockpit-host-settings`) under Applications, in step
  with the add-on's metainfo. It belongs on each server that should send messages.

## 1.5.0 – 2026-10-21

The repository serves Security Monitor.

- **Server:** the sync takes the releases of
  [Azentrius/cockpit-security-monitor](https://github.com/Azentrius/cockpit-security-monitor), with
  the same checks as for every add-on (SHA256SUMS, the digest GitHub reports, the build provenance
  of its own release workflow).
- **Catalog:** Cockpit lists Security Monitor (`cockpit-security-monitor`) under Applications, in
  step with the add-on's metainfo. Its 0.1 releases carry only a `.deb`: on Fedora and RHEL the
  entry shows up, but dnf finds no package to install. README and the web page say "Debian and
  Ubuntu only".

## 1.4.0 – 2026-10-21

The repository serves Status Board.

- **Server:** the sync takes the releases of
  [Azentrius/cockpit-status-board](https://github.com/Azentrius/cockpit-status-board), with the same
  checks as for every add-on (SHA256SUMS, the digest GitHub reports, the build provenance of its own
  release workflow).
- **Catalog:** Cockpit lists Status Board (`cockpit-status-board`) under Applications, in step with
  the add-on's metainfo. Its releases carry a `.deb` and an `.rpm`. It belongs on the Cockpit host
  from which the others are reached; README and the web page say so.

## 1.3.0 – 2026-10-20

The repository serves Update Gaps.

- **Server:** the sync takes the releases of
  [Azentrius/cockpit-update-gaps](https://github.com/Azentrius/cockpit-update-gaps), with the same
  checks as for every add-on (SHA256SUMS, the digest GitHub reports, the build provenance of its own
  release workflow).
- **Catalog:** Cockpit lists Update Gaps (`cockpit-update-gaps`) under Applications, in step with
  the add-on's metainfo. Its releases carry only a `.deb` so far: on Fedora and RHEL the entry shows
  up, but dnf finds no package to install. README and the web page say "Debian and Ubuntu only".

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
