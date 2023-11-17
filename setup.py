from setuptools import setup


def get_requirements():
    with open("requirements.txt", "r") as f:
        reqs = f.readlines()
    return reqs


setup(
    name="shipping",
    version="0.1.0",
    py_modules=["shipping"],
    install_requires=get_requirements(),
    entry_points={
        "console_scripts": [
            "shipping = main:cli",
        ],
    },
)
