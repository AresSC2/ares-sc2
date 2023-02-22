import platform
from distutils.core import setup
from distutils.extension import Extension
from os import path, walk

import numpy
from Cython.Build import cythonize
from Cython.Distutils import build_ext

if __name__ == "__main__":
    ext_modules = []
    for root, directories, files in walk("src"):
        for file in files:
            if file.endswith("pyx"):
                file_name = file.split(".")[0]
                if platform.system() == "Windows":
                    _path = root.replace("\\", ".")
                else:
                    _path = root.replace("/", ".")

                module = Extension(
                    name=f"{_path}.{file_name}", sources=[path.join(root, file)]
                )
                ext_modules.append(module)

    setup(
        name="ares-sc2",
        cmdclass={"build_ext": build_ext},
        ext_modules=cythonize(ext_modules, language_level="3"),
        include_dirs=[numpy.get_include()],
    )
