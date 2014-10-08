Plant_EnergySE is a set of models for analyzing wind plant energy production for both land-based and offshore wind plants.

Author: [K. Dykes and G. Scott](mailto:nrel.wisdem+plantenergyse@gmail.com)

## Version

This software is a beta version 0.1.0.

## Detailed Documentation

For detailed documentation see <http://wisdem.github.io/Plant_EnergySE/>

## Prerequisites

General: NumPy, SciPy, Swig, pyWin32, MatlPlotLib, Lxml, OpenMDAO

## Dependencies

Wind Plant Framework: [FUSED-Wind](http://fusedwind.org) (Framework for Unified Systems Engineering and Design of Wind Plants)

Sub-Models: CommonSE, OpenWind

Supporting python packages: Pandas, Algopy, Zope.interface, Sphinx, Xlrd, PyOpt, py2exe, Pyzmq, Sphinxcontrib-bibtex, Sphinxcontrib-zopeext, Numpydoc, Ipython

## Installation

First, clone the [repository](https://github.com/WISDEM/Plant_EnergySE)
or download the releases and uncompress/unpack (Plant_EnergySE.py-|release|.tar.gz or Plant_EnergySE.py-|release|.zip) from the website link at the bottom the [WISDEM site](http://nwtc.nrel.gov/Plant_EnergySE).

Install PLant_EnergySE within an activated OpenMDAO environment:

	$ plugin install

It is not recommended to install the software outside of OpenMDAO.

## Run Unit Tests

To check if installation was successful try to import the module from within an activated OpenMDAO environment:

	$ python
	> import plant_energyse.basic_aep.basic_aep
	> import plant_energyse.nrel_csm_aep.nrel_csm_aep
	> import plant_energyse.openwind.enterprise.openWindExtCode
	> import plant_energyse.openwind.enterprise.openwind_assembly
	> import plant_energyse.openwind.academic.openWindAcComponent
	> import plant_energyse.openwind.academic.openwindAC_assembly

Note that you must have the enterprise or academic versions and corresponding licesnses for OpenWind in order to use those software packages.  This software contains only the OpenMDAO wrapper for those models.

You may also run the unit tests which include functional and gradient tests.  Analytic gradients are provided for variables only so warnings will appear for missing gradients on model input parameters; these can be ignored.

	$ python src/test/test_Plant_EnergysSE.py

For software issues please use <https://github.com/WISDEM/Plant_EnergySE/issues>.  For functionality and theory related questions and comments please use the NWTC forum for [Systems Engineering Software Questions](https://wind.nrel.gov/forum/wind/viewtopic.php?f=34&t=1002).