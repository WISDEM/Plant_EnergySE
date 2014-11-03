Introduction
------------

The set of models contained in this Plant_EnergySE are used to assess the energy production for a wind plant.  The first model is based on using simple statistics to determine wind plant output.  The model (nrel_csm_aep) is based on the NREL Cost and Scaling Model :cite:`Fingersh2006` and estimates energy production with either a pre-determined power curve as an input or a determined power curve based on key wind turbine parameters.  The latter software is a wrapper for the AWS Truepower OpenWind software :cite:`AWS_2012` and one must have the model and license in order to use the enterprise and academic wrappers for those respective software versions.  Only the OpenMDAO wrappers for the model are provided in this software set.

Plant_EnergySE is implemented as an `OpenMDAO <http://openmdao.org/>`_ assembly.  All supporting code is also in OpenMDAO based on the Python programming language with the exception of the AWS Truepower Openwind Software which was developed in the U++ development framework for C++.  You must have the model and license in order to use the academic and enterprise versions of this software.
