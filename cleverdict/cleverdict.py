import os
import json
import inspect
import keyword
import itertools
import click  # used to get cross-platform folder path for config file
from pathlib import Path
from datetime import datetime

"""
Change log
==========

version 1.7.4 2021-01-20
------------------------
Auto-delete feature implemented:
https://github.com/PFython/cleverdict/issues/11
Auto-save to json config file implemented:
https://github.com/PFython/cleverdict/issues/10


version 1.7.2 2020-11-03
--------------------------
Removed .fromlist (__init__ does the job!)
Updated test_cleverdict.py
Updated README
Updated setup.py to correct support for Python 3.6+

version 1.7.0 2020-11-01
--------------------------
Added methods .fromlist and .to_list
Updated test_cleverdict.py
Updated README
Updated setup.py to show support for Python 3.2+

version 1.6.0
--------------------------
Updated README

version 1.5.3  2020-07-17
--------------------------
The method info() now sorts the names alphabetically, and uses the first to show the structure.
If no name matches, the name x is used now (that used to cause a crash)
Added tests for info()


version 1.5.24  2020-07-16
--------------------------
Docstring added for info()
info() now tests and reports x is y not x == y

version 1.5.23  2020-07-16
--------------------------
_update renamed back to update
info(noprint=True) changed to info(as_str=True)
test added for info

version 1.5.22  2020-07-16
--------------------------
README updated
example_save_function includes line spaces and prints output
Methods grouped and sorted by dunder, private, public.
name_to_aliases renamed: all_aliases

version 1.5.21  2020-07-16
--------------------------
__str__ now defaults to __repr__
Added .info() method for displaying summary previously returned by __str__
get_key() reinstated.
Parameters added to main CleverDict class Docstring.

version 1.5.2  2020-07-15
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
"""


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

    KWARGS:

    json_save : overwrite .save and auto-save changes to JSON config file
    json_load : load values from existing JSON config file
    """

    expand = True  # Used by .delete_alias
    never_save = "password PASSWORD Password".split()

    def __init__(self, _mapping=(), _aliases=None, _vars={}, **kwargs):
        self.setattr_direct("_aliases", {})
        with Expand(CleverDict.expand if _aliases is None else False):
            self.update(_mapping, **kwargs)
            if _aliases is not None:
                for k, v in _aliases.items():
                    self._add_alias(v, k)
            for k, v in _vars.items():
                self.setattr_direct(k, v)
        CleverDict.original_save = self.save  # create a copy
        CleverDict.original_delete = self.delete  # create a copy

    def autosave(self, setting, path = None):
        """ Toggles autosave to a JSON config file ON (True) / OFF (False) """
        if path is None and not hasattr(self, "json_path"):
            path = self.get_default_settings_path()
            self.setattr_direct("json_path", Path(path))
        if setting.lower() == "json":
            CleverDict.save = CleverDict.save_value_to_json_file
            CleverDict.delete = CleverDict.delete_value_from_json_file
            self.create_json_file()
            print(f"\n⚠ Autosaving to:\n  {self.json_path}")
        if setting.lower() == "off":
            CleverDict.save = CleverDict.original_save
            CleverDict.delete = CleverDict.original_delete
            print("\n⚠ Autosave disabled.\n")
            if hasattr(self, "json_path"):
                print(f"\nⓘ Previous updates saved to:\n  {self.json_path}\n")

    def __setattr__(self, name, value):
        if name in self._aliases:
            name = self._aliases[name]
        elif name not in self:
            for al in all_aliases(name):
                self._add_alias(name, al)
        super().__setitem__(name, value)
        self.save(name, value)  # Call an overwriteable user defined method

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
        self.delete(key)  # Call an overwriteable user defined method

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
        _vars = {k: v for k, v in vars(self).items() if k != "_aliases"}
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

    def update(self, _mapping=(), **kwargs):
        """
        Parameters
        ----------
        The same as dict.update(), i.e.
            D.update([E, ]**F) -> None.  Update D from dict/iterable E and F.
            If E is present and has a .keys() method, then does:  for k in E: D[k] = E[k]
            If E is present and lacks a .keys() method, then does:  for k, v in E: D[k] = v
            In either case, this is followed by: for k in F:  D[k] = F[k]
        """
        if hasattr(_mapping, "items"):
            _mapping = getattr(_mapping, "items")()

        for k, v in itertools.chain(_mapping, getattr(kwargs, "items")()):
            self.__setitem__(k, v)

    @classmethod
    def fromkeys(cls, iterable, value):
        """
        Instantiates an object using supplied keys/aliases and values e.g.

        >>> x = CleverDict().fromkeys(["Abigail", "Tino", "Isaac"], "Year 9")

        Parameters
        ----------
        iterable: iterable
            used as the keys for the new CleverDict

        value: any
            used as the values for the new CleverDict

        Returns
        -------
        New CleverDict with keys from iterable and values equal to value.

        """
        return CleverDict({k: value for k in iterable})

    def to_list(self):
        """
        Creates a (json-serialisable) list of k,v pairs as a list of tuples.
        Main use case is Client/Server apps where returning a CleverDict object
        or a dictionary with numeric keys (which get converted to strings by
        json.dumps for example).  This output can be used to instantiate a new
        CleverDict object (e.g. when passing between Client/Server code) using
        the .fromlist() method.

        Returns
        -------
        A list of k,v pairs as a list of tuples e.g.
        [(1, "one"), (2, "two")]

        """
        return list(self.items())

    def get_default_settings_path(self):
        """
        Get Operating System specific default for settings folder;
        Return a (hopefully) unique filename comprising time and variable name

        e.g. 2020-12-06-03-30-57-89[x].json
        """
        # Get a timestamp
        t = ''.join([x if x.isnumeric() else "-" for x in str(datetime.now())])
        # Get the most recently assigned object name
        frame = inspect.currentframe().f_back.f_locals
        id = [k for k, v in frame.items() if v is self][-1]
        id = f"{t[:-4]}[{id}].json"
        return Path(click.get_app_dir("CleverDict")) / id

    def load_from_json_file(self, path = None):
        """
        ⚠ CAUTION ⚠
        Loads the contents of a pre-existing config file as attributes
        Overwrites the value of any duplicate keys found.
        """
        if path is None:
            if hasattr(self, json_path):
                path = self.json_path
            else:
                path = get_default_settings_path()
                # json_path is NOT set as this object doesn't isn't necessarily
                # the owner of the config file
        with open(path, "r") as file:
            values = json.load(file)
        for key, value in values.items():
            setattr(self, key, value)

    def create_json_file(self):
        """
        Uses click to find & create a platform-appropriate easyPyPI folder, then
        creates a skeleton json file there to store persistent data (if one
        doesn't already exist, or if the current one is empty).
        """
        try:
            os.makedirs(self.json_path.parent)
            print(f"\nⓘ Folder created:\n {self.json_path.parent}")
        except FileExistsError:
            pass
        with open(self.json_path, "w") as file:
            json.dump({}, file)  # Create skeleton .json file
        print(f"\nⓘ Created a new config file:\n {self.json_path}")

    def to_json(self, never_save = False, **kwargs):
        """
        Return CleverDict serialised to JSON.

        KWARGS
        never_save: Exclude field in CleverDict.never_save if True eg passwords
        file: Save to file if True or filepath

        """
        # .get_aliases finds attributes created after __init__:
        fields_dict = {key: self.get(key) for key in self.get_aliases()}
        if never_save:
            fields_dict = {k:v for k,v in fields_dict if k not in never_save}
        json_str = json.dumps(fields_dict)
        path = kwargs.get("file")
        if path:
            path = Path(path)
            with open(path, "w") as file:
                file.write(json_str)
            if CleverDict.save is not CleverDict.save_value_to_json_file:
                # Avoid spamming confirmation messages
                frame = inspect.currentframe().f_back.f_locals
                ids = [k for k, v in frame.items() if v is self]
                ids = ids[0] if len(ids) == 1 else "/".join(ids)
                print(f"\nⓘ Saved '{ids}' in JSON format to:\n {path.absolute()}")
        return json_str

    def save_value_to_json_file(self, key = None, value = None):
        """
        If .autosave("json") is called on an object, this overwrites
        the default .save() method and is called every time a value changes or
        is created.

        This new method is used to update a json config file automatically.

        If no valid Path is supplied, a default, operating system specific path
        will be created using click.

        NB JSON can only serialise certain datatypes.  Python sets, for example,
        are not currently supported.
        """
        if not hasattr(self, "json_path"):
            path = self.get_default_settings_path()
            self.setattr_direct("json_path", Path(path))
            self.create_json_file()
        self.to_json(file=self.json_path)
        if key:
            if key in CleverDict.never_save:
                location = "memory but NOT saved to file"
            else:
                location = self.json_path # self["json_path"]
            # Comment out if confirmation not required:
            print(f"\n✓ .{key} updated in {location}")
        # TODO: Check for common unsupported types and convert to/from strings

    def save(self, name, value):
        """
        Called every time a CleverDict value is created or change.
        Overwrite with your own custome save() method e.g. to automatically
        write values to file/database/cloud, send a notification etc.

        CleverDict.delete = custom_save_method
        """
        pass

    def delete_value_from_json_file(self, key):
        """
        If .autosave("json") is called on an object, this overwrites
        the default .delete() method and is called every time a value is
        deleted.

        This new method is used to update a json config file automatically.

        If no valid Path is supplied, a default, operating system specific path
        will be created using click.
        """
        self.to_json(file=self.json_path)
        if key in CleverDict.never_save:
            location = "memory and was never saved to file"
        else:
            location = self.json_path # self["json_path"]
        # Comment out if confirmation not required:
        print(f"\n✓ .{key} deleted from {location}")

    def delete(self, name):
        """
        Called every time a CleverDict value is deleted.  Overwrite with your
        own custome delete() method e.g. to automatically delete values from
        file/database/cloud, send a confirmation request/notification etc.

        CleverDict.delete = custom_delete_method
        """
        pass

    def delete_json(self):
        """
        ⚠ CAUTION ⚠
        Deletes the CleverDict json file e.g. in case of corruption.
        Creating a new CleverDict object will automatically recreate a fresh one.
        """
        os.remove(self.json_path)

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

    def identify_self(self):
        """ Identifies names and aliases of current CleverDict instance """
        frame = inspect.currentframe().f_back.f_locals
        return sorted(k for k, v in frame.items() if v is self)

    def info(self, as_str=False):
        """
        Prints or returns a string showing variable name equivalence
        and object attribute/dictionary key equivalence.
        """
        indent = "    "
        frame = inspect.currentframe().f_back.f_locals
        ids = sorted(k for k, v in frame.items() if v is self)
        result = [__class__.__name__ + ":"]
        if ids:
            if len(ids) > 1:
                result.append(indent + " is ".join(ids))
            id = ids[0]  # If more than one variable has the same name, use the first in the list
        else:
            id = "x"
        for k, v in self.items():
            parts = []
            with Expand(True):
                for ak in all_aliases(k):
                    parts.append(f"{id}[{repr(ak)}] == ")
                for ak in all_aliases(k):
                    if isinstance(ak, str) and ak.isidentifier() and not keyword.iskeyword(ak):
                        parts.append(f"{id}.{ak} == ")
            parts.append(f"{repr(v)}")
            result.append(indent + "".join(parts))
        for k, v in vars(self).items():
            if k not in ("_aliases"):
                result.append(f"{indent}{id}.{k} == {repr(v)}")
        output = "\n".join(result)
        if as_str:
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

    By default the list will start with name, followed by all possible aliases for name.
    However if CleverDict.expand == False, the list will only contain name.

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
