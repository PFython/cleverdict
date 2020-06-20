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
        if type(name) == int:  # Python objects can't have numeric attributes
            name = "_" + str(name)
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

    __setattr__ = __setitem__

def my_example_save_function(self, name: str = "", value: any = ""):
    """
    Example of a custom function which can be called by self._save()
    whenever the value of a CleverDict instance is created or changed.

    Required arguments are: self, name: str and value: any

    Specify this (or any other) function as the default 'save' function as follows:

    CleverDict.save = my_example_save_function

    NB this works at the class level, so changing CleverDict.save will overwrite
    the save method of all previously created CleverDict objects as well.

    If you need to specify different .save functions for different instances,
    consider creating sublasses that inherit from CleverDict and set a new
    .save function for each subclass.
    """
    output=f"Notional save to database: .{name} = {value} {type(value)}\n"
    print(output)
    with open("example.log","a") as file:
        file.write(output)
