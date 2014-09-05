.. _documentation-label:

.. currentmodule:: basic_aep.basic_aep

Documentation
-------------

Documentation for Basic_AEP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following inputs and outputs are defined for Basic_AEP:

.. literalinclude:: ../src/basic_aep/basic_aep.py
    :language: python
    :start-after: aep_assembly(GenericAEPModel)
    :end-before: def configure(self)
    :prepend: class aep_assembly(Assembly):

Referenced Energy Production Modules
===========================================
.. module:: basic_aep.basic_aep
.. class:: BasicAEP
.. class:: aep_assembly
.. class:: aep_weibull_assembly

Referenced Supporting Modules
==============================
.. class:: CDFBase
.. class:: WeibullCDF
.. class:: RayleighCDF 
.. class:: aep_component

Referenced Utilities
=================================================
.. module:: commonse.utilities
.. class:: hstack
.. class:: vstack



.. currentmodule:: nrel_csm_aep.nrel.csm.aep

Documentation for NREL_CSM_AEP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following inputs and outputs are defined for NREL_CSM_AEP:

.. literalinclude:: ../src/nrel_csm_aep/nrel_csm_aep.py
    :language: python
    :start-after: aep_csm_assembly(GenericAEPModel)
    :end-before: def configure(self)
    :prepend: class aep_csm_assembly(Assembly):

Referenced Energy Production Modules
===========================================
.. module:: nrel_csm_aep.nrel_csm_aep
.. class:: aep_csm_assembly

Optional Referenced Power Curve Calculation Models
===================================================
.. module:: nrel_csm_aep.aep_csm_component
.. class:: aep_csm_component

.. module:: nrel_csm_aep.aero_csm_component
.. class:: aero_csm_component

.. module:: nrel_csm_aep.csmDriveEfficiency
.. class:: DrivetrainEfficiencyModel
.. class:: csmDriveEfficiency

.. module:: nrel_csm_aep.drivetrain_csm_component
.. class:: drive_csm_component



.. currentmodule:: openwind.enterprise.openwind_assembly

Documentation for openwind_assembly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following inputs and outputs are defined for openwind_assembly:

.. literalinclude:: ../src/openwind/enterprise/openwind_assembly.py
    :language: python
    :start-after: openwind_assembly(GenericAEPModel)
    :end-before: def __init__(self, ssfile)
    :prepend: class openwind_assembly(Assembly):

Referenced Energy Production Modules
===========================================
.. module:: openwind.enterprise.openwind_assembly
.. class:: openwind_assembly

Supporting Models for OpenWind Enterprise
==========================================
.. module:: openwind.enterprise.openWindExtCode
.. class:: OWwrapped

General Supporting Models for OpenWind
==========================================
Turbine Description Translation
.. module:: openwind.turbfuncs
.. function:: owtg_to_wtpc(owtg_file)
.. function:: wtpc_to_owtg(wtpc, trbname='GenericTurbine', desc='GenericDescription')
.. function:: wtpc_dump(wtpc, shortFmt=False)

Read/Write Turbine XML File
..module:: openwind.rwTurbXML
Read
.. function:: parseOWTG(fname,debug=False)
.. function:: getTurbParams(tree,debug=False)
.. function:: getTbls(tree,tblname,debug=False)
.. function:: getPwrTbls(tree,debug=False)
.. function:: getThrustTbls(tree,debug=False)
.. function:: getRPMTbls(tree,debug=False)

Write
.. function:: newTurbTree(trbname, desc, vels, power, thrust, rpm, hubht, rdiam, rho=[1.225], percosts=[], cutInWS=3.0, cutOutWS=25.0, nblades=3, machineRating=3000.0, ttlCost=2000000, fndCost=100000)
.. class:: PerCost
.. function:: makeTblRows(parent, x, xname, cr)
.. function:: addNoiseRows(parent, ttl, tnl, hz, nhz)
.. function:: makeTable(tblName, vels, rho, y)
.. function:: modTurbXML(oldTurbFile, newTurbFile, rotor_diameter=None)

Read/Write OpenWind Script File
Read
..module:: openwind.rwScriptXML
..function:: parseScript(fname, debug=False)
..function:: rdScript(fname, debug=False)
Write
..function:: newScriptTree(rpath)
..function:: makeChWkbkOp(parent,blbpath)
..function:: makeRepTurbOp(parent,tname,tpath)
..function:: makeEnCapOp(parent, wm = "DAWM Eddy-Viscosity" )
..function:: makeOptimiseOp(parent, nIter=None)
..function:: makeOptimizeOp(parent, nIter=None)
..function:: makeOptCostEnergyOp(parent)
..function:: makeExitOp(parent)
..function:: makeEnableOp(parent, siteName, enable=True)
..function:: wrtScript(scripttree, ofname, addCols=False)

OpenWind Utilities
..module:: openwind.openWindUtils
..class:: owWindTurbine
..function:: rdReport(rptpath, debug=False)
..module:: openwind.getworkbookvals
..function:: getTurbPos(workbook, owexe, delFiles=True)
..function:: getEC(workbook, owexe, delFiles=True)


.. currentmodule:: openwind.academic.openwindAC_assembly

Documentation for openwind_assembly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following inputs and outputs are defined for openwindAC_assembly:

.. literalinclude:: ../src/openwind/academic/openwindAC_assembly.py
    :language: python
    :start-after: openwindAC_assembly(GenericAEPModel)
    :end-before: def __init__(self, ssfile)
    :prepend: class openwindAC_assembly(Assembly):

Referenced Energy Production Modules
===========================================
.. module:: openwind.academic.openwindAC_assembly
.. class:: openwindAC_assembly

Supporting Models for OpenWind Academic
==========================================
.. module:: openwind.academic.openWindAcComponent
.. class:: OWACcomp

.. module:: openwind.academic.openWindPlantComponent
.. class:: PlantFromPosFile
.. class:: PlantFromOWWorkbook

.. module:: openwind.academic.wtlayoutComponents
.. class:: WTPupdate
.. class:: WTLupdate

.. module:: openwind.academic.owAcademicUtils
.. class:: MyNotifyMLHandler
.. function:: waitForNotify(watchFile='notifyML.txt', path='.', callback=None, debug=False)
.. function:: writePositionFile(wt_positions, debug=False, path=None
.. function:: logPositions(wt_positions, ofname=None)
.. function:: writeNotify(path=None, debug=False)
.. function:: parseACresults(fname='results.txt', debug=False)
.. class:: WTPosFile
.. class: WTWkbkFile


