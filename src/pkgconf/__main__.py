import logging
import os
import shlex
import subprocess
import sys
import sysconfig
import warnings

from typing import TextIO

import pkgconf


_LOGGER = logging.getLogger(__name__)


def main() -> None:
    args = sys.argv[1:]

    # If we find that we are calling ourselves, exit immediately
    if os.environ.get('PKGCONF_PYPI_RECURSIVE') == __file__:
        _LOGGER.info('Giving up, pkgconf recursion loop detected')
        sys.exit(1)

    os.environ['PKGCONF_PYPI_RECURSIVE'] = __file__
    returncode = 1
    try:
        returncode = pkgconf.run_pkgconf(*args, check=True).returncode
    except subprocess.SubprocessError as e:
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
            _LOGGER.info('$ ' + shlex.join(cmd))
            returncode = subprocess.run(cmd).returncode
        elif isinstance(e, subprocess.CalledProcessError):
            returncode = e.returncode

    sys.exit(returncode)


def _venv_paths(config_vars: dict[str, str]) -> str:
    if 'venv' in sysconfig.get_scheme_names():
        return sysconfig.get_paths('venv', vars=config_vars)
    return sysconfig.get_paths(vars=config_vars)


def _entrypoint():
    # Since project.script entrypoints use an hardcoded interpreter path from
    # the environment they were installed in, when stacking environments (eg.
    # using venv's --system-site-packages option), the entrypoint will run in
    # the base environment and, as such, it will not have access to the
    # entrypoints from the "child" environment. Because of this, when a virtual
    # environment is enabled, instead of running main() from this process, we
    # will run 'python -m pkgconf', so that we have access to the full
    # environment.
    if 'VIRTUAL_ENV' in os.environ:
        venv_vars = sysconfig.get_config_vars().copy()
        venv_vars['base'] = venv_vars['platbase'] = os.environ['VIRTUAL_ENV']
        scripts = _venv_paths(venv_vars)['scripts']
        python_path = os.path.join(scripts, 'python')
        process = subprocess.run([python_path, '-m', 'pkgconf', *sys.argv[1:]])
        sys.exit(process.returncode)
    else:
        _setup_cli()
        main()


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
        format=f'{dim}> %(message)s{reset} [%(levelname)s:%(name)s]',
    )
    pkgconf._CLI_LOGGER.setLevel(logging.INFO)

    def _showwarning(
        message: Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: TextIO | None = None,
        line: str | None = None,
    ) -> None:  # pragma: no cover
        print(f'{yellow}WARNING{reset} {message}', file=sys.stderr)

    warnings.showwarning = _showwarning


if __name__ == '__main__':
    _setup_cli()
    main()
