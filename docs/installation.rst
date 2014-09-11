Installation
------------

.. admonition:: prerequisites
   :class: warning

   NumPy, SciPy, FUSED-Wind, OpenMDAO

Clone the repository at `<https://github.com/WISDEM/Plant_EnergySE>`_
or download the releases and uncompress/unpack (Plant_EnergySE.py-|release|.tar.gz or Plant_EnergySE.py-|release|.zip)

To install Plant_EnergySE, first activate the OpenMDAO environment and then install with the following command.

.. code-block:: bash

   $ plugin install

To check if installation was successful try to import the module

.. code-block:: bash

    $ python

.. code-block:: python

	> import basic_aep.basic_aep
	> import nrel_csm_aep.nrel_csm_aep
	> import openwind.enterprise.openWindExtCode
	> import openwind.enterprise.openwind_assembly
	> import openwind.academic.openWindAcComponent
	> import openwind.academic.openwindAC_assembly

Note that you must have the enterprise or academic versions and corresponding licesnses for OpenWind in order to use those software packages.  This software contains only the OpenMDAO wrapper for those models.

You can also run the unit tests for the gradient checks

.. code-block:: bash

   $ python src/test/test_Plant_EnergySE_gradients.py

Note that the gradient test is only provided for the basic_aep software.

An "OK" signifies that all the tests passed.

.. only:: latex

    An HTML version of this documentation that contains further details and links to the source code is available at `<http://wisdem.github.io/Plant_EnergySE>`_

