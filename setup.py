from setuptools import setup

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="battle-of-dots",
    version="0.1.1",
    description="Battle of Dots is a LAN RTS war game, a simple barebones war simulation built in python with pygame. Original credit goes to",
    author="Keruki2005",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/Keruki2005/battle-of-dots",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.10",
    packages=['src'],
    py_modules=["bod"],
    install_requires=[
        'pygame-ce',
        'orjson',
        'perlin-noise',
        'numpy',
        'setuptools'
    ],
    entry_points={
        "console_scripts": [
            "bod=bod:main",
            "bod-map-editor=src.bod_map_editor:main",
        ],
    },
)
