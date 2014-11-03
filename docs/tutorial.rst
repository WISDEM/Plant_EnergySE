.. _tutorial-label:

.. currentmodule:: plant_energyse.docs.examples.example


Tutorial
--------


Tutorial for NREL_CSM_AEP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As an example of NREL_CSM_AEP, let us simulate energy production for a land-based wind plant.  

The first step is to import the relevant files and set up the component.

.. literalinclude:: examples/example.py
    :start-after: # 5 ---
    :end-before: # 5 ---

The plant energy production model relies on some turbine as well as plant input parameters that must be specified.  These include main turbine parameters including the machine rating, rotor diameter, maximum allowable tip speed, drivetrain design, hub height, cut-in and cut-out speed as well as optimum tip speed ratio, rated power thrust coefficient and maximum power coefficient.  Plant inputs include the overall turbine number and plant resource characteristics including the shear exponent, 50 m annual average wind speed, the weibull distribution shape factor and plant loss information including soiling losses, array losses and availability.

.. literalinclude:: examples/example.py
    :start-after: # 6 ---
    :end-before: # 6 ---

We can now evaluate the plant energy production.

.. literalinclude:: examples/example.py
    :start-after: # 7 ---
    :end-before: # 7 ---

We then print out the resulting energy production values.

.. literalinclude:: examples/example.py
    :start-after: # 8 ---
    :end-before: # 8 ---

The result is:

>>> Annual energy production for an offshore wind plant with 100 NREL 5 MW reference
 turbines.
>>> AEP gross output (before losses): 1986524060.9 kWh
>>> AEP net output (after losses): 1760663682.8 kWh
>>> Rated rotor speed: 12.13 rpm
>>> Rated wind speed: 11.51 m/s


Tutorial for Openwind
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here we provide a tutorial for the Openwind Enterprise version wrapper.  For the academic version, the user is referred to the example in the source code.

First we need to import the wrapper module.  

.. literalinclude:: examples/example.py
    :start-after: # 9 ---
    :end-before: # 9 ---

Then we need to specify the workbook file we are working from as well as the default turbine in that workbook and the script file we are using for our analysis.  

.. literalinclude:: examples/example.py
    :start-after: # 10 ---
    :end-before: # 10 ---

The plant energy production model relies on some turbine as well as plant input parameters that must be specified.  The workbook contains most of the relevant information is already included but we are able to update the turbine description including its power, thrust and rotor speed curve.

.. literalinclude:: examples/example.py
    :start-after: # 11 ---
    :end-before: # 11 ---

We can now evaluate the plant energy production.

.. literalinclude:: examples/example.py
    :start-after: # 12 ---
    :end-before: # 12 ---

We then print out the resulting energy production values.

.. literalinclude:: examples/example.py
    :start-after: # 13 ---
    :end-before: # 13 ---

The result is:

>>> Openwind assembly output:
>>>  AEP gross output (before losses): 49845.4 kWh
>>>  Array losses: 1.47 %
>>>  Array energy production: 49112.0 kWh
>>>  Other losses: 12.32 %
>>>  AEP net output: (after losses) 43059.4 kWh
>>>  Capacity factor: 40.93 %


