#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Keeps packages.azentrius.de: the APT and RPM repository of the Azentrius Cockpit add-ons.

    azentrius-packages sync          take new releases from GitHub, verify them, add their
                                     packages and rebuild the repositories
    azentrius-packages publish       rebuild the repositories from the packages already there
    azentrius-packages add FILE...   add local packages without GitHub (tests, emergencies)

A package is added only if its SHA-256 matches the release's SHA256SUMS and the asset digest
GitHub reports, and if `gh attestation verify` confirms that the release workflow of its own
repository built it. RPMs are then signed; the APT metadata is signed. The signing key never
leaves this machine (GNUPGHOME of the service user).

Environment (defaults for public-host):
    AZPKG_ROOT   /var/www/packages.azentrius.de   what the web server serves
    AZPKG_STATE  /var/lib/azentrius-packages      state, lock, GNUPGHOME (gnupg/)
    AZPKG_KEY    fingerprint of the signing key
"""
import argparse
import fcntl
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

REPOS = [
    "Azentrius/packages",
    "Azentrius/cockpit-cronjobs",
    "Azentrius/cockpit-image-update-monitor",
]
ROOT = pathlib.Path(os.environ.get("AZPKG_ROOT", "/var/www/packages.azentrius.de"))
STATE = pathlib.Path(os.environ.get("AZPKG_STATE", "/var/lib/azentrius-packages"))
KEY = os.environ.get("AZPKG_KEY", "D264AD8EABB36515FCD4FA58607685C42A3FC9E7")
GNUPGHOME = os.environ.get("GNUPGHOME", str(STATE / "gnupg"))
API = "https://api.github.com"
APT = ROOT / "apt"
POOL = APT / "pool" / "main"
RPM = ROOT / "rpm"
ARCHES = ("all", "amd64", "arm64")


def log(*args):
    print(*args, flush=True)


def run(cmd, **kw):
    env = dict(os.environ, GNUPGHOME=GNUPGHOME)
    return subprocess.run(cmd, check=True, env=env, **kw)


def http(url, accept="application/vnd.github+json"):
    req = urllib.request.Request(url, headers={
        "Accept": accept, "User-Agent": "azentrius-packages", "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parse_sums(text):
    """SHA256SUMS lines "<hex>  <name>" (also "*name") -> {name: hex}."""
    sums = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 64:
            sums[parts[1].lstrip("*")] = parts[0].lower()
    return sums


def verify_attestation(repo, path, digest, work):
    """gh checks the Sigstore bundle offline: built by .github/workflows/release.yml of REPO."""
    data = json.loads(http(f"{API}/repos/{repo}/attestations/sha256:{digest}"))
    bundles = [a["bundle"] for a in data.get("attestations", [])]
    if not bundles:
        raise RuntimeError(f"{path.name}: no attestation")
    bundle = work / "bundle.jsonl"
    bundle.write_text("".join(json.dumps(b) + "\n" for b in bundles))
    (work / "gh").mkdir(exist_ok=True)
    env = dict(os.environ, GH_TOKEN="", GITHUB_TOKEN="", GH_CONFIG_DIR=str(work / "gh"))
    subprocess.run(["gh", "attestation", "verify", str(path), "--repo", repo, "--bundle", str(bundle),
                    "--signer-workflow", f"{repo}/.github/workflows/release.yml"],
                   check=True, env=env, stdout=subprocess.DEVNULL)


def add(path):
    """Put one verified package into the repository (RPMs signed first). Returns its new path."""
    if path.name.endswith(".deb"):
        POOL.mkdir(parents=True, exist_ok=True)
        dest = POOL / path.name
    elif path.name.endswith(".rpm"):
        run(["rpmsign", "--addsign", "--define", f"_gpg_name {KEY}", str(path)],
            stdout=subprocess.DEVNULL)
        RPM.mkdir(parents=True, exist_ok=True)
        dest = RPM / path.name
    else:
        raise RuntimeError(f"{path.name}: neither .deb nor .rpm")
    tmp = dest.with_name("." + dest.name + ".part")
    shutil.copyfile(path, tmp)
    os.chmod(tmp, 0o644)
    os.replace(tmp, dest)
    log("added", dest.relative_to(ROOT))
    return dest


def write(path, data):
    tmp = path.with_name("." + path.name + ".part")
    tmp.write_bytes(data)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def publish():
    """Rebuild APT and RPM metadata from the packages in the repository."""
    POOL.mkdir(parents=True, exist_ok=True)
    RPM.mkdir(parents=True, exist_ok=True)
    dists = APT / "dists" / "stable"
    packages = run(["apt-ftparchive", "packages", "pool/main"], cwd=APT, capture_output=True).stdout
    for arch in ARCHES:
        d = dists / "main" / f"binary-{arch}"
        d.mkdir(parents=True, exist_ok=True)
        write(d / "Packages", packages)
        write(d / "Packages.gz", run(["gzip", "-9n"], input=packages, capture_output=True).stdout)
        write(d / "Packages.xz", run(["xz", "-9"], input=packages, capture_output=True).stdout)
    for name in ("Release", "InRelease", "Release.gpg"):
        (dists / name).unlink(missing_ok=True)
    release = run(["apt-ftparchive",
                   "-o", "APT::FTPArchive::Release::Origin=Azentrius",
                   "-o", "APT::FTPArchive::Release::Label=Azentrius",
                   "-o", "APT::FTPArchive::Release::Suite=stable",
                   "-o", "APT::FTPArchive::Release::Codename=stable",
                   "-o", "APT::FTPArchive::Release::Components=main",
                   "-o", "APT::FTPArchive::Release::Architectures=" + " ".join(ARCHES),
                   "-o", "APT::FTPArchive::Release::Description=Azentrius Cockpit add-ons",
                   "release", "."], cwd=dists, capture_output=True).stdout
    write(dists / "Release", release)
    gpg = ["gpg", "--batch", "--yes", "--local-user", KEY, "--digest-algo", "SHA512"]
    write(dists / "InRelease", run(gpg + ["--clearsign"], input=release, capture_output=True).stdout)
    write(dists / "Release.gpg", run(gpg + ["--armor", "--detach-sign"], input=release,
                                     capture_output=True).stdout)
    run(["createrepo_c", "--quiet", "--update", str(RPM)])
    link_latest()
    log("published")


def latest(paths):
    """The path with the highest version; comparing the numbers is enough for X.Y.Z-1."""
    def key(p):
        version = p.name.split("_")[1] if p.suffix == ".deb" else p.name.rsplit("-", 2)[1]
        return [int(n) for n in re.findall(r"\d+", version)]
    return max(paths, key=key) if paths else None


def link_latest():
    """Stable names for the setup package: azentrius-repository.deb and .rpm in the root."""
    for found, name in ((latest(list(POOL.glob("azentrius-repository_*.deb"))), "azentrius-repository.deb"),
                        (latest(list(RPM.glob("azentrius-repository-*.rpm"))), "azentrius-repository.rpm")):
        if found:
            link = ROOT / name
            tmp = ROOT / ("." + name + ".part")
            tmp.unlink(missing_ok=True)
            tmp.symlink_to(found.relative_to(ROOT))
            os.replace(tmp, link)


def sync():
    seen_file = STATE / "seen.json"
    seen = set(json.loads(seen_file.read_text())) if seen_file.exists() else set()
    changed = False
    for repo in REPOS:
        for rel in json.loads(http(f"{API}/repos/{repo}/releases?per_page=30")):
            if rel["draft"] or rel["prerelease"]:
                continue
            assets = {a["name"]: a for a in rel["assets"]}
            new = [n for n in assets if n.endswith((".deb", ".rpm")) and f"{repo}/{rel['tag_name']}/{n}" not in seen]
            if not new:
                continue
            if "SHA256SUMS" not in assets:
                log(f"{repo} {rel['tag_name']}: no SHA256SUMS, skipped")
                continue
            sums = parse_sums(http(assets["SHA256SUMS"]["browser_download_url"], "*/*").decode())
            with tempfile.TemporaryDirectory(dir=STATE) as tmp:
                work = pathlib.Path(tmp)
                for name in new:
                    path = work / name
                    path.write_bytes(http(assets[name]["browser_download_url"], "*/*"))
                    digest = sha256(path)
                    reported = assets[name].get("digest")
                    if sums.get(name) != digest or (reported and reported != "sha256:" + digest):
                        log(f"{repo} {rel['tag_name']} {name}: checksum differs, skipped")
                        continue
                    try:
                        verify_attestation(repo, path, digest, work)
                    except (subprocess.CalledProcessError, RuntimeError) as e:
                        log(f"{repo} {rel['tag_name']} {name}: provenance not verified ({e}), skipped")
                        continue
                    add(path)
                    seen.add(f"{repo}/{rel['tag_name']}/{name}")
                    changed = True
            write(seen_file, json.dumps(sorted(seen), indent=1).encode())
    if changed or not (APT / "dists" / "stable" / "InRelease").exists():
        publish()
    else:
        log("nothing new")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync")
    sub.add_parser("publish")
    p_add = sub.add_parser("add")
    p_add.add_argument("files", nargs="+", type=pathlib.Path)
    args = parser.parse_args()

    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / "lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.cmd == "sync":
            sync()
        elif args.cmd == "publish":
            publish()
        else:
            with tempfile.TemporaryDirectory(dir=STATE) as tmp:
                for f in args.files:
                    copy = pathlib.Path(tmp) / f.name
                    shutil.copyfile(f, copy)
                    add(copy)
            publish()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f"failed: {' '.join(map(str, e.cmd))} (exit {e.returncode})")
