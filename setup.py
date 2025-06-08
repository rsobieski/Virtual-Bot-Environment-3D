from setuptools import setup, find_packages

setup(
    name="vbe_3d",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=2.2.6",
        "Panda3D>=1.10.15",
        "panda3d-gltf>=1.3.0",
        "panda3d-simplepbr>=0.13.1",
        "pillow>=11.2.1",
        "torch>=2.7.0",
        "typing_extensions>=4.14.0",
        "ursina>=7.0.0",
        "pandas>=2.3.0",
        "matplotlib>=3.10.0",
        "scikit-learn>=1.7.0",
        "gym>=0.26.0",
        "websockets>=15.0.0",
        "aiohttp>=3.12.0",
    ],
    python_requires=">=3.8",
) 