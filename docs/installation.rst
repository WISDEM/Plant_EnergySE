Installation
------------

.. admonition:: prerequisites
   :class: warning

	General: C compiler, Fortran compiler, NumPy, SciPy, Swig, pyWin32, MatlPlotLib, Lxml, OpenMDAO

	Wind Plant Framework: FUSED-Wind (Framework for Unified Systems Engineering and Design of Wind Plants)

	Sub-Models: CommonSE, OpenWind

	Supporting python packages: Pandas, Algopy, Zope.interface, Sphinx, Xlrd, PyOpt, py2exe, Pyzmq, Sphinxcontrib-bibtex, Sphinxcontrib-zopeext, Numpydoc, Ipython

Clone the repository at `<https://github.com/WISDEM/Plant_EnergySE>`_
or download the releases and uncompress/unpack (Plant_EnergySE.py-|release|.tar.gz or Plant_EnergySE.py-|release|.zip) from the website link at the bottom the `Plant_EnergySEsite<http://nwtc.nrel.gov/Plant_EnergySE>`_.

To install Plant_EnergySE, first activate the OpenMDAO environment and then install with the following command.

.. code-block:: bash

   $ plugin install

To check if installation was successful try to import the module from within an activated OpenMDAO environment:

.. code-block:: bash

    $ python

.. code-block:: python

	> import plant_energyse.nrel_csm_aep.nrel_csm_aep
	> import plant_energyse.openwind.enterprise.openWindExtCode
	> import plant_energyse.openwind.enterprise.openwind_assembly
	> import plant_energyse.openwind.academic.openWindAcComponent
	> import plant_energyse.openwind.academic.openwindAC_assembly

Note that you must have the enterprise or academic versions and corresponding licesnses for OpenWind in order to use those software packages.  This software contains only the OpenMDAO wrapper for those models.

You can also run the unit tests which include functional and gradient tests.  Analytic gradients are provided for variables only so warnings will appear for missing gradients on model input parameters; these can be ignored.

.. code-block:: bash

   $ python src/test/test_Plant_EnergySE.py

An "OK" signifies that all the tests passed.

For software issues please use `<https://github.com/WISDEM/Plant_EnergySE/issues>`_.  For functionality and theory related questions and comments please use the NWTC forum for `Systems Engineering Software Questions <https://wind.nrel.gov/forum/wind/viewtopic.php?f=34&t=1002>`_.

.. only:: latex

    An HTML version of this documentation that contains further details and links to the source code is available at `<http://wisdem.github.io/Plant_EnergySE>`_

