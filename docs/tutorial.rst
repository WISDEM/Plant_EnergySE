.. _tutorial-label:

.. currentmodule:: plant_energyse.docs.examples.example


Tutorial
--------

Tutorial for Basic_AEP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As an example of Basic_AEP, let us simulate energy production for a land-based wind plant.  

The first step is to import the relevant files and set up the component.

.. literalinclude:: examples/example.py
    :start-after: # 1 ---
    :end-before: # 1 ---

The plant energy production model relies on some turbine as well as plant input parameters that must be specified.

.. literalinclude:: examples/example.py
    :start-after: # 2 ---
    :end-before: # 2 ---

We can now evaluate the plant energy production.

.. literalinclude:: examples/example.py
    :start-after: # 3 ---
    :end-before: # 3 ---

We then print out the resulting cost values

.. literalinclude:: examples/example.py
    :start-after: # 4 ---
    :end-before: # 4 ---

The result is:

>>>AEP gross output: 1570713782.15

>>>AEP output: 1389359168.87


Tutorial for NREL_CSM_AEP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As an example of NREL_CSM_AEP, let us simulate energy production for a land-based wind plant.  

The first step is to import the relevant files and set up the component.

.. literalinclude:: examples/example.py
    :start-after: # 5 ---
    :end-before: # 5 ---

The plant energy production model relies on some turbine as well as plant input parameters that must be specified.

.. literalinclude:: examples/example.py
    :start-after: # 6 ---
    :end-before: # 6 ---

We can now evaluate the plant energy production.

.. literalinclude:: examples/example.py
    :start-after: # 7 ---
    :end-before: # 7 ---

We then print out the resulting cost values.

.. literalinclude:: examples/example.py
    :start-after: # 8 ---
    :end-before: # 8 ---

The result is:

>>>5 MW Reference Turbine

>>>rated rotor speed: 12.126

>>>rated wind speed: 11.506

>>>maximum efficiency: 0.902

>>>gross annual energy production: 0.0

>>>annual energy production: 0.0

>>>Power Curve:

>>>[[4.0 80.0]

>>>[2.5 5000.0]]

