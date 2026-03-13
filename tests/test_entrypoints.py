import os
import re
import subprocess
import sys

import pytest

import pkgconf
import pkgconf.__main__


@pytest.mark.parametrize('name', ['pkgconf', 'pkg-config', 'pkgconf-pypi'])
def test_entries(env, name):
    # TODO: Check PKG_CONFIG_PATH is correctly set
    help_text = env.run_script('pkgconf', '--help')
    assert help_text.decode().startswith('usage: pkgconf')


def test_pkgconf_pypi_fallback(mocker, monkeypatch):
    """Test that we fallback to the system pkgconf if ours fails."""
    mocker.patch('pkgconf.run_pkgconf', side_effect=subprocess.CalledProcessError(1, '(cmd)'))
    mocker.patch('subprocess.run', return_value=subprocess.CompletedProcess(['(cmd)'], 0))
    mocker.patch('sys.exit')

    mocker.patch('shutil.which', return_value='(pkgconf-path)')

    args = ['--libs', 'py-test-inexistent']
    monkeypatch.setattr(sys, 'argv', ['(argv0)', *args])

    pkgconf.__main__.main()

    subprocess.run.assert_called_with(['(pkgconf-path)', *args])
    sys.exit.assert_called_with(0)


def test_pkgconf_pypi_no_fallback(mocker, monkeypatch):
    """Test that we don't fail if there's no system pkgconf and ours fails."""
    mocker.patch('pkgconf.run_pkgconf', side_effect=subprocess.CalledProcessError(1, '(cmd)'))
    mocker.patch('subprocess.run', return_value=subprocess.CompletedProcess(['(cmd)'], 0))
    mocker.patch('sys.exit')

    mocker.patch('shutil.which', return_value=None)

    args = ['--libs', 'py-test-inexistent']
    monkeypatch.setattr(sys, 'argv', ['(argv0)', *args])

    pkgconf.__main__.main()

    sys.exit.assert_called_with(1)


def test_pkgconf_pypi_venv_redirect(mocker, monkeypatch):
    mocker.patch('subprocess.run', return_value=subprocess.CompletedProcess(['(cmd)'], 0))
    mocker.patch('sys.exit')

    monkeypatch.setenv('VIRTUAL_ENV', '(venv)')

    args = ['--libs', 'py-test-inexistent']
    monkeypatch.setattr(sys, 'argv', ['(argv0)', *args])

    pkgconf.__main__._python_aware_entrypoint()

    assert subprocess.run.call_args.args[0][1:] == ['-m', 'pkgconf', *args]
    sys.exit.assert_called_with(0)


def test_pkgconf_pypi_venv_system_site_packages(container):
    # Install pkgconf in the global site-packages
    status, out = container.exec_run(['pip', 'install', '/project'])
    assert status == 0, out

    # Create a venv with --system-site-packages
    status, out = container.exec_run(['python', '-m', 'venv', '--system-site-packages', '/venv'])
    assert status == 0, out

    # Install a project that registers a pkg-config path in the venv
    status, out = container.exec_run(['/venv/bin/pip', 'install', '/packages/register-pkg-config-path'])
    assert status == 0, out

    # Run pkg-config with VIRTUAL_ENV set
    status, out = container.exec_run(
        ['pkgconf-pypi', '--cflags', 'register_pkg_config_path'],
        environment={'VIRTUAL_ENV': '/venv'},
        stderr=False,
    )
    assert status == 0, out
    assert re.match(rb'.*\-I/venv/lib/python.*/site-packages/register_pkg_config_path/pkgconf/../include'.strip(), out), out


def test_main(env):
    output = env.run_interpreter('-m', 'pkgconf', '--help')
    assert output.decode().startswith('usage: pkgconf')


def test_vanilla_warn(env, packages):
    p = subprocess.run(
        ['pkgconf', '--cflags', 'foo'],
        capture_output=True,
        text=True,
        env=env.env,
    )
    assert p.returncode == 1
    assert 'PKG_CONFIG_PATH not specified, and the system is unavailable!' in p.stderr


@pytest.mark.skipif(os.name == 'nt', reason='meson-python does not support bundling libraries in wheel on win32')
def test_vanilla_force(env, packages):
    env.install_from_path(packages / 'register-pkg-config-path', from_sdist=False)

    p = subprocess.run(
        ['pkgconf', '--cflags', 'register_pkg_config_path'],
        capture_output=True,
        text=True,
        env=env.env,
    )
    assert p.returncode == 1
    assert 'Package register_pkg_config_path was not found in the pkg-config search path.' in p.stderr

    p = subprocess.run(
        ['pkgconf', '--cflags', 'register_pkg_config_path'],
        capture_output=True,
        text=True,
        env=env.env | {'FORCE_PKGCONF_PYPI': ''},
    )
    assert p.returncode == 0
    assert p.stdout.startswith('-I')
