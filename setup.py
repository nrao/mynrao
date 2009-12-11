from setuptools import setup, find_packages
import sys, os

version = '0.2'

setup(name='nraouserdb',
      version=version,
      description="Retrieve profiles from the NRAO user database.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Kai Groner',
      author_email='kgroner@nrao.edu',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
	  'lxml >= 2.2',
	  'caslib >= 0.3',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      nraouserdb-query = nraouserdb.cli:main
      """,
      )
