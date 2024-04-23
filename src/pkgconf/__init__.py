import importlib.metadata
import importlib.resources
import os
import pathlib
import shutil
import sys
import sysconfig
import subprocess

from collections.abc import Sequence
from typing import Any


def get_executable() -> pathlib.Path:
    """Get the pkgconf executable."""
    if os.name == 'posix':
        executable_name = 'pkgconf'
    else:
        raise NotImplementedError
    return pathlib.Path(importlib.resources.files('pkgconf') / '.bin' / executable_name)


def get_pkg_config_path() -> Sequence[str]:
    """Calculate PKG_CONFIG_PATH for Python packages in the current environment.

    Python packages may register a directory for their pkg-config files by
    specifying a "pkg-config" entrypoint.

    TODO: Document the entrypoint creation and point to that here.
    [project.entry-points.pkg-config]
    entrypoint-name = 'project.package'
    """
    entrypoints = importlib.metadata.entry_points(group='pkg-config')
    return [
        os.fspath(importlib.resources.files(entry.value))
        for entry in entrypoints
    ]


def run_pkgconf(*args: str, **subprocess_kwargs: Any) -> subprocess.Popen:
    """Run the pkgconf executable.

    :param args: Arguments to pass to the pkgconf call.
    :param subprocess_kwargs: Keyword arguments to pass to the subprocess.run call.
    """
    env = os.environ.copy()
    env['PKG_CONFIG_PATH'] = os.pathsep.join((
        env.get('PKG_CONFIG_PATH', ''),
        *get_pkg_config_path(),
    ))
    return subprocess.run([get_executable(), *args], **subprocess_kwargs)


def _entrypoint() -> None:
    args = sys.argv[1:]
    try:
        run_pkgconf(*args, check=True)
    except subprocess.SubprocessError:
        # If our pkgconf lookup fails, fallback to the system pkgconf/pkg-config.
        # For simplicity, the previous call will output to stdout/stderr
        # regardless of its success, since capturing stdout/stderr in order to
        # replay is tricky. If the fallback path triggers, it will also output
        # to stdout/stderr, meaning we will have the output of both process
        # calls. While a bit unexpected, I believe this is the best option for
        # debugging.
        scripts = sysconfig.get_path('scripts')
        path_list = os.environ.get('PATH', os.defpath).split(os.pathsep)
        if scripts in path_list:
            path_list.remove(scripts)
        path = os.pathsep.join(path_list)
        system_executable = shutil.which('pkgconf', path=path) or shutil.which('pkg-config', path=path)
        if system_executable:
            subprocess.run([system_executable, *args])
