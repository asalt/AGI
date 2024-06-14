from setuptools import setup, find_packages

setup(
    name='AGI',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        # list your Python dependencies here, for example:
        # 'numpy',
        # 'pandas',
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            # If you want your package to install any scripts directly to the PATH, define them here
            # 'my-command=my_package.module:function'
        ],
    },
)
