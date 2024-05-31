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
    env.run_interpreter('-m', 'ensurepip')
    env.run_interpreter('-m', 'pip', 'install', os.fspath(self_wheel))
    return env
