import os
import pathlib
import shutil
import subprocess
import sys

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

    path = [pathlib.Path(p).resolve() for p in env.introspectable.call('pkgconf.get_pkg_config_path')]
    assert path == [pathlib.Path(env.scheme['purelib'], 'register_pkg_config_path', 'pkgconf').resolve()]


def test_pkg_config_path_namespace(env, packages):
    path = list(env.introspectable.call('pkgconf.get_pkg_config_path'))
    assert len(path) == 0

    env.install_from_path(packages / 'namespace', from_sdist=False)

    path = [pathlib.Path(p).resolve() for p in env.introspectable.call('pkgconf.get_pkg_config_path')]
    assert path == [pathlib.Path(env.scheme['purelib'], 'namespace').resolve()]


@pytest.mark.parametrize('first', ['primary', 'secondary'])
@pytest.mark.parametrize(
    'isolation',
    [
        'subprocess',
        pytest.param(
            'subinterpreter',
            marks=pytest.mark.skipif(sys.version_info < (3, 14), reason='subinterpreters require Python 3.14+'),
        ),
    ],
)
def test_pkg_config_path_namespace_multiple_locations(env, packages, tmp_path, first, isolation):
    dst = tmp_path / 'namespace-pkgconfig-primary'
    shutil.copytree(packages / 'namespace-pkgconfig-primary', dst)

    env.install(['-e', dst])
    env.install_from_path(packages / 'namespace-pkgconfig-secondary', from_sdist=False)

    roots = {'primary': dst, 'secondary': pathlib.Path(env.scheme['purelib'])}
    expected = [roots[name] / 'namespace' / 'pkgconf' for name in (first, 'secondary' if first == 'primary' else 'primary')]
    # A conflicting filename also checks that namespace search order is preserved.
    for directory, name in zip(expected, ('first', 'second'), strict=True):
        (directory / 'shared.pc').write_text(
            f'prefix=${{pcfiledir}}\nName: {name}\nDescription: Shared fixture\nVersion: 1.0\n'
        )

    script = """
import contextlib
import io
import pathlib
import sys
import warnings

import namespace.pkgconf
import pkgconf
import pkgconf.diagnose
import pkgconf._path_entrypoints

warnings.simplefilter('error', pkgconf._path_entrypoints.PathWarning)
pkgconf._path_entrypoints.run_in_isolated_context = getattr(pkgconf._path_entrypoints, f'run_in_{sys.argv[1]}')
expected = [pathlib.Path(p).resolve() for p in sys.argv[2:]]
# Verify that the fixture really spans two distinct directories in the intended order.
locations = list(dict.fromkeys(pathlib.Path(p).resolve() for p in namespace.pkgconf.__path__))
assert locations == expected, locations
# Check the backend directly so local fallback cannot conceal an isolation failure.
isolated_paths = pkgconf._path_entrypoints.run_in_isolated_context(
    pkgconf._path_entrypoints.module_paths, 'namespace.pkgconf'
)
assert [pathlib.Path(p).resolve() for p in isolated_paths] == expected, isolated_paths
paths = pkgconf.get_pkg_config_path()
assert [pathlib.Path(p).resolve() for p in paths] == expected, paths

for name in ('primary', 'secondary'):
    result = pkgconf.run_pkgconf('--variable=prefix', f'namespace-pkgconfig-{name}', capture_output=True, text=True, check=True)
    directory = pathlib.Path(result.stdout.strip()).resolve()
    assert directory in expected, result.stdout
    assert (directory / f'namespace-pkgconfig-{name}.pc').is_file(), result.stdout
result = pkgconf.run_pkgconf('--variable=prefix', 'shared', capture_output=True, text=True, check=True)
assert pathlib.Path(result.stdout.strip()).resolve() == expected[0], result.stdout

output = io.StringIO()
with contextlib.redirect_stdout(output):
    pkgconf.diagnose.report()
for path in paths:
    assert f'     path: {path}\\n' in output.getvalue(), output.getvalue()
"""
    process = subprocess.run(
        [os.fspath(env.interpreter), '-c', script, isolation, *map(os.fspath, expected)],
        env=env.env
        | {
            'PYTHONPATH': os.fspath(roots[first]),
            'PKG_CONFIG_PATH': '',
            'PKG_CONFIG_LIBDIR': os.fspath(tmp_path / 'empty'),
            'PKGCONF_PYPI_EMBEDDED_ONLY': '1',
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert process.returncode == 0, process.stderr


def test_pkg_config_path_error_on_import(env, packages):
    path = list(env.introspectable.call('pkgconf.get_pkg_config_path'))
    assert len(path) == 0

    env.install_from_path(packages / 'error-on-import', from_sdist=False)
    env_site_dir = pathlib.Path(env.scheme['purelib']).resolve()

    path = {pathlib.Path(p).resolve() for p in env.introspectable.call('pkgconf.get_pkg_config_path')}
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


def test_inplace_editable(env, tmp_path, packages, data):
    dst = tmp_path / 'inplace'
    shutil.copytree(packages / 'inplace', dst)

    env.install(['-e', dst])

    src = os.fspath(data / 'needs-example-lib.c')
    bin = os.fspath(tmp_path / 'needs-example-lib')

    cflags = env.run_interpreter('-m', 'pkgconf', '--cflags', 'example').decode().split()
    subprocess.check_call(['gcc', '-o', bin, src, *cflags])
    out = subprocess.check_output([bin])

    assert out == b'bar'
