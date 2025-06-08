# pkgconf-pypi

[![CI test](https://github.com/pypackaging-native/pkgconf-pypi/actions/workflows/test.yml/badge.svg)](https://github.com/pypackaging-native/pkgconf-pypi/actions/workflows/test.yml)
[![CI build](https://github.com/pypackaging-native/pkgconf-pypi/actions/workflows/build.yml/badge.svg)](https://github.com/pypackaging-native/pkgconf-pypi/actions/workflows/build.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/pypackaging-native/pkgconf-pypi/main.svg)](https://results.pre-commit.ci/latest/github/pypackaging-native/pkgconf-pypi/main)
[![codecov](https://codecov.io/gh/pypackaging-native/pkgconf-pypi/graph/badge.svg)](https://codecov.io/gh/pypackaging-native/pkgconf-pypi)

[![Documentation Status](https://readthedocs.org/projects/pkgconf-pypi/badge/?version=latest)](https://pkgconf-pypi.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/pkgconf.svg)](https://pypi.org/project/pkgconf/)
[![Discord](https://img.shields.io/discord/803025117553754132?label=Discord%20chat%20pkgconf-pypi)](https://discord.gg/pypa)

This goal of this repo is to facilitate building and publishing of
[pkgconf](https://github.com/pkgconf/pkgconf) binaries on PyPI, primarily for
ease of installing in a cross-platform manner. This is useful when `pkgconf` is
for example needed in workflows of other Python packages.

## Choices

The intent is to:

- distribute `pkgconf` without any modifications
- configure the build with no system directory
- install `pkg-config` as an alias in the scripts directory of the Python
  environment

## Links

Documentation: https://pkgconf-pypi.readthedocs.io
