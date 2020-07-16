import inspect
import keyword
import itertools

__version__ = "1.5.21"

'''
Change log
==========

version 1.5.21  2020-97-16
-------------------------
__str__ now defaults to __repr__
Added .info() method for displaying summary previously returned by __str__
get_key() reinstated.
Parameters added to main CleverDict class Docstring.
Methods grouped and sorted by dunder, private, public.
name_to_aliases renamed all_aliases

version 1.5.2  2020-97-15
-------------------------

Wording of Docstrings, README, and tests updated.
expand (class) now upper-case e.g. "Expand" to distinguish from .expand.
get_key other internal methods renamed to private functions e.g. _get_key

version 1.5.1  2020-07-02
-------------------------
First version with the change log.

Removed the no_expand context manager and introduced a more logical expand context manager. The context
manager now restores the CleverDict.expand setting correctly upon exiting.

Expansion can now be controlled by CleverDict.expand, instead of cleverdict.expand.

The __repr__ method now provides the vars as well, thus showing attributes set with set_attr_direct also
The __repr__ method output is more readable

In order to support evalation from __repr__, the __init__ method has been changed.

The implemenation of several methods is more compact and more stable by reusing functionality.

More and improved tests.
'''

class Expand:
    def __init__(self, ok):
        """
        Provides a context manager to temporary disable expansion of keys.
        upon exiting the context manager, the value of expand is restored.

        Parameters
        ----------
        ok : bool
           if True, enabled expansion
           if False, disable expansion
        """
        self.ok = ok

    def __enter__(self):
        self.save_expand = CleverDict.expand
        CleverDict.expand = self.ok

    def __exit__(self, *args):
        CleverDict.expand = self.save_expand

