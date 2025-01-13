project('error-on-import', 'c', version: '1.0.0')

py = import('python').find_installation()
py.install_sources('foo/__init__.py', subdir: 'foo')
py.install_sources('foo/bar/__init__.py', subdir: 'foo/bar')
