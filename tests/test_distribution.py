import os
import zipfile

import environment_helpers.build
import pytest


@pytest.mark.order('first')
def test_build(root, tmp_path):
    environment_helpers.build.build_wheel_via_sdist(root, tmp_path)


def test_single_pkgconfig_in_wheel_contents(self_wheel):
    """pkgconf.get_executable() makes an assumption we are only installing one file named 'pkgconf'"""
    if os.name == 'posix':
        executable_name = 'pkgconf'
    elif os.name == 'nt':
        executable_name = 'pkgconf.exe'
    else:
        raise NotImplementedError

    wheel = zipfile.ZipFile(self_wheel)
    pkgconf_entries = [entry for entry in wheel.namelist() if entry.split('/')[-1].lower() == executable_name]
    assert len(pkgconf_entries) == 1
