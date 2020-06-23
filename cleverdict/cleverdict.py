
import collections
import string

def normalise(name):
    """
    Replaces all characters that are not letters, digits or _ with an underscore.  If the resulting string then starts with a digit or is empty, it prepends it with an underscore.
    """
    for case, replacement in {"": "_nullstring", " ": "_space"}.items():
        name = replacement if name == case else name
    name = str(name)
    name = ''.join(c if c in string.ascii_letters + string.digits + '_' else '_' for c in name)
    if not name or name[0] in string.digits:
        name = '_' + name
    return name

class CleverDict(collections.UserDict):
    """
    A data structure which allows both object attributes and dictionary
    keys and values to be used simultaneously and interchangeably.

    The save() method (which you can adapt or overwrite) is called whenever
    an attribute or dictionary value changes.  Useful for automatically writing
    results to a database, for example:

        from cleverdict.test_cleverdict import my_example_save_function
        CleverDict.save = my_example_save_function

    Convert an existing dictionary or UserDict to CleverDict:
        x = CleverDict(my_existing_dict)

    Import data from an existing object to a CleverDict:
        x = CleverDict(vars(my_existing_object))

    Created by Peter Fison, Ruud van der Ham, Loic Domaigne, and Rik Huygen
    from pythonistacafe.com, hoping to improve on a similar feature in Pandas.
    """

    normalise = True

    def __setitem__(self, name, value,):
        if name=='data':  # required because UserDict defines 'data' internally
            return super().__setattr__(name, value)
        if CleverDict.normalise:
            name = normalise(name)
        super().__setitem__(name, value)
        self._save(name,value)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError

    def _save(self, name, value):
        """ Notional database save or other custom function called here """
        pass

    def __repr__(self):
        return self.__class__.__name__ + '({' + ", ".join(f'{repr(k)}:{repr(v)}' for k,v in vars(self)['data'].items()) + '})'

    def __str__(self):
        return "\n".join([f".{k} = {v} {type(v)}" for k,v in list(vars(self)['data'].items())])

    __setattr__ = __setitem__



