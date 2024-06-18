import os
import sys

import pkgconf


if sys.version_info >= (3, 10):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


def report() -> None:
    print(f'pkgconf executable: {pkgconf.get_executable()}')

    entrypoints = importlib_metadata.entry_points(group='pkg_config')
    print('entrypoints:')
    for entry in entrypoints:
        paths_str = ', '.join(pkgconf._get_module_paths(entry.value))
        print(f'  {entry.name}:')
        print(f'    value: {entry.value}')
        print(f'    paths: {paths_str}')

    print(f'PKG_CONFIG_PATH: {os.pathsep.join(pkgconf.get_pkg_config_path())}')


if __name__ == '__main__':
    try:
        report()
    except (KeyboardInterrupt, BrokenPipeError):  # pragma: no cover
        pass
