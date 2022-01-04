from setuptools import  find_packages, setup

setup(
    name='sol006-vnfd-handler',
    version='1.0.0',
    description="SOL006 vnfd handler",
    long_description="This is a simple prototype that takes in a SOL004 based package with a SOL006 VNFD descriptor and produces a CP4NA package with an assembly and a resource for each VDU.",
    include_package_data=True,
    packages = find_packages(), 
    entry_points ={ 
        'console_scripts': [ 
        'sol006vnfdctl=src.sol006_vnfd.core:main'
        ] 
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent'
    ],
    install_requires=[
        'glob2',
        'pyyaml',
        'pathlib', 
        'requests',
        'importlib',
    ],
)
