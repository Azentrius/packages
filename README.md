# Azentrius packages

The package repository of the Azentrius add-ons for [Cockpit](https://cockpit-project.org):
**https://packages.azentrius.de**. Set it up once; Cockpit then lists the add-ons under
**Applications**, ready to install with a click, and the system's own updates keep them current.

| Add-on | Package | Source |
|---|---|---|
| Cron Jobs | `cockpit-cronjobs` | [Azentrius/cockpit-cronjobs](https://github.com/Azentrius/cockpit-cronjobs) |
| Image updates | `cockpit-image-updates` | [Azentrius/cockpit-image-update-monitor](https://github.com/Azentrius/cockpit-image-update-monitor) |

## Set up

**Debian and Ubuntu**

```bash
curl -fsSLO https://packages.azentrius.de/azentrius-repository.deb
sudo apt install ./azentrius-repository.deb
sudo apt update
```

**Fedora, RHEL and openSUSE**

```bash
sudo rpm --import https://packages.azentrius.de/azentrius.asc
sudo dnf install https://packages.azentrius.de/azentrius-repository.rpm
```

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

Every add-on repository builds its `.deb` and `.rpm` in its release workflow on GitHub and signs a
build provenance for them. Once an hour, `azentrius-packages sync` on the server takes new releases
and adds a package only if

1. its SHA-256 matches the release's `SHA256SUMS` and the digest GitHub reports for the asset, and
2. `gh attestation verify` confirms that the release workflow of its own repository built it.

It then signs the RPM and the APT metadata. The signing key belongs to a service user on the server
and never leaves it; GitHub has no access to the server, the server only reads public releases.

## Server

`server/` holds everything for packages.azentrius.de (public-host): the tool
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

Operation:

```bash
sudo systemctl start azentrius-packages.service          # sync now
journalctl -u azentrius-packages.service -n 50           # what it added or skipped
sudo -u azentrius-packages GNUPGHOME=/var/lib/azentrius-packages/gnupg \
    azentrius-packages publish                            # rebuild the metadata only
```

A new add-on needs an entry in `REPOS` (in `server/azentrius-packages.py`) and in the catalog
`repository/azentrius.xml`, then a release of this repository.

## Development

```bash
pip install -r test/requirements.txt
make lint           # shellcheck, ruff
make check          # catalog as Cockpit reads it, version and changelog, the server tool compiles
make packages       # dist/azentrius-repository_X.Y.Z-1_all.deb and -X.Y.Z-1.noarch.rpm
```

The `test` workflow also builds a signed APT and RPM repository with a throwaway key through the
server tool and installs `azentrius-repository` from it on Debian 13 and Fedora 43.
`tools/build-packages.sh` is the same file in every Azentrius add-on.

Releases: raise `VERSION`, add a section to `CHANGELOG.md`, merge, then Actions › release › Run
workflow on `main`.

## License

Apache-2.0, see [LICENSE](LICENSE). The catalog is metadata under CC0-1.0, see [NOTICE](NOTICE).
