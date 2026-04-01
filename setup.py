import json
from setuptools import setup
from pathlib import Path

here = Path(__file__).parent
with open('package.json') as f:
    package = json.load(f)

long_description = (here / 'README.md').read_text(encoding='utf-8')

package_name = package["name"].replace(" ", "_").replace("-", "_")

setup(
    name=package_name,
    version=package["version"],
    author=package['author'],
    packages=[package_name],
    include_package_data=True,
    license=package['license'],
    description=package.get('description', package_name),
    install_requires=[
        'dash>=3.3.0',
    ],
    classifiers=[
        'Framework :: Dash',
    ],
    url='https://github.com/luojiaaoo/nokiao-copilot-chat',
)
