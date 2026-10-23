# Azentrius packages

The package repository of the Azentrius add-ons for [Cockpit](https://cockpit-project.org):
**https://packages.azentrius.com**. Set it up once; Cockpit then lists the add-ons under
**Applications**, ready to install with a click, and the system's own updates keep them current.

| Add-on | Package | Source |
|---|---|---|
| Cron Jobs | `cockpit-cronjobs` | [Azentrius/cockpit-cronjobs](https://github.com/Azentrius/cockpit-cronjobs) |
| Image Update Monitor | `cockpit-image-update-monitor` | [Azentrius/cockpit-image-update-monitor](https://github.com/Azentrius/cockpit-image-update-monitor) |
| Update Gaps (Debian and Ubuntu only) | `cockpit-update-gaps` | [Azentrius/cockpit-update-gaps](https://github.com/Azentrius/cockpit-update-gaps) |
| Status Board (for the host with the host switcher) | `cockpit-status-board` | [Azentrius/cockpit-status-board](https://github.com/Azentrius/cockpit-status-board) |
| Security Monitor (Debian and Ubuntu only) | `cockpit-security-monitor` | [Azentrius/cockpit-security-monitor](https://github.com/Azentrius/cockpit-security-monitor) |
| Host Settings (on each server that should send messages) | `cockpit-host-settings` | [Azentrius/cockpit-host-settings](https://github.com/Azentrius/cockpit-host-settings) |

## Set up

**Debian and Ubuntu**

```bash
curl -fsSLO https://packages.azentrius.com/azentrius-repository.deb
sudo apt install ./azentrius-repository.deb
sudo apt update
```

**Fedora and RHEL**

```bash
sudo rpm --import https://packages.azentrius.com/azentrius.asc
sudo dnf install https://packages.azentrius.com/azentrius-repository.rpm
```

RHEL and its derivatives use the same dnf set-up; it is tested on Fedora and on the rebuilds Rocky
Linux and AlmaLinux 9 and 10, not on RHEL itself. openSUSE is not served
(`azentrius-repository` sets up only apt and dnf): there, install the `.rpm` from the add-on's
GitHub release after checking it with the release's `SHA256SUMS` and `gh attestation verify`.

Then open **Applications** in Cockpit (with administrative access), or install on the console, e.g.
`sudo apt install cockpit-cronjobs`. Removing `azentrius-repository` takes the repository out of
apt and dnf again; installed add-ons stay.

`azentrius-repository` installs:

- the signing key, `/usr/share/keyrings/azentrius.asc`, fingerprint
  `D264 AD8E ABB3 6515 FCD4 FA58 6076 85C4 2A3F C9E7`,
- the repository for apt (`/etc/apt/sources.list.d/azentrius.sources`) or dnf
  (`/etc/yum.repos.d/azentrius.repo`), whichever the system has,
- the AppStream catalog `/usr/share/swcatalog/xml/azentrius.xml`, from which Cockpit lists the
  add-ons.

## How packages get here

Every add-on repository builds its packages in its release workflow on GitHub and signs a build
provenance for them: a `.deb` and an `.rpm`, for Update Gaps and Security Monitor only a `.deb` so
far. Once an hour, `azentrius-packages sync` on the server takes new releases and adds a package
only if

1. its SHA-256 matches the release's `SHA256SUMS` and, when GitHub reports one, the digest of the
   asset, and
2. `gh attestation verify` confirms that the release workflow of its own repository built it.

It then signs the RPM and the APT metadata. The signing key belongs to a service user on the server
and never leaves it; GitHub has no access to the server, the server only reads public releases.
The key has no passphrase and does not expire (`server/setup.sh` creates it so, and the hourly sync
signs without anyone present): only file permissions protect it. Its folder
`/var/lib/azentrius-packages/gnupg` has mode 700 and belongs to the service user, so whoever is root
on the server or runs as that user can sign with it.

`azentrius-packages add FILE…` puts local packages into the repository without any of these checks
and signs them as the sync does. It is a way out for tests and emergencies, for root on the server
only (it runs as the service user, like `publish` below), not part of the normal way in.

## Server

`server/` holds everything for packages.azentrius.com (public-host): the tool
(`azentrius-packages.py`, Python 3, standard library only), its hardened systemd service and hourly
timer, the nginx site and the web page. `sudo sh server/setup.sh` sets it all up on Debian or Ubuntu
with nginx and certbot, and brings it up to date when run again:

- tools: `apt-ftparchive`, `createrepo_c`, `rpmsign`, `gpg`, GitHub CLI (`gh`, from its own APT
  repository),
- the service user `azentrius-packages` with the signing key (`/var/lib/azentrius-packages/gnupg`);
  the script stops if that key is not `repository/azentrius.asc`,
- the web root `/var/www/packages.azentrius.de` (`apt/`, `rpm/`, `azentrius.asc`, the stable names
  `azentrius-repository.deb` and `.rpm`),
- nginx with a Let's Encrypt certificate, and the timer `azentrius-packages.timer`.

The repository also answers as packages.azentrius.de, its first name, with the same files and no
redirect, so servers set up before `azentrius-repository` 1.2.0 keep working until their next
update moves them. Paths and the certificate on the server keep that name.

Operation:

```bash
sudo systemctl start azentrius-packages.service          # sync now
journalctl -u azentrius-packages.service -n 50           # what it added or skipped
sudo -u azentrius-packages GNUPGHOME=/var/lib/azentrius-packages/gnupg \
    azentrius-packages publish                            # rebuild the metadata only
```

A new add-on needs an entry in `REPOS` (in `server/azentrius-packages.py`) and in the catalog
`repository/azentrius.xml`, then a release of this repository, which brings the catalog to the
servers that use it, and `sudo sh server/setup.sh` run again on the server from a checkout with the
new entry: the sync runs the copy of the tool that `setup.sh` installed as
`/usr/local/bin/azentrius-packages`, so until then it takes no releases of the new add-on.

## Development

```bash
pip install -r test/requirements.txt
make lint           # shellcheck, ruff
make check          # catalog as Cockpit reads it, version and changelog, the server tool compiles
make packages       # dist/azentrius-repository_X.Y.Z-1_all.deb and -X.Y.Z-1.noarch.rpm
```

The `test` workflow also builds a signed APT and RPM repository with a throwaway key through the
server tool and installs `azentrius-repository` from it on Debian 13, Fedora 43, Rocky Linux 9 and
10 and AlmaLinux 9 and 10; the RPM systems import the repository's real key first.
`tools/build-packages.sh` is the same file in every Azentrius add-on.

Releases: raise `VERSION`, add a section to `CHANGELOG.md`, merge, then Actions › release › Run
workflow on `main`.

## License

Apache-2.0, see [LICENSE](LICENSE). The catalog is metadata under CC0-1.0, see [NOTICE](NOTICE).

Made by [Azentrius](https://azentrius.com).
