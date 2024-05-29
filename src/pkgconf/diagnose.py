import importlib.metadata
import importlib.resources
import os

import pkgconf


def report() -> None:
    print(f'pkgconf executable: {pkgconf.get_executable()}')

    entrypoints = importlib.metadata.entry_points(group='pkg-config')
    print('entrypoints:')
    for entry in entrypoints:
        print(f'  {entry.name}:')
        print(f'    value: {entry.value}')
        print(f'    path: {os.fspath(importlib.resources.files(entry.value))}')

    print(f'PKG_CONFIG_PATH: {os.pathsep.join(pkgconf.get_pkg_config_path())}')


if __name__ == '__main__':
    try:
        report()
    except (KeyboardInterrupt, BrokenPipeError):
        pass
