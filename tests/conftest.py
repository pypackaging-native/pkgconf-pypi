import pathlib
import sys

import environment_helpers
import environment_helpers.build
import pytest


root = pathlib.Path(__file__).parent.parent

sys.path.insert(0, str(root / 'src'))


@pytest.fixture
def packages():
    return root / 'tests' / 'packages'


@pytest.fixture
def data():
    return root / 'tests' / 'data'


@pytest.fixture
def examples():
    return root / 'examples'


@pytest.fixture(scope='session')
def self_wheel(tmp_path_factory):
    tmpdir = tmp_path_factory.mktemp('wheel')
    return environment_helpers.build.build_wheel(root, tmpdir)


@pytest.fixture
def env(tmpdir, self_wheel):
    """Make a virtual environment with our project installed."""
    env = environment_helpers.create_venv(tmpdir)
    env.install_wheel(self_wheel)
    return env
