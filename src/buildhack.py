import pathlib
import textwrap

import mesonpy
import wheel.wheelfile


def get_requires_for_build_sdist(config_settings=None):
    return mesonpy.get_requires_for_build_sdist(config_settings)


def get_requires_for_build_wheel(config_settings=None):
    return mesonpy.get_requires_for_build_wheel(config_settings)


def build_sdist(sdist_directory, config_settings=None):
    return mesonpy.build_sdist(sdist_directory, config_settings)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    workdir = pathlib.Path(wheel_directory)

    wheel_path = workdir / mesonpy.build_wheel(wheel_directory, config_settings, metadata_directory)

    name_parts = wheel_path.stem.split('-')
    name_parts[2] = 'py3'
    name_parts[3] = 'none'
    new_name = '-'.join(name_parts) + '.whl'
    assert new_name != wheel_path.name
    new_wheel_path = workdir / new_name

    with (
        wheel.wheelfile.WheelFile(wheel_path, 'r') as original_wheel,
        wheel.wheelfile.WheelFile(new_wheel_path, 'w') as new_wheel,
    ):
        for item in original_wheel.infolist():
            if item.filename.endswith('.dist-info/WHEEL'):
                new_wheel.writestr(
                    item,
                    textwrap.dedent("""
                    Wheel-Version: 1.0
                    Generator: meson
                    Root-Is-Purelib: false
                    Tag: py3-none-linux_x86_64
                """)
                    .strip()
                    .encode(),
                )
            elif item.filename.endswith('.dist-info/RECORD'):
                pass  # WheelFile does this automatically for us :)
            else:
                new_wheel.writestr(item, original_wheel.read(item.filename))

    wheel_path.unlink()
    return new_wheel_path.name
