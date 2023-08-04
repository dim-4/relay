from setuptools import setup, find_packages

setup(
    name='relaypy-async',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        "asyncio",
        "pydantic"
    ],
    author='Vos',
    author_email='your.email@example.com',
    description="""Relay is a Python package providing an asynchronous event system in a class, enabling easy inter-method communication. It automatically validates emitted data against provided type hints and facilitates setting up complex event emitting-listening configurations through easy bindings creation.""",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/dim-4/relay',  # your repo link
    classifiers=[
        # Classifiers to indicate who your project is intended for, what it does, etc.
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11'
    ],
)