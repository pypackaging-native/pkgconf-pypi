import importlib
import itertools
import logging
import os
import pathlib
import shutil
import subprocess
import sys
import sysconfig
import warnings

from typing import Any, Optional


if sys.version_info >= (3, 9):
    from collections.abc import Sequence
else:
    from typing import Sequence


if sys.version_info >= (3, 10):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


__version__ = '2.1.1-8'


_LOGGER = logging.getLogger(__name__)


def _get_system_executable() -> Optional[pathlib.Path]:
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


def _get_module_paths(name: str) -> Sequence[str]:
    module = importlib.import_module(name)
    if isinstance(module.__path__, list) or 'NamespacePath' in module.__path__.__class__.__name__:
        return list(module.__path__)
    assert isinstance(module.__path__, str), module.__path__
    return [module.__path__]


def get_pkg_config_path() -> Sequence[str]:
    """Calculate PKG_CONFIG_PATH for Python packages in the current environment.

    Python packages may register a directory for their pkg-config files by
    specifying a "pkg-config" entrypoint.

    TODO: Document the entrypoint creation and point to that here.
    [project.entry-points.pkg-config]
    entrypoint-name = 'project.package'
    """
    entrypoints = importlib_metadata.entry_points(group='pkg_config')
    return itertools.chain.from_iterable([_get_module_paths(entry.value) for entry in entrypoints])


def run_pkgconf(*args: str, **subprocess_kwargs: Any) -> subprocess.Popen:
    """Run the pkgconf executable.

    :param args: Arguments to pass to the pkgconf call.
    :param subprocess_kwargs: Keyword arguments to pass to the subprocess.run call.
    """
    env = os.environ.copy()
    env['PKG_CONFIG_PATH'] = os.pathsep.join(
        (
            env.get('PKG_CONFIG_PATH', ''),
            *get_pkg_config_path(),
        )
    )
    cmd = [os.fspath(get_executable()), *args]
    _LOGGER.info('Running the Python pkgconf')
    _LOGGER.info('$ PKG_CONFIG_PATH=' + env['PKG_CONFIG_PATH'] + ' ' + ' '.join(cmd))
    return subprocess.run(cmd, env=env, **subprocess_kwargs)
