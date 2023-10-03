from setuptools import setup

setup(
    name='timesheet',
    version='1.0',
    py_modules=['timesheet'],
    install_requires=open('requirements.txt').readlines(),
    entry_points={
        'console_scripts': [
            'timesheet=timesheet:main'
        ]
    }
)