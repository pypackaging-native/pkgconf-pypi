# SPDX-FileCopyrightText: 2024 The pypackaging-native developers
#
# SPDX-License-Identifier: MIT

project('pkgconf-pypi',
  version : '2.1.1-0',
  license : 'MIT AND ISC',
  license_files : ['LICENSE'],
  meson_version : '>=1.3.2',
)

py = import('python').find_installation(pure: false)
python_bin_dir = py.get_install_dir(pure: true) / 'pkgconf' / '.bin'  # FIXME: This is not pure.

py.install_sources(
  [
    'src/pkgconf/__init__.py',
    'src/pkgconf/diagnose.py',
  ],
  subdir: 'pkgconf',
  pure: true,
)

# In pyproject.toml we only select the `runtime-python` tag to install,
# which contains the doesn't contain anything from the upstream pkgconf.
upstream = subproject('pkgconf', default_options : ['default_library=static'])

libpkgconf = upstream.get_variable('libpkgconf')
pkgconf_exe = upstream.get_variable('pkgconf_exe')

executable(
  'pkgconf',
  objects: pkgconf_exe.extract_all_objects(),
  link_with: upstream.get_variable('libpkgconf'),
  install_dir: python_bin_dir,
  install_tag: 'python-runtime',
  install: true,
)

# FIXME: This is needed to make meson-python give us a platform-dependent but
#        Python-independent wheel.
executable(
  '_pkgconf-original',
  objects: pkgconf_exe.extract_all_objects(),
  link_with: upstream.get_variable('libpkgconf'),
  install_tag: 'python-runtime',
  install: true,
)
