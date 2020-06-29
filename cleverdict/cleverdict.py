import keyword
import itertools


def normalise(name):
    """
    This function converts a dictionary key into a valid Python attribute name.

    Parameters
    ----------
    name : any
        name (dictionary key) to be normalised

    Returns
    -------
    normalised name : str

    Notes
    -----
    First, the name is converted to a string.
    All floats without a decimal part, are converted to an underscore plus
    their 'integer' string, e.g. 1234.0 is converted to '_1234'.
    If the string is a keyword, the null string or starts with a digit it is prepended by a "_".
    The characters of the resulting string are then tested individually and if
    it is invalid in an identifier it will be replaced by a "_".
    Note that this test is different for the first character, than the rest.


    Examples
    --------
    normalise('a') --> 'a'
    normalise('thisisalongname') --> 'thisisalongname'
    normalise('short name') --> 'short_name'  # blank translated to _
    normalise('who are you?') --> 'who_are_you_'  # everything that's not a letter, digit or _ is translated to _
    normalise('3') --> '_3'  # name starts with a digit
    normalise(3) --> '_3'  # name starts with a digit
    normalise(0) --> '_0'  # name starts with a digit``
    normalise(False) --> '_False'  # False is a keyword
    normalise(True) --> '_True'  # True is a keyword
    normalise('True') --> '_True'  # 'True' is a keyword
    normalise(1234.0) --> '_1234'  # 1234.0 == hash(1234.0) and hash(1234.0) gives 1234
    normalise('else') --> '_else'  # 'else' is a keyword
    normalise(None) --> '_None'  # None is a keyword
    normalise('None') --> '_None'  # None is a keyword
    normalise('abcве') --> 'abcве'  # unicode is accepted
    normalise('веabc') --> 'веabc'  # unicode is accepted
    """
    if name == hash(name):
        if not (name is True or name is False):  # 'is' is essential
            name = hash(name)
    name = str(name)
    if not name or name[0].isdigit() or keyword.iskeyword(name):
        name = "_" + name

    return "".join(ch if ("A"[:i] + ch).isidentifier() else "_" for i, ch in enumerate(name))


class CleverDict(dict):
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

    def __init__(self, mapping=(), **kwargs):
        self.setattr_direct("_alias", {})
        self.update(mapping, **kwargs)

    def update(self, mapping=(), **kwargs):
        if hasattr(mapping, "items"):
            mapping = getattr(mapping, "items")()
        for k, v in itertools.chain(mapping, getattr(kwargs, "items")()):
            self.__setitem__(k, v)

    @classmethod
    def fromkeys(cls, keys, value):
        x = CleverDict()
        for k in keys:
            x[k] = value
        return x

    def save(self, name, value):
        pass

    def __setattr__(self, name, value):
        if name in self:
            if name in (0, 1):
                for alias_name in self._alias:
                    if alias_name is str(name):  # 'is' is essential
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
            if norm_name in self:
                raise AttributeError(f"duplicate alias already exists for {repr(norm_name)}")
            if norm_name in self._alias:
                if self._alias[norm_name] != name:
                    raise AttributeError(f"duplicate alias already exists for {repr(self._alias[norm_name])}")
            self._alias[norm_name] = name
        super().__setitem__(name, value)
        self.save(name, value)

    __setitem__ = __setattr__

    def setattr_direct(self, name, value):
        """
        Sets an attribute directly, i.e. without making it into an item.
        This can be useful to store save data.  See example in:
        test_cleverdict.Test_Save_Functionality.test_save_misc()

        class SaveDict(CleverDict):
            def __init__(self, *args, **kwargs):
                self.setattr_direct('store', [])
                super().__init__(*args, **kwargs)

            def save(self, name, value):
                self.store.append((name, value))

        Used internally to create the _alias dict.

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
        Attributes set via setattr_direct (including aliases, notably) will
        expressly not be appear in the result of repr().  They will appear in the result of str() however.
        """

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

    def __delitem__(self, k):

        orgk = k
        if k in self._alias:
            k = self._alias[k]
        if k in self:
            super().__delitem__(k)
        else:
            raise KeyError(orgk)
        for ak, av in list(self._alias.items()):
            if av == k:
                del self._alias[ak]

    def __repr__(self):
        parts = []
        for k, v in self.items():
            if type(v) == str:
                v = "'" + v + "'"
            any_alias = False
            for ak, av in self._alias.items():

                if k == av:
                    parts.append(f"({repr(av)}, {v})")
                    any_alias = True
            if not any_alias:
                parts.append(f"({repr(k)}, {v})")
        return f"{self.__class__.__name__}([{', '.join(parts)}])"

    def __str__(self):
        result = [__class__.__name__]
        id = "x"
        for k, v in self.items():
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
            if k not in ("_alias"):
                result.append(f"    {id}.{k} == {repr(v)}")
        return "\n".join(result)

    def __eq__(self, other):
        if isinstance(other, CleverDict):
            return self.items() == other.items() and vars(self) == vars(other)
        return NotImplemented


if __name__ == "__main__":
    x = CleverDict()
    x["abcà"] = 5
    x["1a"] = 6
    x["11a23bccà~£#@q123b/=€впВМвапрй"] = "6"
    x["$a"] = 7
    print(x)
    print(repr(x))
    x = CleverDict({1: "First Entry", " ": "space", "??": "question"})

    print(x)
    x = CleverDict.fromkeys((1, 2, True, "a", "$test"), "YES")
    print(x)
    print(repr(x))
    del x[True]
    del x["_2"]
    #    del x[3]
    x["ветчина_и_яйца$a"] = "ham and eggs"
    print(x)

    tests = normalise.__doc__.split("--------\n")[-1].splitlines()[:-1]
    for test in tests:
        test_case, expected_result = test.split(" --> ")
        argument = eval(test_case.split("(")[1].split(")")[0])
        print(test_case, expected_result)
        print(eval(test_case.strip()), eval(expected_result.strip()))
