from setuptools import setup, find_packages

with open("README.md", "r") as file:
    readme = file.read()

setup(
    name = "femcord",
    version = "0.1.0",
    author = "czubix",
    description = "A simple Discord library",
    license = "Apache 2.0",
    long_description = readme,
    long_description_content_type = "text/markdown",
    url = "https://github.com/czubix/femcord",
    packages = find_packages(exclude=["docs"])
)