from setuptools import setup, find_packages

setup(
    name="vbe_3d",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "ursina",
        "numpy",
        "torch",
    ],
) 