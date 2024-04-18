import os
import shutil
import subprocess

import pytest


@pytest.mark.parametrize('name', ['pkgconf', 'pkg-config'])
def test_entries(env, name):
    # TODO: Check PKG_CONFIG_PATH is correctly set
    path = shutil.which(name, path=env.scripts)
    help_text = subprocess.check_output([os.fspath(path), '--help'])
    assert help_text.decode().startswith('usage: pkgconf')
