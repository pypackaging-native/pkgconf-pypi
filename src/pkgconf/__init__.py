import importlib.metadata
import importlib.resources
import os
import pathlib

from collections.abc import Sequence


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

