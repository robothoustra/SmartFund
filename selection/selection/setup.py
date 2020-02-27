import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="selection", # Replace with your own username
    version="0.1",
    author="Alexis Robert",
    author_email="alexis.robert1088@hotmail.fr",
    description="Module de sélection de titres et de backtesting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/robothoustra/SmartFund/tree/master/selection",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
