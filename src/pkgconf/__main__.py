import logging
import os
import subprocess
import sys
import warnings

from typing import Optional, TextIO, Type, Union

import pkgconf


_LOGGER = logging.getLogger(__name__)


def main() -> None:
    args = sys.argv[1:]

    # If we find that we are calling ourselves, exit immediately
    if os.environ.get('PKGCONF_PYPI_RECURSIVE') == __file__:
        _LOGGER.info('Giving up, pkgconf recursion loop detected')
        sys.exit(1)

    os.environ['PKGCONF_PYPI_RECURSIVE'] = __file__
    exit_code = 1
    try:
        proc = pkgconf.run_pkgconf(*args, check=True)
    except subprocess.SubprocessError:
        # If our pkgconf lookup fails, fallback to the system pkgconf/pkg-config.
        # For simplicity, the previous call will output to stdout/stderr
        # regardless of its success, since capturing stdout/stderr in order to
        # replay is tricky. If the fallback path triggers, it will also output
        # to stdout/stderr, meaning we will have the output of both process
        # calls. While a bit unexpected, I believe this is the best option for
        # debugging.
        system_executable = pkgconf._get_system_executable()
        if system_executable:
            cmd = [os.fspath(system_executable), *args]
            _LOGGER.info(f'Running the system {system_executable.name}')
            _LOGGER.info('$ ' + ' '.join(cmd))
            proc = subprocess.run(cmd)

    sys.exit(proc.returncode)


def _use_colors() -> bool:
    if 'NO_COLOR' in os.environ:
        if 'FORCE_COLOR' in os.environ:
            warnings.warn('Both NO_COLOR and FORCE_COLOR environment variables are set, disabling color', stacklevel=2)
        return False
    elif 'FORCE_COLOR' in os.environ or sys.stdout.isatty():
        if os.name == 'nt':
            try:
                import colorama
            except ModuleNotFoundError:
                return False
            colorama.init()
        return True
    return False


def _setup_cli():
    if _use_colors():
        dim = '\33[2m'
        yellow = '\33[93m'
        reset = '\33[0m'
    else:
        dim = yellow = reset = ''

    logging.basicConfig(
        stream=sys.stderr,
        format=f'{dim}> %(message)s{reset}',
        level=logging.INFO,
    )

    def _showwarning(
        message: Union[Warning, str],
        category: Type[Warning],
        filename: str,
        lineno: int,
        file: Optional[TextIO] = None,
        line: Optional[str] = None,
    ) -> None:  # pragma: no cover
        print(f'{yellow}WARNING{reset} {message}', file=sys.stderr)

    warnings.showwarning = _showwarning


def _entrypoint():
    _setup_cli()
    main()


if __name__ == '__main__':
    _entrypoint()
