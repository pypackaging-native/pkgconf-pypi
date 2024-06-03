import importlib.metadata
import os

import pkgconf


def report() -> None:
    print(f'pkgconf executable: {pkgconf.get_executable()}')

    entrypoints = importlib.metadata.entry_points(group='pkg_config')
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
    except (KeyboardInterrupt, BrokenPipeError):
        pass
