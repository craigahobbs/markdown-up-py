# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

import os

from setuptools import setup


def main():
    # Read the readme for use as the long description
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.md'), encoding='utf-8') as readme_file:
        long_description = readme_file.read()

    # Do the setup
    setup(
        name='markdown-up',
        description='Markdown viewer application',
        long_description=long_description,
        long_description_content_type='text/markdown',
        version='1.2.5',
        author='Craig A. Hobbs',
        author_email='craigahobbs@gmail.com',
        keywords='Markdown viewer application',
        url='https://github.com/craigahobbs/markdown-up-py',
        license='MIT',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Topic :: Utilities'
        ],
        package_dir={'': 'src'},
        packages=['markdown_up'],
        install_requires=[
            'chisel >= 1.0'
        ],
        entry_points={
            'console_scripts': [
                'markdown-up = markdown_up.main:main'
            ]
        }
    )


if __name__ == '__main__':
    main()
