import os
import pathlib
import sys

import environment_helpers
import environment_helpers.build
import pytest


ROOT = pathlib.Path(__file__).parent.parent

sys.path.insert(0, str(ROOT / 'src'))


@pytest.fixture
def root():
    return ROOT


@pytest.fixture
def packages():
    return ROOT / 'tests' / 'packages'


@pytest.fixture
def data():
    return ROOT / 'tests' / 'data'


@pytest.fixture
def examples():
    return ROOT / 'examples'


@pytest.fixture(scope='session')
def self_wheel(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp('wheel')
    return environment_helpers.build.build_wheel(ROOT, tmpdir)


@pytest.fixture
def env(tmpdir, self_wheel):
    """Make a virtual environment with our project installed."""
    env = environment_helpers.create_venv(tmpdir)

    # Write .pth file pointing to the current environment
    current_env = environment_helpers.CurrentEnvironment()
    purelib, platlib = current_env.scheme['purelib'], current_env.scheme['platlib']
    env.scheme['purelib'].joinpath('base-env.pth').write_text(f'{purelib!s}\n{platlib!s}\n')

    env.install_wheel(self_wheel)
    return env


@pytest.fixture(autouse=True)
def unset_pkg_config_path(monkeypatch):
    monkeypatch.delenv('PKG_CONFIG_PATH', raising=False)


@pytest.fixture(autouse=True)
def reset_recursive_flag():
    yield
    os.environ.pop('PKGCONF_PYPI_RECURSIVE', None)


@pytest.fixture()
def podman():
    podman = pytest.importorskip('podman')
    with podman.PodmanClient() as client:
        yield client


@pytest.fixture()
def container(podman, root, packages):
    yield podman.containers.run(
        'python',
        command=['bash', '-c', 'sleep infinity'],
        detach=True,
        privileged=True,  # https://github.com/containers/podman-py/issues/343
        # security_opt=['seccomp=unconfined'],
        mounts=[
            {
                'type': 'bind',
                'source': os.fspath(root),
                'target': '/project',
                'read_only': False,
            },
            {
                'type': 'bind',
                'source': os.fspath(packages),
                'target': '/packages',
                'read_only': False,
            },
        ],
    )
