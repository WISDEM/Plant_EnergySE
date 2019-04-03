# Plant_EnergySE
## WARNING- This repository is deprecated

Plant_EnergySE is a set of models for analyzing wind plant energy production for both land-based and offshore wind plants.

Author: [NREL WISDEM Team](mailto:systems.engineering@nrel.gov) 

## Documentation

See local documentation in the `docs`-directory or access the online version at <http://wisdem.github.io/Plant_EnergySE/>

## Dependencies

OpenWind

## Installation

For detailed installation instructions of WISDEM modules see <https://github.com/WISDEM/WISDEM> or to install Plant_EnergySE by itself do:

    $ python setup.py install

## Run Unit Tests

To check if installation was successful try to import the package:

	$ python
	> import plant_energyse.basic_aep.basic_aep
	> import plant_energyse.nrel_csm_aep.nrel_csm_aep
	> import plant_energyse.openwind.openWindExtCode
	> import plant_energyse.openwind.openWindAComponent

Note that you must have the enterprise version and corresponding license for OpenWind in order to use those software packages.  
This software contains only the OpenMDAO wrapper for those models.

You may also run the unit tests which include functional and gradient tests.  Analytic gradients are provided for variables only so warnings will appear for missing gradients on model input parameters; these can be ignored.

	$ python src/test/test_Plant_EnergysSE.py

For software issues please use <https://github.com/WISDEM/Plant_EnergySE/issues>.  For functionality and theory related questions and comments please use the NWTC forum for [Systems Engineering Software Questions](https://wind.nrel.gov/forum/wind/viewtopic.php?f=34&t=1002).
