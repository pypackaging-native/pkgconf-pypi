import importlib.metadata
import importlib.resources
import os
import pathlib

from collections.abc import Sequence


_distribution = importlib.metadata.distribution(__package__)
_distribution_name = f'{_distribution.name}-{_distribution.version}'


def _iter_records(path: importlib.metadata.SimplePath) -> pathlib.Path:
    for line in path.read_text().splitlines():
        entry = line.split(',')[0]
        abspath = os.path.abspath(os.path.join(path, '..', '..', entry))
        yield pathlib.Path(abspath)


def get_executable() -> pathlib.Path:
    """Get the pkgconf executable."""
    if os.name == 'posix':
        executable_name = 'pkgconf'
    else:
        raise NotImplementedError
    # Try looking in .dist-info, in case .data/scripts got installed to the scripts location
    record_file = _distribution.locate_file(f'{_distribution_name}.dist-info/RECORD')
    if record_file.exists():
        for record in _iter_records(record_file):
            if record.name == executable_name:
                return record
    # Try looking in .data/scripts, in case it was kept in-place
    path = _distribution.locate_file(f'{_distribution_name}.data/scripts/{executable_name}')
    if path.exists():
        return pathlib.Path(path)
    raise ValueError('Could not find the pkgconf executable.')


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

