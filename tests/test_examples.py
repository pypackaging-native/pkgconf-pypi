import os
import subprocess


def test_header_only_library(env, tmp_path, examples, data):
    env.install_from_path(examples / 'header-only-library', from_sdist=False)

    src = os.fspath(data / 'needs-example-lib.c')
    bin = os.fspath(tmp_path / 'needs-example-lib')

    pkgconf = os.path.join(env.scheme['scripts'], 'pkgconf')
    cflags = subprocess.check_output([pkgconf, '--cflags', 'example']).decode().split()
    subprocess.check_call(['gcc', '-o', bin, src, *cflags])
    out = subprocess.check_output([bin])

    assert out == b'bar'
