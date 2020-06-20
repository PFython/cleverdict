# __init__.py
__version__ = "0.1"

import collections

class CleverDict(collections.UserDict):
    """
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
    """

    save = None  # Custom 'save' function to call for all class instances

    def __setitem__(self, name, value):
        # Attribute names in Python have some restrictions, so...
        if type(name) == int or name == "":
            name = "_" + str(name)
        # TODO: Further validation e.g. to handle keys like " ", "", "?"
        if name=='data':  # required because UserDict defines 'data' internally
            return super().__setattr__(name, value)
        super().__setitem__(name, value)
        self._save(name,value)

    def __getattr__(self, name):
        try:
            return  collections.UserDict.__getitem__(self, name)
        except KeyError:
            raise AttributeError

    def _save(self, name, value):
        """ Notional database save  or other custom function called here """
        if CleverDict.save:
            CleverDict.save(self, name, value)

    def __repr__(self):
        return self.__class__.__name__ + '({' + ", ".join(f'{repr(k)}:{repr(v)}' for k,v in vars(self)['data'].items()) + '})'

    def __str__(self):
        return "\n".join([f".{k} = {v} {type(v)}" for k,v in list(vars(x)['data'].items())])

    __setattr__ = __setitem__

def my_example_save_function(self, name: str = "", value: any = ""):
    """
    Example of a custom function which can be called by self._save()
    whenever the value of a CleverDict instance is created or changed.

    Required arguments are: self, name: str and value: any

    Specify this (or any other) function as the default 'save' function as follows:

    CleverDict.save = my_example_save_function
    """
    output=f"Notional save to database: .{name} = {value} {type(value)}"
    print(output)
    with open("example.log","a") as file:
        file.write(output)

