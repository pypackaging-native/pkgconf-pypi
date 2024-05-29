project('example', 'c', version: '1.0.0')

lib = library('example', 'lib.c', install: true)

py = import('python').find_installation()
py.install_sources('example/__init__.py', subdir: 'example')
py.install_sources('example/pkgconf/__init__.py', subdir: 'example/pkgconf')

pkg = import('pkgconfig')
# https://github.com/mesonbuild/meson-python/issues/609
# pkg.generate(lib, install_dir: py.get_install_dir(pure: true) / 'example' / 'pkgconf')
