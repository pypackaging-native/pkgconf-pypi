import os
import subprocess


def test_valid_executable(env):
    executable = env.introspectable.call('pkgconf.get_executable')

    help_text = subprocess.check_output([os.fspath(executable), '--help']).decode()
    assert help_text.startswith('usage: pkgconf')


def test_pkg_config_path(env, packages):
    path = list(env.introspectable.call('pkgconf.get_pkg_config_path'))
    assert len(path) == 0

    env.install_from_path(packages / 'register-pkg-config-path', from_sdist=False)

    path = list(env.introspectable.call('pkgconf.get_pkg_config_path'))
    assert list(path) == [os.path.join(env.scheme['purelib'], 'example', 'pkgconf')]


def test_pkg_config_path_namespace(env, packages):
    path = list(env.introspectable.call('pkgconf.get_pkg_config_path'))
    assert len(path) == 0

    env.install_from_path(packages / 'namespace', from_sdist=False)

    path = list(env.introspectable.call('pkgconf.get_pkg_config_path'))
    assert list(path) == [os.path.join(env.scheme['purelib'], 'example')]


def test_run_pkgconfig(env):
    output = env.introspectable.call('pkgconf.run_pkgconf', '--help', capture_output=True)
    assert output.stdout.decode().startswith('usage: pkgconf')
