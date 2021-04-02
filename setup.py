from setuptools import setup

with open("readme.md", 'r') as f:
    long_description = f.read()

setup(
    name="steam_account_switcher",
    version="0.0.1",
    description="Program to quickly switch between steam accounts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tommis/steam_account_switcher",
    download_url="https://github.com/tommis/steam_account_switcher/releases",
    author="Tommi Saira",
    author_email="tommi@saira.fi",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    packages=["pyside2", "pyvdf", "requests"],
    include_package_data=True,
    install_requires=[
    ],
    entry_points={"console_scripts": ["main=main.__main__:main"]},
)