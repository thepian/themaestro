from setuptools import setup, find_packages
import sys, os

version = '0.1dev'

packages = find_packages('python')
packages.append('conf')

setup(name='themaestro',
      version=version,
      description="Thepian Maestro",
      long_description="""\
""",
      keywords='thepian themaestro maestro theapps django',
      author='Henrik Vendelbo',
      author_email='hvendelbo.dev@googlemail.com',
      url='www.thepian.org',
      license='All Rights Reserved',
      package_dir= {'':'python', 'conf':'conf'},
      packages= packages,
      include_package_data=True,
      zip_safe=False,
      setup_requires=['setuptools',],
      install_requires= ['Django','theapps','thepian-lib','docutils','ipython'],
      entry_points= {
        'console_scripts':[
            'syspath = about:dummy_cmdline',
            'maestro = themaestro.commands:maestro_execute_from_command_line',
            'django = themaestro.commands:django_execute_from_command_line',
        ],
      },
      classifiers=[
        'Development Status :: Alpha',
        'Environment :: Web Environment',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: JavaScript',
        ], 
      )