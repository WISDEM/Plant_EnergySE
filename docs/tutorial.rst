.. _tutorial-label:

.. currentmodule:: plant_costsse.docs.examples.example


Tutorial
--------

Tutorial for NREL_CSM_BOS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As an example of NREL_CSM_BOS, let us simulate balance of station costs for a land-based wind plant.  

The first step is to import the relevant files and set up the component.

.. literalinclude:: examples/example.py
    :start-after: # 1 ---
    :end-before: # 1 ---

The plant balance of station cost model relies on some turbine as well as plant input parameters that must be specified.

.. literalinclude:: examples/example.py
    :start-after: # 2 ---
    :end-before: # 2 ---

We can now evaluate the plant balance of station costs.

.. literalinclude:: examples/example.py
    :start-after: # 3 ---
    :end-before: # 3 ---

We then print out the resulting cost values

.. literalinclude:: examples/example.py
    :start-after: # 4 ---
    :end-before: # 4 ---

The result is:

>>>BOS cost offshore: 766464743.6
>>>BOS cost per turbine: 7664647.4

Next we repeat the process but change the input settings for an land-based wind plant.

.. literalinclude:: examples/example.py
    :start-after: # 5 ---
    :end-before: # 5 ---

The new result is:

>>> BOS cost onshore: 308453311.9
>>> BOS cost per turbine: 3084533.1


Tutorial for NREL_CSM_OM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As an example of NREL_CSM_OM, let us simulate operational expenditures for a land-based wind plant.  

The first step is to import the relevant files and set up the component.

.. literalinclude:: examples/example.py
    :start-after: # 6 ---
    :end-before: # 6 ---

The plant operational expenditures model relies on some turbine as well as plant input parameters that must be specified.

.. literalinclude:: examples/example.py
    :start-after: # 7 ---
    :end-before: # 7 ---

We can now evaluate the plant operational expenditures.

.. literalinclude:: examples/example.py
    :start-after: # 8 ---
    :end-before: # 8 ---

We then print out the resulting cost values

.. literalinclude:: examples/example.py
    :start-after: # 9 ---
    :end-before: # 9 ---

The result is:

>>>OM offshore 48839574.1

>>>OM by turbine 374228.7

>>>LRC by turbine 93467.7

>>>LLC by turbine 20699.3

Next we repeat the process but change the input settings for an land-based wind plant.

.. literalinclude:: examples/example.py
    :start-after: # 10 ---
    :end-before: # 10 ---

The new result is:

>>>OM offshore 21512056.3

>>>OM by turbine 134162.2

>>>LRC by turbine 60258.9

>>>LLC by turbine 20699.3

Tutorial for ECN_Offshore_OM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As an example of ECN_Offshore_OM, let us simulate operational expenditures for an offshore wind plant.  

The first step is to import the relevant files and set up the component.  Note that the location of the ECN model must be specified as an input to the wrapper.

.. literalinclude:: examples/example.py
    :start-after: # 11 ---
    :end-before: # 11 ---

The plant operational expenditures model relies on some turbine as well as plant input parameters that must be specified.

.. literalinclude:: examples/example.py
    :start-after: # 12 ---
    :end-before: # 12 ---

We can now evaluate the plant operational expenditures.

.. literalinclude:: examples/example.py
    :start-after: # 13 ---
    :end-before: # 13 ---

We then print out the resulting cost values

.. literalinclude:: examples/example.py
    :start-after: # 14 ---
    :end-before: # 14 ---

The result is:

>>>Availability 94.3%

>>>OnM Annual costs $60080182.5

>>>OM by turbine 56525.7

>>>LRC by turbine 389276.1	

>>>LLC by turbine 105000.0


