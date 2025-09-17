import os

import pkgconf


def report() -> None:
    print(f'pkgconf executable: {pkgconf.get_executable()}')

    print('entrypoints:')
    for entrypoint in pkgconf._entry_points():
        print(f'  {entrypoint.name}:')
        print(f'    value: {entrypoint.value}')
        print(f'     path: {entrypoint.path}')

    print(f'PKG_CONFIG_PATH: {os.pathsep.join(pkgconf.get_pkg_config_path())}')


if __name__ == '__main__':
    try:
        report()
    except (KeyboardInterrupt, BrokenPipeError):  # pragma: no cover
        pass
