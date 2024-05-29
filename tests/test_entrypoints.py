import os
import shutil
import subprocess
import sys

import pytest

import pkgconf


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

    pkgconf._entrypoint()

    subprocess.run.assert_called_with(['(pkgconf-path)', *args])
