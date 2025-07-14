from pathlib import Path
from setuptools import setup, find_packages

# Get base working directory.o
base_dir = Path(__file__).resolve().parent

# Readme text for long description
with open(base_dir/"README.md") as f:
    readme = f.read()
    
setup(
    name = "jp_errant",
    version = "3.0.1",
    license = "",
    description = "The Joint Processing - ERRor ANnotation Toolkit (JP-ERRANT). Extract and Classify grammatical erros in multiple languages",
    long_description = readme,
    long_description_content_type = "text/markdown",
    author = "Jungyeul Park",
    author_email = "jungyeul.park@gmail.com",
    url = "",    
    python_requires = ">= 3.7",
    install_requires = ["rapidfuzz>=3.4.0", "errant>=3.0.0", "stanza", "pypinyin"],
    package_data={
        "jp_errant": ["en/resources/*", "stanza_resources_1.7.0.json", "zh/方正黑体简体.ttf"]
    },
    packages = find_packages(),    
    include_package_data=True,
    entry_points = {
        "console_scripts": [
            "jp_errant_compare = jp_errant.commands.compare_m2:main",
            "jp_errant_m2 = jp_errant.commands.m2_to_m2:main",
            "jp_errant_parallel = jp_errant.commands.parallel_to_m2:main"]},
    classifiers = [
        "Topic :: Text Processing :: Linguistic"]
)
