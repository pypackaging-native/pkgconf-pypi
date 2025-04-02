import os
import re
import textwrap

import pytest


@pytest.mark.skipif(os.name == 'nt', reason='meson-python does not support bundling libraries in wheel on win32')
def test_diagnose(env, packages):
    env.install_from_path(packages / 'namespace', from_sdist=False)
    env.install_from_path(packages / 'register-pkg-config-path', from_sdist=False)

    output = env.run_interpreter('-m', 'pkgconf.diagnose').decode()

    expected = textwrap.dedent(f"""
        pkgconf executable: .*{os.path.sep}pkgconf
        entrypoints:
          namespace:
            value: namespace
             path: .*{os.path.sep}namespace
          register-pkg-config-path:
            value: register_pkg_config_path.pkgconf
             path: .*{os.path.sep}register_pkg_config_path{os.path.sep}pkgconf
        PKG_CONFIG_PATH: .*{os.path.sep}namespace:.*{os.path.sep}register_pkg_config_path{os.path.sep}pkgconf
    """).strip()

    assert re.match(expected, output), output
