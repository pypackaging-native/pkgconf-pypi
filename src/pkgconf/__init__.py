import logging
import operator
import os
import pathlib
import shlex
import shutil
import subprocess
import sys
import sysconfig
import warnings

from collections.abc import Sequence
from typing import Any, Optional


if sys.version_info >= (3, 10):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


__version__ = '2.4.3-2'


_LOGGER = logging.getLogger(__name__)


class PathWarning(Warning):
    def __init__(self, message: str, entrypoint: importlib_metadata.EntryPoint) -> None:
        self._message = message
        self._entrypoint = entrypoint

    def __str__(self) -> str:
        return (
            f'Skipping PKG_CONFIG_PATH entry: {self._message}'
            f'- Entrypoint: {self._entrypoint}'
            f'- Distribution: {self._distribution_info()}'
        )

    def _distribution_info(self) -> str:
        info = f'{self._entrypoint.dist}-{self._entrypoint.dist.version}'
        metadata_path = self._find_metadata_path()
        if metadata_path:
            info += f' at {metadata_path!r}'
        return info

    def _find_metadata_path(self) -> Optional[str]:
        try:
            dist_root = self._entrypoint.dist.locate_file('')
        except NotImplementedError:
            return None

        for file in self._entrypoint.dist.files() or []:
            if file.parts[0].endswith('.dist-info'):
                return str(dist_root / file.parts[0])
        return None


def _get_system_executable() -> Optional[pathlib.Path]:
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


def _find_entrypoints() -> Sequence[importlib_metadata.EntryPoint]:
    """Return the list of pkg_config entrypoints sorted by name."""
    entrypoints = importlib_metadata.entry_points(group='pkg_config')
    return sorted(entrypoints, key=operator.attrgetter('name'))


def _resolve_entrypoint_path(entrypoint: importlib_metadata.EntryPoint) -> str:
    """Return a filesystem path for module specified in the entrypoint.

    XXX: This only considers files provided by the distribution that registered the entrypoint.
    """
    assert entrypoint.dist
    subpath = pathlib.PurePath(*entrypoint.value.split('.'))
    try:
        module_path = entrypoint.dist.locate_file(subpath).resolve()
    except NotImplementedError:
        warnings.warn(
            PathWarning(
                'Unable to resolve the file-system path for the entrypoint, '
                f"as {entrypoint.dist} doesn't implement locate_file()"
            ),
            stacklevel=2,
        )
    return os.fspath(module_path)


def get_pkg_config_path() -> Sequence[str]:
    """Calculate PKG_CONFIG_PATH for Python packages in the current environment.

    Python packages may register a directory for their pkg-config files by
    specifying a "pkg-config" entrypoint.

    TODO: Document the entrypoint creation and point to that here.
    [project.entry-points.pkg-config]
    entrypoint-name = 'project.package'
    """
    return [_resolve_entrypoint_path(ep) for ep in _find_entrypoints()]


def run_pkgconf(*args: str, **subprocess_kwargs: Any) -> subprocess.CompletedProcess:
    """Run the pkgconf executable.

    :param args: Arguments to pass to the pkgconf call.
    :param subprocess_kwargs: Keyword arguments to pass to the subprocess.run call.
    """
    env = os.environ.copy()
    PKG_CONFIG_PATH = env.get('PKG_CONFIG_PATH', '').split(os.pathsep) + get_pkg_config_path()
    PKG_CONFIG_PATH = list(dict.fromkeys(PKG_CONFIG_PATH))  # Remove duplicated entried
    env['PKG_CONFIG_PATH'] = os.pathsep.join(PKG_CONFIG_PATH)
    cmd = [os.fspath(get_executable()), *args]
    _LOGGER.info('Running the Python pkgconf')
    _LOGGER.info('$ ' + shlex.join(('PKG_CONFIG_PATH=' + shlex.quote(env['PKG_CONFIG_PATH']), *cmd)))
    return subprocess.run(cmd, env=env, **subprocess_kwargs)
