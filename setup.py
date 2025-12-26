"""Setup script for Farmer CLI."""
from pathlib import Path

from setuptools import find_packages
from setuptools import setup


# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()


def read_requirements(filename: str) -> list[str]:
    requirements_file = Path(__file__).parent / filename
    if not requirements_file.exists():
        return []
    with open(requirements_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith(("#", "-r"))]


requirements = read_requirements("requirements.txt")
dev_requirements = read_requirements("requirements-dev.txt")
test_requirements = read_requirements("requirements-test.txt")
extras_require = {}
if dev_requirements:
    extras_require["dev"] = dev_requirements
if test_requirements:
    extras_require["test"] = test_requirements

setup(
    name="farmer-cli",
    version="0.2.0",
    author="Farmer CLI Team",
    author_email="support@farmercli.com",
    description="A modular CLI application with Rich UI for video downloading and system management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/deadcoast/farmer-cli",
    project_urls={
        "Homepage": "https://github.com/deadcoast/farmer-cli",
        "Documentation": "https://farmercli.readthedocs.io",
        "Repository": "https://github.com/deadcoast/farmer-cli.git",
        "Issues": "https://github.com/deadcoast/farmer-cli/issues",
    },
    packages=find_packages(where="src", include=["farmer_cli*"]),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require=extras_require,
    entry_points={"console_scripts": ["farmer-cli=farmer_cli.__main__:main"]},
    include_package_data=True,
    package_data={"": ["*.json", "*.sql"]},
)
