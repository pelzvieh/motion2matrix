from setuptools import setup

setup(
    name='motion2matrix',
    version='0.0.5',
    packages=['motion2matrix'],
    url='https://github.com/pelzvieh/motion2matrix',
    license='MIT',
    author='pelzvieh',
    author_email='motion2matrix@flying-snail.de',
    description='Send motion detection events to matrix',
    install_requires=['matrix-nio[e2e]>=0.19', 'asyncio', 'aiohttp', 'python-magic>=0.4.22'],
    entry_points={
        'console_scripts': ['motion2matrix=motion2matrix.main:motion2matrixmain'],
    },
)
