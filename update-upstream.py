#!/usr/bin/env python
import os
import pathlib
import shlex
import subprocess
import sys
import warnings

import tomllib


def _use_colors() -> bool:
    if 'NO_COLOR' in os.environ:
        if 'FORCE_COLOR' in os.environ:
            warnings.warn('Both NO_COLOR and FORCE_COLOR environment variables are set, disabling color', stacklevel=2)
        return False
    elif 'FORCE_COLOR' in os.environ or sys.stdout.isatty():
        return os.name != 'nt'
    return False


if _use_colors():
    dim = '\33[2m'
    yellow = '\33[93m'
    reset = '\33[0m'
else:
    dim = yellow = reset = ''


root = pathlib.Path(__file__).parent
submodule = root / 'subprojects' / 'pkgconf'

version_files = [
    root / 'pyproject.toml',
    root / 'meson.build',
    root / 'src' / 'pkgconf' / '__init__.py',
]


def git(*args: str, cwd: str | os.PathLike = submodule, capture: bool = False) -> subprocess.CompletedProcess:
    args = ['git', *args]
    print(dim + '$ ' + shlex.join(args) + reset)
    try:
        process = subprocess.run(args, cwd=cwd, capture_output=capture, text=True, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    if capture:
        if process.stdout:
            sys.stderr.write(process.stdout)
        if process.stderr:
            sys.stderr.write(process.stderr)
    return process


with root.joinpath('pyproject.toml').open('rb') as f:
    pyproject_data = tomllib.load(f)

downstream_version = pyproject_data['project']['version']
downstream_version_tuple = tuple(downstream_version.split('-')[0].split('.'))
print(f'{yellow}Current version: {downstream_version}{reset}')

# Get the latest upstream version
# subprocess.check_output(['git', 'fetch', 'origin', 'master'], cwd=submodule)
git('fetch', 'origin', 'master')
# upstream_latest_tag = subprocess.check_output(['git', 'describe', -'-tags', '--abbrev=0'], cwd=submodule)
upstream_latest_tag = git('describe', '--tags', '--abbrev=0', capture=True).stdout.strip()
upstream_version = upstream_latest_tag.removeprefix('pkgconf-')
upstream_version_tuple = tuple(upstream_version.split('.'))


if upstream_version_tuple > downstream_version_tuple:
    print(f'{yellow}Found new upstream version: {upstream_version} (current: {downstream_version}){reset}')
    print(f'{yellow}Updating...{reset}')
    # subprocess.check_output(['git', 'checkout', upstream_latest_tag], cwd=submodule)
    git('checkout', upstream_latest_tag)
    new_downstream_version = f'{upstream_version}-0'
    print(f'{yellow}New version: {new_downstream_version}{reset}')
    for file in version_files:
        file.write_text(
            file.read_text().replace(
                f"'{downstream_version}'",
                f"'{new_downstream_version}'",
            )
        )
