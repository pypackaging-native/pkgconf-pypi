project('register-pkg-config-path', 'c', version: '1.0.0')

py = import('python').find_installation(pure: false)

lib = library(
    'register-pkg-config-path', 'lib.c',
    install: true,
    install_dir: py.get_install_dir() / 'register_pkg_config_path' / 'lib',
)

install_subdir('register_pkg_config_path', install_dir: py.get_install_dir())
