
import collections
import string
import keyword


def normalise(name):
    """
    normalises a name

    Parameters
    ----------
    name : any
        name to be normalised

    Returns
    -------
    normalised name : str

    Notes
    -----
    Normalising is used to make an item name ready to be used as an attribute
    First, the name is converted to a string
    Then, any characters that are not a letter, digit or underscore are substituted by a _
    Finally if the name is the null string, starts with a digit or is a keyword, an underscore is prepended.
    All floats without a decimal part, are converted to an underscore plus their 'integer' string, like
    1234.0 is converted to '_1234'.

    Examples
    --------
    normalise('a') --> 'a'
    normalise('thisisalongname') --> 'thisisalogname'
    normalise('short name') --> 'short_name'  # blank translated to _
    normalise('who are you?') --> 'who_are_you_'  # everything that's not a letter, digit or _ is translated to _
    normalise('3') --> '_3'  # name starts with a digit
    normalise(3) --> '_3'  # name starts with a digit
    normalise(0) --> '_0'  # name starts with a digit``
    normalise(False) --> '_False'  # False is a keyword
    normalise(True) --> '_True1'  # True is a keyword
    normalise(1234.0) --> '_1234'  # 1234.0 == hash(1234.0) and hash(1234.0) gives 1234
    normalise('else') --> '_else'  # 'else' is a keyword
    normalise('True') --> '_True'  # 'True' is a keyword
    """
    if name == hash(name):
        if not (name is True or name is False):  # is is essential
            name = hash(name)
    name = str(name)
    name = "".join(c if c in string.ascii_letters + string.digits + "_" else "_" for c in name)
    if not name or name[0] in string.digits or keyword.iskeyword(name):
        name = "_" + name
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
    def __init__(self, *args, **kwargs):
        self.setattr_direct('_alias', {})
        super().__init__(*args, **kwargs)

    def save(self, name, value):
        pass

    def __setattr__(self, name, value):
        if name == "data":
            return super().__setattr__(name, value)
        if name in self.data:
            if name in (0, 1):
                for alias_name in self._alias:
                    if alias_name is str(name):  # is is essential
                        alias_set = False
                        break
                else:
                    alias_set = True
            else:
                alias_set = False
            if not alias_set:
                super().__setitem__(name, value)
                self.save(name, value)
                return
        if name in self._alias:
            super().__setitem__(self._alias[name], value)
            self.save(self._alias[name], value)
            return
        norm_name = normalise(name)
        if norm_name != name:
            if norm_name in self.data:
                raise AttributeError(f"already defined by {repr(norm_name)}")
            if norm_name in self._alias:
                if self._alias[norm_name] != name:
                    raise AttributeError(f"already defined by {repr(self._alias[norm_name])}")
            self._alias[norm_name] = name
        super().__setitem__(name, value)
        self.save(name, value)

    __setitem__ = __setattr__

    def setattr_direct(self, name, value):
        '''
        sets an attribute directly, i.e. without making it into an item
        this can be useful to store save data (see the test script)
        used internally to create the _alias dict

        Parameters
        ----------
        name : str
            name of attribute to be set

        value : any
            value of the attribute

        Returns
        -------
        None

        Notes
        -----
        Attributes set via setattr_direct will -by nature- not be appear in the result of repr().
        But, they will be included in the result of str().
        '''

        super().__setattr__(name, value)

    def _getattr_item(self, name, exception):
        try:
            return super().__getitem__(name)
        except KeyError:
            norm_name = normalise(name)
            if norm_name in self._alias:
                return self[self._alias[norm_name]]
            raise exception

    def __getattr__(self, name):
        if name in vars(self):
            return self.__getattr__(name)
        else:
            return self._getattr_item(name, AttributeError)

    def __getitem__(self, name):
        return self._getattr_item(name, KeyError)

    def __repr__(self):
        parts = []
        for k, v in self.data.items():
            any_alias = False
            for ak, av in self._alias.items():
                if k == av:
                    parts.append(f"({repr(av)}, {v})")
                    any_alias = True
            if not any_alias:
                parts.append(f"({repr(k)}, {v})")
        return (f"{self.__class__.__name__}([{', '.join(parts)}])")

    def __str__(self):
        result = [__class__.__name__]
        id = "x"
        for k, v in self.data.items():
            parts = [f"    {id}[{repr(k)}] == "]
            for ak, av in self._alias.items():
                if k == av:
                    parts.append(f"{id}[{repr(ak)}] == ")
            for ak, av in self._alias.items():
                if k == av:
                    parts.append(f"{id}.{ak} == ")
            if len(parts) == 1:  # no aliases found
                parts.append(f"{id}.{k} == ")
            parts.append(f"{repr(v)}")
            result.append("".join(parts))
        for k, v in vars(self).items():
            if k not in ('data', '_alias'):
                result.append(f"    {id}.{k} == {repr(v)}")
        return "\n".join(result)

    def __eq__(self, other):
        if isinstance(other, CleverDict):
            return vars(self) == vars(other)
        return NotImplemented

if __name__ == "__main__":
    x =CleverDict()
    x[True] = 1
    x[1] = 2
    x[False]  = 3
    x[0] = 4
    print(vars(x))
    print(x)

    x =CleverDict()
    x[1] = 1
    x[True] = 2
    x[0] = 3
    x[False] = 4
    x[1] = 1
    x[True] = 2
    x[0] = 3
    x[False] = 4
    x['a'] = 2
    x[2] = 3
    x[2.] =4
    print(vars(x))
    print(x)
    print(repr(x))
    y = eval(repr(x))
    print(x==y)
