import json
import os
import subprocess
import textwrap

import environment_helpers


def run(env: environment_helpers.Environment, expression: str, setup: str = '') -> str:
    script = textwrap.dedent(f"""
    import json
    import os
    import sys

    import pkgconf

    {setup}
    data = {expression}

    json.dump(obj=data, fp=sys.stdout)
    """)
    data = env.run_interpreter('-c', script)
    return json.loads(data)


def test_valid_executable(env):
    executable = run(env, 'os.fspath(pkgconf.get_executable())')

    help_text = subprocess.check_output([executable, '--help']).decode()
    assert help_text.startswith('usage: pkgconf')


def test_pkg_config_path(env, packages):
    path = run(env, 'list(pkgconf.get_pkg_config_path())')
    assert len(path) == 0

    env.install_from_path(packages / 'register-pkg-config-path', from_sdist=False)

    path = run(env, 'list(pkgconf.get_pkg_config_path())')
    assert list(path) == [os.path.join(env.scheme['purelib'], 'example', 'pkgconf')]
