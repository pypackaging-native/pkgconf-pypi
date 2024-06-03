project('register-pkg-config-path', 'c', version: '1.0.0')

lib = library('register-pkg-config-path', 'lib.c', install: true)

py = import('python').find_installation()
py.install_sources('register_pkg_config_path/__init__.py', subdir: 'register_pkg_config_path')
py.install_sources('register_pkg_config_path/pkgconf/__init__.py', subdir: 'register_pkg_config_path/pkgconf')

pkg = import('pkgconfig')
# https://github.com/mesonbuild/meson-python/issues/609
# pkg.generate(lib, install_dir: py.get_install_dir(pure: true) / 'example' / 'pkgconf')