class CleverDict(dict):
    """
    A data structure which allows both object attributes and dictionary
    keys and values to be used simultaneously and interchangeably.

    Parameters
    ----------
    The same as dict i.e.:

        CleverDict() -> new empty Clever Dictionary.
        CleverDict(mapping) -> new Clever Dictionary initialized from a mapping
        object's (key, value) pairs.
        CleverDict(iterable) -> new Clever Dictionary initialized as if via:
            d = {}
            for k, v in iterable:
                d[k] = v
        CleverDict(**kwargs) -> new Clever Dictionary initialized with the
        name=value pairs in the keyword argument list.  For example:
        CleverDict(one=1, two=2)

    On top of that there are two extra positional parameters which are
    primarily for evalation of the result of a __repr__ call:

    _aliases : dict
        a dictionary that contains items as follows:
            key : name of a (new) alias.
            value : value to which this key belongs. This key *must* be defined!

    _vars : dict
        a dictionary that contains items as follows:
            key: attribute which, when set, will *not* become an item of the Clever Dictionary.
            value : value of this attribute.
    """

    expand = True  # Used by .delete_alias

    def __init__(self, _mapping=(), _aliases=None, _vars={}, **kwargs):
        self.setattr_direct("_aliases", {})
        with Expand(CleverDict.expand if _aliases is None else False):
            self._update(_mapping, **kwargs)
            if _aliases is not None:
                for k, v in _aliases.items():
                    self._add_alias(v, k)
            for k, v in _vars.items():
                self.setattr_direct(k, v)

    def __setattr__(self, name, value):
        if name in self._aliases:
            name = self._aliases[name]
        elif name not in self:
            for al in all_aliases(name):
                self._add_alias(name, al)
        super().__setitem__(name, value)
        self.save(name, value)

    __setitem__ = __setattr__

    def __getitem__(self, name):
        name = self.get_key(name)
        return super().__getitem__(name)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(e)

    def __delitem__(self, key):
        key = self.get_key(key)
        super().__delitem__(key)
        for ak, av in list(self._aliases.items()):
            if av == key:
                del self._aliases[ak]

    def __delattr__(self, k):
        try:
            del self[k]
        except KeyError as e:
            raise AttributeError(e)

    def __eq__(self, other):
        if isinstance(other, CleverDict):
            return self.items() == other.items() and vars(self) == vars(other)
        return NotImplemented

    def __repr__(self):
       _mapping = dict(self.items())
       _aliases = {k: v for k, v in self._aliases.items() if k not in self}
       _vars = {k: v for k,v in vars(self).items() if k != '_aliases'}
       return f"{self.__class__.__name__}({repr(_mapping)}, _aliases={repr(_aliases)}, _vars={repr(_vars)})"

    def _add_alias(self, name, alias):
        """
        Internal method for error handling while adding and alias, and finally
        adding to .alias.

        Used by add_alias, __init__ and __setattr__.
        """
        if alias in self._aliases and self._aliases[alias] != name:
            raise KeyError(f"{repr(alias)} already an alias for {repr(self._aliases[alias])}")
        self._aliases[alias] = name

    def _update(self, _mapping=(), **kwargs):
        """
        Finally updates the objects values according to a mapping or iterable."""
        if hasattr(_mapping, "items"):
            _mapping = getattr(_mapping, "items")()

        for k, v in itertools.chain(_mapping, getattr(kwargs, "items")()):
            self.__setitem__(k, v)

    @classmethod
    def fromkeys(cls, keys, value):
        """
        Instantiates an object using supplied keys/aliases and values e.g.

        >>> x = CleverDict().fromkeys(["Abigail", "Tino", "Isaac"], "Year 9")

        """
        return CleverDict({k: value for k in keys})

    def save(self, name, value):
        pass

    def setattr_direct(self, name, value):
        """
        Sets an attribute directly, i.e. without making it into an item.
        This can be useful to store save data.

        Used internally to create the _aliases dict.

        Parameters
        ----------
        name : str
            name of attribute to be set

        value : any
            value of the attribute

        Returns
        -------
        None
        """
        super().__setattr__(name, value)

    def get_key(self, name):
        """
        Returns the primary key for a given name.

        Parameters
        ----------
        name : any
            name to be searched

        Returns
        -------
        key where name belongs to : any

        Notes
        -----
        If name can't be found, a KeyError is raised
        """
        if name in self._aliases:
            return self._aliases[name]
        raise KeyError(name)

    _default = object()

    def get_aliases(self, name=_default):
        """
        Returns all alliases or aliases for a given name.

        Parameters
        ----------
        name : any
            name to be given aliases for
            if omitted, all aliases will be returned

        Returns
        -------
        aliases : list
            list of aliases
        """
        if name is CleverDict._default:
            return list(self._aliases.keys())
        else:
            return [ak for ak, av in self._aliases.items() if av == self.get_key(name)]

    def add_alias(self, name, alias):
        """
        Adds an alias to a given key/name.

        Parameters
        ----------
        name : any
            must be an existing key or an alias

        alias : scalar or list of scalar
            alias(es) to be added to the key

        Returns
        -------
        None

        Notes
        -----
        No change if alias already refers to a key in 'name'.
        If alias already refers to a key not in 'name', a KeyError will be raised.
        """

        key = self.get_key(name)
        if not hasattr(alias, "__iter__") or isinstance(alias, str):
            alias = [alias]
        for al in alias:
            for name in all_aliases(al):
                self._add_alias(key, name)

    def delete_alias(self, alias):
        """
        deletes an alias

        Parameters
        ----------
        alias : scalar or list of scalars
            alias(es) to be deleted

        Returns
        -------
        None

        Notes
        -----
        If .exapand == True (the 'normal' case), .delete_alias will remove all
        the specified alias AND all other aliases (apart from the original key).
        If .exapand == False (most likely set via the Expand context manager),
        .delete_alias will only remove the alias specified.

        Keys cannot be deleted.
        """
        if not hasattr(alias, "__iter__") or isinstance(alias, str):
            alias = [alias]
        for al in alias:
            if al not in self._aliases:
                raise KeyError(f"{repr(al)} not present")
            if al in self:
                raise KeyError(f"primary key {repr(al)} can't be deleted")
            del self._aliases[al]
            for alx in all_aliases(al):
                if alx in list(self._aliases.keys())[1:]:  # ignore the key, which is at the front of ._aliases
                    del self._aliases[alx]

    def info(self, **kwargs):
        frame = inspect.currentframe().f_back.f_locals
        self_value = locals()["self"]
        # If more than one variable has the same value, use the most recent [-1]
        ids = [k for k, v in frame.items() if v == self_value]
        result = [__class__.__name__ + ": " + "\n" + " == ".join(ids) + "\n"]
        id = ids[-1]
        for k, v in self.items():
            parts = []
            with Expand(True):
                for ak in all_aliases(k):
                    parts.append(f"{id}[{repr(ak)}] == ")
                for ak in all_aliases(k):
                    if isinstance(ak, str) and ak.isidentifier() and not keyword.iskeyword(ak):
                        parts.append(f"{id}.{ak} == ")
            parts.append(f"{repr(v)}")
            result.append("".join(parts))
        for k, v in vars(self).items():
            if k not in ("_aliases"):
                result.append(f"{id}.{k} == {repr(v)}")
        output = "\n".join(result)
        if kwargs.get("noprint"):
            return output
        else:
            print(output)

def all_aliases(name):
    """
    Returns all possible aliases for a given name.

    Parameters
    ----------
    name : any

    Return
    ------
    Aliases for name : list

    By default the list will start with name, followed by all possible aliases for name.  However if CleverDict.expand == False, the list will only contain name.

    CleverDict.expand should preferably be set via the context manager Expand.
    """
    result = [name]
    if CleverDict.expand:
        if name == hash(name):
            result.append(f"_{int(name)}")
            if name in (0, 1):
                result.append(f"_{bool(name)}")
        else:
            if name != str(name):
                name = str(name)
                if name.isidentifier() and not keyword.iskeyword(name):
                    result.append(str(name))

            if not name or name[0].isdigit() or keyword.iskeyword(name):
                norm_name = "_" + name
            else:
                norm_name = name

            norm_name = "".join(ch if ("A"[:i] + ch).isidentifier() else "_" for i, ch in enumerate(norm_name))
            if name != norm_name:
                result.append(norm_name)
    return result

if __name__ == "__main__":
    pass

