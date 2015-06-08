#
# This file is autogenerated during plugin quickstart and overwritten during
# plugin makedist. DO NOT CHANGE IT if you plan to use plugin makedist to update 
# the distribution.
#

from setuptools import setup, find_packages

kwargs = {'author': 'Katherine Dykes and George Scott',
 'author_email': 'systems.engineering@nrel.gov',
 'description': 'NREL WISDEM modules for plant energy production and flow',
 'include_package_data': True,
 'install_requires': ['openmdao.main'],
 'keywords': ['openmdao'],
 'license' : 'Apache License, Version 2.0',
 'version' : '0.1.0',
 'name': 'Plant_EnergySE',
 'package_data': {'Plant_EnergySE': []},
 'package_dir': {'': 'src'},
 'packages': ['test','plant_energyse.nrel_csm_aep', 'plant_energyse.openwind', 'plant_energyse.openwind.enterprise', 'plant_energyse.openwind.academic'],
 'zip_safe': False}


setup(**kwargs)

