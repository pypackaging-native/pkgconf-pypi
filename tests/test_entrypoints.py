import os
import shutil
import subprocess
import sys

import pytest

import pkgconf
import pkgconf.__main__


@pytest.mark.parametrize('name', ['pkgconf', 'pkg-config'])
def test_entries(env, name):
    # TODO: Check PKG_CONFIG_PATH is correctly set
    path = shutil.which(name, path=env.scripts)
    help_text = subprocess.check_output([os.fspath(path), '--help'])
    assert help_text.decode().startswith('usage: pkgconf')


def test_fallback(mocker, monkeypatch):
    """Test that we fallback to the system pkgconf if ours fails."""
    mocker.patch('pkgconf.run_pkgconf', side_effect=subprocess.CalledProcessError(1, '(cmd)'))
    mocker.patch('subprocess.run')

    mocker.patch('shutil.which', return_value='(pkgconf-path)')

    args = ['--libs', 'py-test-inexistent']
    monkeypatch.setattr(sys, 'argv', ['(argv0)', *args])

    pkgconf.__main__.main()

    subprocess.run.assert_called_with(['(pkgconf-path)', *args])


def test_main(env):
    output = env.run_interpreter('-m', 'pkgconf', '--help')
    assert output.decode().startswith('usage: pkgconf')
