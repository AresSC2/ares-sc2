import os
import shutil
from distutils.command.build_ext import build_ext
from distutils.core import Distribution, Extension

import numpy
from Cython.Build import cythonize
import platform

link_args = []
include_dirs = [numpy.get_include()]
libraries = []


def build():
    ext_modules = []
    for root, directories, files in os.walk("src"):
        for file in files:
            if file.endswith("pyx"):
                file_name = file.split(".")[0]
                if platform.system() == "Windows":
                    _path = root.replace("\\", ".")
                else:
                    _path = root.replace("/", ".")

                module = Extension(
                    name=f"{_path}.{file_name}",
                    sources=[os.path.join(root, file),],
                    extra_link_args=link_args,
                    include_dirs=include_dirs,
                    libraries=libraries,
                )
                ext_modules.append(module)

    ext_modules = cythonize(
        ext_modules,
        include_path=include_dirs,
        compiler_directives={"binding": True, "language_level": 3},
    )

    distribution = Distribution({"name": "extended", "ext_modules": ext_modules})
    distribution.package_dir = "extended"

    cmd = build_ext(distribution)
    cmd.ensure_finalized()
    cmd.run()

    # Copy built extensions back to the project
    for output in cmd.get_outputs():
        relative_extension = os.path.relpath(output, cmd.build_lib)
        shutil.copyfile(output, relative_extension)
        mode = os.stat(relative_extension).st_mode
        mode |= (mode & 0o444) >> 2
        os.chmod(relative_extension, mode)

if __name__ == "__main__":
    build()
