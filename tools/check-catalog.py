#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Checks the AppStream catalog the way Cockpit reads it (pkg/apps/watch-appstream.py):
a <components> root with an origin, and per component an id, a pkgname, a cockpit-manifest
launchable, a name and a summary. IDs and package names must be unique.

    python3 tools/check-catalog.py repository/azentrius.xml
"""
import sys
import xml.etree.ElementTree as ET

LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def main(path):
    root = ET.parse(path).getroot()
    errors = []
    if root.tag != "components" or not root.get("origin"):
        errors.append("root must be <components origin=…>")
    ids, pkgs = set(), set()
    for comp in root.iter("component"):
        cid = comp.findtext("id")
        where = cid or "component without id"
        if comp.get("type") != "addon":
            errors.append(f"{where}: type must be addon")
        for tag in ("id", "pkgname", "name", "summary"):
            if not [e for e in comp.findall(tag) if LANG not in e.attrib and (e.text or "").strip()]:
                errors.append(f"{where}: no <{tag}> without xml:lang")
        if comp.findtext("extends") != "org.cockpit_project.cockpit":
            errors.append(f"{where}: must extend org.cockpit_project.cockpit")
        if not [e for e in comp.findall("launchable") if e.get("type") == "cockpit-manifest" and e.text]:
            errors.append(f"{where}: no cockpit-manifest launchable")
        if cid in ids:
            errors.append(f"{where}: id twice")
        ids.add(cid)
        pkg = comp.findtext("pkgname")
        if pkg in pkgs:
            errors.append(f"{where}: pkgname {pkg} twice")
        pkgs.add(pkg)
    if not ids:
        errors.append("no components")
    for e in errors:
        print(e)
    if errors:
        sys.exit(1)
    print(f"catalog ok: {', '.join(sorted(pkgs))}")


if __name__ == "__main__":
    main(sys.argv[1])
