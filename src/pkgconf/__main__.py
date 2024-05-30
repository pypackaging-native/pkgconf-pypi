import os
import shutil
import subprocess
import sys
import sysconfig

import pkgconf


def main() -> None:
    args = sys.argv[1:]
    try:
        pkgconf.run_pkgconf(*args, check=True)
    except subprocess.SubprocessError:
        # If our pkgconf lookup fails, fallback to the system pkgconf/pkg-config.
        # For simplicity, the previous call will output to stdout/stderr
        # regardless of its success, since capturing stdout/stderr in order to
        # replay is tricky. If the fallback path triggers, it will also output
        # to stdout/stderr, meaning we will have the output of both process
        # calls. While a bit unexpected, I believe this is the best option for
        # debugging.
        scripts = sysconfig.get_path('scripts')
        path_list = os.environ.get('PATH', os.defpath).split(os.pathsep)
        if scripts in path_list:
            path_list.remove(scripts)
        path = os.pathsep.join(path_list)
        system_executable = shutil.which('pkgconf', path=path) or shutil.which('pkg-config', path=path)
        if system_executable:
            subprocess.run([system_executable, *args])


if __name__ == '__main__':
    main()
