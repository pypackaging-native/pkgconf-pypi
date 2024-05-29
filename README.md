# pkgconf-pypi

This goal of this repo is to facility building and publishing of
[pkgconf](https://github.com/pkgconf/pkgconf) binaries on PyPI, primarily for
ease of installing in a cross-platform manner. This is useful when `pkgconf` is
for example needed in workflows of other Python packages.

## Choices

The intent is to:

- distribute `pkgconf` without any modifications
- configure the build with no system directory
- install `pkg-config` as an alias in the scripts directory of the Python
  environment
