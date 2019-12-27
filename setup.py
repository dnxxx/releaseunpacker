from distutils.core import setup

setup(
    name='releaseunpacker',
    version='1.0.0',
    description='Release unpacker',

    packages=['releaseunpacker'],
    scripts=['bin/releaseunpacker'],

    author='dnxxx',
    author_email='dnx@fbi-security.net',
    license='BSD',

    install_requires=[
        'ago',
        'argh',
        'lazy',
        'rarfile',
        'tendo',
        'unipath',
    ]
)
