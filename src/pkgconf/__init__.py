import importlib.metadata
import importlib.resources
import os
import pathlib
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
