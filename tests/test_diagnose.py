import os
import re
import textwrap


def test_diagnose(env, packages):
    env.install_from_path(packages / 'namespace', from_sdist=False)
    env.install_from_path(packages / 'register-pkg-config-path', from_sdist=False)

    output = env.run_interpreter('-m', 'pkgconf.diagnose').decode()

    assert re.match(
        textwrap.dedent(f"""
            pkgconf executable: .*{os.path.sep}pkgconf
            entrypoints:
              namespace:
                value: namespace
                paths: .*{os.path.sep}namespace
              register-pkg-config-path:
                value: register_pkg_config_path.pkgconf
                paths: .*{os.path.sep}pkgconf
            PKG_CONFIG_PATH: .*{os.path.sep}namespace:.*{os.path.sep}register_pkg_config_path/pkgconf
        """).strip(),
        output,
    ), output
