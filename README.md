A data structure which allows both object attributes and dictionary
keys and values to be used simultaneously and interchangeably.

The save() method (which you can adapt or overwrite) is called whenever
an attribute or dictionary value changes.  Useful for automatically writing
results to a database, for example.

Convert an existing dictionary or UserDict to CleverDict:
    x = CleverDict(my_existing_dict)

Import data from an exiting object to a CleverDict:
    x = CleverDict(vars(my_existing_object))

Created by Peter Fison, Ruud van der Ham, Loic Domaigne, and Rik Huygen
from pythonistacafe.com, hoping to improve on a similar feature in Pandas.
