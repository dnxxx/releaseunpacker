from distutils.core import setup

setup(
    name='releaseunpacker',
    version='0.2.0',
    description='Release unpacker',

    packages=['releaseunpacker'],
    scripts=['bin/releaseunpacker'],

    author='dnxxx',
    author_email='dnx@fbi-security.net',
    license='BSD',

    install_requires=[
        'tendo',
        'argh',
        'unipath',
        'rarfile',
        'ago',
        'lazy',
    ]
)
