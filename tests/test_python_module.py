import os
import pathlib
import subprocess

import pytest

import pkgconf


RUNNING_FROM_SOURCE = bool(any(not pathlib.Path(path, '.bin').exists() for path in pkgconf.__path__))


def test_valid_executable(env):
    executable = env.introspectable.call('pkgconf.get_executable')

    help_text = subprocess.check_output([os.fspath(executable), '--help']).decode()
    assert help_text.startswith('usage: pkgconf')


@pytest.mark.skipif(os.name == 'nt', reason='meson-python does not support bundling libraries in wheel on win32')
def test_pkg_config_path(env, packages):
    path = list(env.introspectable.call('pkgconf.get_pkg_config_path'))
    assert len(path) == 0

    env.install_from_path(packages / 'register-pkg-config-path', from_sdist=False)

    path = list(map(pathlib.Path, env.introspectable.call('pkgconf.get_pkg_config_path')))
    assert path == [pathlib.Path(env.scheme['purelib'], 'register_pkg_config_path', 'pkgconf')]


def test_pkg_config_path_namespace(env, packages):
    path = list(env.introspectable.call('pkgconf.get_pkg_config_path'))
    assert len(path) == 0

    env.install_from_path(packages / 'namespace', from_sdist=False)

    path = list(map(pathlib.Path, env.introspectable.call('pkgconf.get_pkg_config_path')))
    assert path == [pathlib.Path(env.scheme['purelib'], 'namespace')]


def test_pkg_config_path_error_on_import(env, packages):
    path = list(env.introspectable.call('pkgconf.get_pkg_config_path'))
    assert len(path) == 0

    env.install_from_path(packages / 'error-on-import', from_sdist=False)
    env_site_dir = pathlib.Path(env.scheme['purelib'])

    path = set(map(pathlib.Path, env.introspectable.call('pkgconf.get_pkg_config_path')))
    assert path == {env_site_dir / 'foo', env_site_dir / 'foo' / 'bar'}


def test_run_pkgconfig(env):
    output = env.introspectable.call('pkgconf.run_pkgconf', '--help', capture_output=True)
    assert output.stdout.decode().startswith('usage: pkgconf')


@pytest.mark.skipif(not RUNNING_FROM_SOURCE, reason='Not running from source')
@pytest.mark.filterwarnings('ignore:Bundled pkgconf not found, using the system executable')
def test_get_executable_none(mocker):
    mocker.patch('pkgconf._get_system_executable', return_value=None)

    with pytest.raises(RuntimeError, match='No pkgconf/pkg-config executable available'):
        pkgconf.get_executable()


@pytest.mark.skipif(not RUNNING_FROM_SOURCE, reason='Not running from source')
def test_get_executable_fallback_to_system(mocker):
    with pytest.warns(match='Bundled pkgconf not found, using the system executable'):
        executable = pkgconf.get_executable()

    assert executable == pkgconf._get_system_executable()
