from setuptools import setup, find_packages


def get_requirements():
    with open("requirements.txt", "r") as f:
        reqs = f.readlines()
    return reqs


setup(
    name="shipping",
    version="0.1.1",
    py_modules=["shipping"],
    packages=find_packages(),
    install_requires=get_requirements(),
    entry_points={
        "console_scripts": [
            "shipping = shipping.main:cli",
        ],
    },
)
