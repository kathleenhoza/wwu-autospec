from setuptools import setup

setup(
    name='WWU-AutoSpec',
    version='0.1.18',
    packages=['wwu-autospec'],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    description='Control software for spectroscopy using ASD RS3 and ViewSpec Pro',
    long_description=open('README.txt').read(),
    url='https://github.com/kathleenhoza/autospectroscopy',
    author='Kathleen Hoza',
    author_email='kathleenhoza@gmail.com',
    project_urls={
        'Source':'https://github.com/kathleenhoza/autospectroscopy'
    },
    install_requires=['pygame','matplotlib','numpy','cython'],
    python_requires='>=3',
)