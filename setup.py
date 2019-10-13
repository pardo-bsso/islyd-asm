import os
from setuptools import find_packages, setup

from islyd_asm import __version__


with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='islyd-asm',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'attrs',
    ],
    license='AGPL-3.0',
    description='Simple assembler for the VHDL processor described in https://catedra.ing.unlp.edu.ar/electrotecnia/islyd/seminario_micro.html',
    long_description=README,
    long_description_content_type='text/markdown',
    url='http://github.com/telescopio-montemayor/islyd-asm',
    author='Adrián Pardini',
    author_email='github@tangopardo.com.ar',
    entry_points={
        'console_scripts': [
            'islyd-asm=islyd_asm.main:run'
        ]
    },
    classifiers=[
        'Environment :: Console',
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Education',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'Topic :: Software Development :: Assemblers',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: System :: Hardware',
    ],
    keywords='assembler, vhdl, electronics',
)
