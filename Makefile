# Azentrius package repository
# SPDX-License-Identifier: Apache-2.0

VERSION := $(shell cat VERSION)
# Reproducible packages: file times from the last commit.
SOURCE_DATE_EPOCH ?= $(shell git log -1 --format=%ct 2>/dev/null || date +%s)

.PHONY: all check lint stage packages

all:
	@echo "Nothing to build. Try: make check, make lint, make packages"

# The catalog, the version and its changelog section, the server tool compiles.
check:
	python3 tools/check-catalog.py repository/azentrius.xml
	sh tools/check-version.sh
	python3 -m py_compile server/azentrius-packages.py

# As in CI (the tools: pip install -r test/requirements.txt).
lint:
	shellcheck --severity=warning tools/*.sh server/*.sh packaging/scripts/*
	ruff check .

# The files of azentrius-repository, as installed, in build/root.
stage:
	rm -rf build/root
	install -D -m 644 repository/azentrius.asc build/root/usr/share/keyrings/azentrius.asc
	install -D -m 644 repository/azentrius.xml build/root/usr/share/swcatalog/xml/azentrius.xml
	install -D -m 644 NOTICE build/root/usr/share/doc/azentrius-repository/copyright
	install -m 644 LICENSE build/root/usr/share/doc/azentrius-repository/LICENSE

# azentrius-repository_VERSION-1_all.deb and azentrius-repository-VERSION-1.noarch.rpm in dist/
# (needs dpkg-deb and rpmbuild), reproducible.
packages: stage
	SOURCE_DATE_EPOCH=$(SOURCE_DATE_EPOCH) sh tools/build-packages.sh build/root $(VERSION) dist
