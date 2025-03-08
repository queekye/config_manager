from setuptools import setup, find_packages

setup(
    name="modern-config-manager",
    version="0.3.1",
    description="一个强大而灵活的配置管理系统",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    author="Kang Chen",
    author_email="chenkangcs@foxmail.com",
    url="https://github.com/queekye/config_manager",
    packages=find_packages(include=['config_manager', 'config_manager.*']),
    install_requires=[
        'dataclasses;python_version<"3.7"',
        'pyyaml>=5.1',
    ],
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
)