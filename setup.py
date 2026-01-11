# Copyright (c) SkyForge Team.
# !/usr/bin/env python
import os
from setuptools import find_packages, setup
from typing import List


def readme():
    with open('README.md', encoding='utf-8') as f:
        content = f.read()
    return content


version_file = 'swift/version.py'


def get_version():
    with open(version_file, 'r', encoding='utf-8') as f:
        exec(compile(f.read(), version_file, 'exec'))
    return locals()['__version__']


def parse_requirements(fname='requirements.txt'):
    requirements = []
    if os.path.exists(fname):
        with open(fname, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements


if __name__ == '__main__':
    install_requires = parse_requirements('requirements.txt')

    setup(
        name='skyforge-core',
        version=get_version(),
        description='SkyForge: Next-generation Infrastructure for LLM Fine-Tuning',
        long_description=readme(),
        long_description_content_type='text/markdown',
        author='SkyForge Team',
        author_email='contact@skyforge.ai',
        keywords=['transformers', 'LLM', 'lora', 'rlhf', 'skyforge'],
        url='https://github.com/skyforge-ai/skyforge',
        packages=find_packages(exclude=('tests', 'tests.*')),
        include_package_data=True,
        package_data={
            '': ['utils/*', 'llm/dataset/data/*.*', 'llm/ds_config/*.json', 'plugin/loss_scale/config/*.json']
        },
        python_requires='>=3.8.0',
        classifiers=[
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.12',
        ],
        license='Apache License 2.0',
        install_requires=install_requires,
        entry_points={
            'console_scripts': ['skyforge=swift.cli.main:cli_main', 'swift=swift.cli.main:cli_main']
        },
        zip_safe=False)
