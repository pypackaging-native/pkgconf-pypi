import logging
import os
import pathlib
import shlex
import shutil
import subprocess
import sysconfig
import warnings

from typing import Any

import pkgconf._path_entrypoints

from pkgconf._path_entrypoints import PathWarning


__version__ = '2.5.1-0'


_LOGGER = logging.getLogger(__name__)
_CLI_LOGGER = _LOGGER.getChild('cli')


def _get_system_executable() -> pathlib.Path | None:
    if os.environ.get('PKGCONF_PYPI_EMBEDDED_ONLY'):
        return None

    scripts = sysconfig.get_path('scripts')
    path_list = os.environ.get('PATH', os.defpath).split(os.pathsep)
    if scripts in path_list:
        path_list.remove(scripts)
    path = os.pathsep.join(path_list)

    executable = shutil.which('pkgconf', path=path) or shutil.which('pkg-config', path=path)
    if executable:
        return pathlib.Path(executable)
    return None


def get_executable() -> pathlib.Path:
    """Get the pkgconf executable."""
    executable: pathlib.Path | None

    if os.name == 'posix':
        executable_name = 'pkgconf'
    elif os.name == 'nt':
        executable_name = 'pkgconf.EXE'
    else:
        raise NotImplementedError

    for path in __path__:
        executable = pathlib.Path(path) / '.bin' / executable_name
        if executable.exists():
            return executable

    warnings.warn('Bundled pkgconf not found, using the system executable', stacklevel=2)
    executable = _get_system_executable()
    if executable:
        return executable

    msg = 'No pkgconf/pkg-config executable available'
    raise RuntimeError(msg)


def _entry_points() -> list[pkgconf._path_entrypoints.EntryPoint]:
    return pkgconf._path_entrypoints.entry_points(group='pkg_config')


def get_pkg_config_path() -> list[str]:
    """Calculate PKG_CONFIG_PATH for Python packages in the current environment.

    Python packages may register a directory for their pkg-config files by
    specifying a "pkg-config" entrypoint.

    TODO: Document the entrypoint creation and point to that here.
    [project.entry-points.pkg-config]
    entrypoint-name = 'project.package'
    """
    return [ep.path for ep in _entry_points()]


def run_pkgconf(*args: str, **subprocess_kwargs: Any) -> subprocess.CompletedProcess[bytes | str]:
    """Run the pkgconf executable.

    :param args: Arguments to pass to the pkgconf call.
    :param subprocess_kwargs: Keyword arguments to pass to the subprocess.run call.
    """
    env = os.environ.copy()
    PKG_CONFIG_PATH = env.get('PKG_CONFIG_PATH', '').split(os.pathsep) + get_pkg_config_path()
    PKG_CONFIG_PATH = list(dict.fromkeys(PKG_CONFIG_PATH))  # Remove duplicated entried
    env['PKG_CONFIG_PATH'] = os.pathsep.join(PKG_CONFIG_PATH)
    cmd = [os.fspath(get_executable()), *args]
    _CLI_LOGGER.info('Running the Python pkgconf')
    _CLI_LOGGER.info('$ ' + shlex.join(('PKG_CONFIG_PATH=' + shlex.quote(env['PKG_CONFIG_PATH']), *cmd)))
    return subprocess.run(cmd, env=env, **subprocess_kwargs)


__all__ = [
    'PathWarning',
    'get_executable',
    'get_pkg_config_path',
    'run_pkgconf',
]
