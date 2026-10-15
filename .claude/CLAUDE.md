# Notes for working on this repository

## What this is

The package repository of the Azentrius Cockpit add-ons, packages.azentrius.de (on public-host):
the package `azentrius-repository` that sets it up on a server (signing key, apt or dnf repository,
AppStream catalog for Cockpit's Applications page), and the server side that fills it from the
GitHub releases of the add-ons, verifies and signs.

- Overview, setup and operation: `README.md`
- What changed: `CHANGELOG.md`

## Working together

- Big picture first in a few sentences, then details; the recommendation first, then the reasons.
- This repository decides what runs as root on every server that uses it. For anything that touches
  the checks, the signing key or the catalog, say briefly what the user has to understand to answer
  for it.

## Repository conventions

The same in every Azentrius repository.

- **Language.** Everything in the repository is English: code, comments, docs, commit messages, pull
  requests, test names and test data. The only German is the German translation and the tests that
  check it. User-facing texts always exist in English and German; German addresses the user formally
  (“Sie”). Answer the user in the language they write in.
- **Versions.** Semantic Versioning; the version lives in exactly one place (see “Releases and the
  repository”). Tags are `vX.Y.Z`.
- **Changelog.** `CHANGELOG.md`, newest first. Each version gets `## X.Y.Z – YYYY-MM-DD`, a one-line
  summary, then bullets. The pull request that raises the version adds its section.
- **Pull requests.** `main` is protected: every change goes through a pull request and is
  squash-merged once the `test` check is green; the branch is deleted afterwards. The PR title becomes
  the commit on `main`: short, imperative, English, without version numbers.
- **Authorship.** Commits on `main` are authored by the maintainer (the squash merge takes care of
  that). Commits, pull requests and files carry no co-author trailers and no “generated with” lines.

Here there is no translation file: the German texts are in the catalog (`xml:lang="de"`) and on the
web page (`server/index.html`).

## Repository baseline

The same in every Azentrius repository; keep it when changing the repository or its settings.

- **Security.** `SECURITY.md` with private vulnerability reporting; secret scanning with push
  protection; Dependabot alerts and security updates; Dependabot version updates for every
  ecosystem in use and for GitHub Actions; CodeQL default setup.
- **Branches and tags.** Ruleset `main`: pull request, squash only, linear history, no deletion or
  force push, required check `test`. Ruleset `release tags`: `v*` cannot be deleted or moved.
- **CI.** The job `test` runs every test and every lint on each push and pull request. Actions are
  pinned by commit SHA with the version as a comment; checkouts use `persist-credentials: false`;
  the token is read-only unless a job needs more. Check tools are pinned as well, so Dependabot keeps
  them current.
- **Releases.** Only the `release` workflow makes releases, on request, from `main`: it checks the
  version against the code and the existing tags, runs all tests, builds the artifact with
  `SHA256SUMS`, signs a build provenance (`gh attestation verify`) and takes the notes from
  `CHANGELOG.md`. Releases are immutable. Files that are not for users stay out of the artifact.
- **Licensing.** Apache-2.0: `LICENSE` in the root, an SPDX header in every source file, `NOTICE`
  for third-party material.

Here: check tools in `test/requirements.txt` (pip); lint is `make lint` (`shellcheck --severity=warning`,
`ruff check` with the rules in `ruff.toml`); the artifacts are the `.deb` and `.rpm` of
`azentrius-repository` (`make packages`, built by `tools/build-packages.sh` from `packaging/`). Job
`test` also builds a signed APT and RPM repository with a throwaway key through the server tool and
installs from it on Debian and Fedora.

## Layout

```
repository/azentrius.asc   public signing key (the private key is only on public-host)
repository/azentrius.xml   AppStream catalog; one component per add-on, in step with its metainfo
packaging/                 package.conf of azentrius-repository; scripts/configure writes the apt or
                           dnf repository file, scripts/remove deletes it
server/azentrius-packages.py   sync (GitHub releases -> checks -> add -> publish), publish, add
server/*.service, *.timer  hourly sync as the user azentrius-packages, hardened
server/nginx.conf, index.html  the site
server/setup.sh            sets up or updates public-host (idempotent)
tools/build-packages.sh    .deb and .rpm from a staged tree; the same file in every Azentrius add-on
tools/check-catalog.py     the catalog as Cockpit reads it (pkg/apps/watch-appstream.py)
VERSION                    the version of azentrius-repository
```

## Commands

```sh
make lint && make check     # as in CI
make packages               # dist/*.deb, dist/*.rpm (needs dpkg-deb and rpmbuild)
```

## Rules (not negotiable)

1. **Nothing unverified gets in.** A package is added only after SHA256SUMS, the GitHub asset digest
   and `gh attestation verify --signer-workflow <repo>/.github/workflows/release.yml` agree.
   `add` exists for tests and emergencies only.
2. **The signing key stays on public-host** (`/var/lib/azentrius-packages/gnupg`, service user).
   Never copy it, never add it to GitHub. `setup.sh` refuses a key that differs from
   `repository/azentrius.asc`.
3. **GitHub has no access to the server.** The server only reads public releases (pull).
4. **Catalog and add-ons agree:** `id`, `pkgname` and the `cockpit-manifest` launchable match the
   add-on's `packaging/*.metainfo.xml` and Cockpit package directory.

## Useful knowledge

- Cockpit (`pkg/apps/watch-appstream.py`) reads only AppStream **XML** from `/usr/share/swcatalog/xml`,
  `/var/cache/swcatalog/xml`, `/usr/share/app-info/xmls` and similar, never the DEP-11 YAML of APT
  repositories. That is why the catalog comes as a file in `azentrius-repository`.
- RPMs are signed on the server (`rpmsign`), so the RPM in the repository differs from the release
  asset; the provenance is checked before signing. dnf needs the key imported once
  (`rpm --import`): an RPM scriptlet cannot run `rpm --import` (database lock).
- `gh attestation verify --bundle` works without a GitHub login; the bundle comes from
  `GET /repos/<repo>/attestations/sha256:<digest>`, which needs no login either.
- APT: `Signed-By` with an armored `.asc` works on Debian 12+ and Ubuntu 22.04+.
