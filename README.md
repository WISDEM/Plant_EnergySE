# Plant_AEPSE

A set of models for analyzing wind plant energy production for use in plant layout design and cost of energy analysis.

Author: [K. Dykes](mailto:katherine.dykes@nrel.gov)

## Prerequisites

NumPy, SciPy, FUSED-Wind, OpenMDAO

## Installation

Install Plant_AEPSE within an activated OpenMDAO environment

	$ plugin install

It is not recommended to install the software outside of OpenMDAO.

## Run Unit Tests

To check if installation was successful try to import the module

	$ python
	> import plant_aepse.plant_aepse

You may also run the unit tests.

	$ python src/test/test_Plant_AEPSE_gradients.py

## Detailed Documentation

Online documentation is available at <http://wisdem.github.io/Plant_AEPSE/>