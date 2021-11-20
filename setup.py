from setuptools import setup
from Cython.Build import cythonize
import numpy


setup(
    name='puzzle solver',
    ext_modules=cythonize("puzzle/solver.pyx"),
    include_dirs=[numpy.get_include()],
    zip_safe=False,
)