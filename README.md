Plant_EnergySE is a set of models for analyzing wind plant energy production for both land-based and offshore wind plants.

Author: [K. Dykes](mailto:katherine.dykes@nrel.gov)

## Prerequisites

NumPy, SciPy, FUSED-Wind, OpenMDAO

## Installation

Install PLant_EnergySE within an activated OpenMDAO environment

	$ plugin install

It is not recommended to install the software outside of OpenMDAO.

## Run Unit Tests

To check if installation was successful try to import the module

	$ python
	> import basic_aep.basic_aep
	> import nrel_csm_aep.nrel_csm_aep
	> import openwind.enterprise.openWindExtCode
	> import openwind.enterprise.openwind_assembly
	> import openwind.academic.openWindAcComponent
	> import openwind.academic.openwindAC_assembly

Note that you must have the enterprise or academic versions and corresponding licesnses for OpenWind in order to use those software packages.  This software contains only the OpenMDAO wrapper for those models.

You may also run the unit tests.

	$ python src/test/test_Plant_EnergysSE_gradients.py

Note that the gradient test is only provided for the basic_aep software.

## Detailed Documentation

Online documentation is available at <http://wisdem.github.io/Plant_EnergySE/>