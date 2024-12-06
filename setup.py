from setuptools import setup, find_packages

setup(
    name="university-scheduler",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "openpyxl>=3.1.0",
        "tabulate>=0.9.0",
        "rich>=13.0.0",
    ],
    python_requires=">=3.8",
) 