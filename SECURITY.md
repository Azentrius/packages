# Security Policy

## Reporting a vulnerability

Please do **not** open a public issue for security problems.

Report them privately through GitHub instead:
[Report a vulnerability](https://github.com/Azentrius/packages/security/advisories/new)
(tab **Security → Report a vulnerability** in this repository).

Please include:

- what is affected (the repository server, `azentrius-repository`, the catalog; version or commit),
- steps to reproduce,
- the impact you expect.

We aim to acknowledge reports within 7 days. This is a small project, so a fix
may take longer; we will keep you informed and credit you in the advisory
unless you prefer to stay anonymous.

## Supported versions

Only the latest release and the latest state of the `main` branch receive
security fixes.

## Especially relevant

packages.azentrius.de delivers software that runs as root on servers.
Reports are particularly welcome for:

- ways to get a package into the repository that was not built by the release
  workflow of its own Azentrius repository (checksum, digest or provenance
  checks that can be bypassed),
- anything that exposes or misuses the signing key, or signs something else,
- `azentrius-repository` writing files outside the apt and dnf repository
  configuration it is meant to change,
- the catalog making Cockpit offer a package under a wrong name.
