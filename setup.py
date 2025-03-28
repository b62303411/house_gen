# setup.py
from setuptools import setup, find_packages

setup(
    name='house_gen',          # Your project name
    version='0.1.0',           # Version number
    packages=find_packages(),  # Automatically find and include all packages
    install_requires=[
        # List your runtime dependencies here, e.g.:
        # 'numpy>=1.19.5',
        # 'some_other_package',
    ],
    python_requires='>=3.7',   # Required Python version
)
