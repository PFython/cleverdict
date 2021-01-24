
import os
import json
import inspect
import keyword
import itertools
from pathlib import Path
from datetime import datetime

"""
Change log
==========

version 1.8
---------------------------
Added to_json() and from_json()
Added to_lines() and from_lines()
Removed identify_self()
Reinstated print for autosave (only), but with 'silent' option
to_json(fullcopy=True) creates JSON that can fully recreate a CleverDict
to_json(fullcopy=False) creates JSON from data dictionary only
__delattr__ removes attributes created using setattr_direct
Dependency on click removed
Applied never_save to: to_lines, to_list, to_json
Auto-delete feature implemented:
https://github.com/PFython/cleverdict/issues/11
Auto-save to json file implemented:
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
    """

    expand = True  # Used by .delete_alias
    never_save = "password PASSWORD Password save_path".split()

    def __init__(self, _mapping=(), _aliases=None, _vars={}, **kwargs):
        self.setattr_direct("_aliases", {})
        with Expand(CleverDict.expand if _aliases is None else False):
            self.update(_mapping, **kwargs)
            if _aliases is not None:
                for k, v in _aliases.items():
                    self._add_alias(v, k)
            for k, v in _vars.items():
                self.setattr_direct(k, v)
        # Prevent over-writing class variables when first instance is created:
        for attr in ("original_save", "original_delete"):
            if not hasattr(CleverDict, attr):
                setattr(CleverDict, attr, getattr(self, attr.split("_")[-1]))

    def autosave(self, fullcopy=False, silent=False):
        """ Toggles autosave to a config file.

        Parameters
        ----------

        fullcopy: bool or str
            False -> Autosave using  _auto_save_data
            True -> Autosave using  _auto_save_fullcopy
            "off" -> Turn off autosave and delete .save_path
        silent: bool
            False -> Print confirmations and file path
            True -> No confirmationor file path printed
        """
        if fullcopy == "off":
            try:
                CleverDict.save = CleverDict.original_save
                CleverDict.delete = CleverDict.original_delete
                del self.save_path
                if not silent:
                    print("\n ⚠  Autosave disabled.")
                    print(f"\nⓘ  Previous updates saved to:\n  {self.save_path}\n")
            except AttributeError:
                # Attempting to turn autosave off before it was ever enabled
                return
        else:
            path = self.get("save_path") or self.get_new_save_path()
            path = path.with_suffix(".json")
            self.setattr_direct("save_path", Path(path))
            if not path.is_file():
                self.create_save_file()
            if fullcopy:
                CleverDict.save = CleverDict._auto_save_fullcopy
            else:
                CleverDict.save = CleverDict._auto_save_data
            # Save and delete events trigger a call to the same method:
            CleverDict.delete = CleverDict._auto_delete
            self.save(key=None, value=None)
            if not silent:
                print(f"\n ⚠  Autosaving to:\n  {path}\n")

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
            if hasattr(self, k):
                super().__delattr__(k)
            else:
                raise AttributeError(e)

    def __eq__(self, other):
        if isinstance(other, CleverDict):
            return self.items() == other.items() and vars(self) == vars(other)
        return NotImplemented

    def __repr__(self, ignore=None):
        if ignore is None:
            ignore = set()
        ignore = set(ignore) | {"_aliases", "never_save"}
        _mapping = {k: v for k, v in self.items() if k not in ignore}
        for k, v in self._aliases.items():
            if k in ignore and v in _mapping:
                del _mapping[v]
        _aliases = {k: v for k, v in self._aliases.items() if k not in self and v in _mapping}
        _vars = {k: v for k, v in vars(self).items() if k not in ignore}
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
        return [(k,v) for k,v in self.items() if k not in self.never_save]

    @classmethod
    def get_new_save_path(cls):
        """
        Get Operating System specific default for settings folder;
        Return a (hopefully) unique filename comprising time and variable name

        e.g. 2020-12-06-03-30-57-89[x].json
        """
        # Get a timestamp
        t = "".join([x if x.isnumeric() else "-" for x in str(datetime.now())])
        id = f"{t}.json"
        dir = Path(get_app_dir("CleverDict"))
        if not dir.is_dir():
            dir.mkdir(parents=True)
        return dir / id

    def to_lines(self, file_path=None, start_at=0):
        """
        Creates a line ("\n") delimited object or file using values for lines
        """
        to_save = {k:v for k,v in self.items() if k not in self.never_save}
        lines = "\n".join(itertools.islice(to_save.values(), start_at, None))
        if not file_path:
            return lines
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(lines)

    @classmethod
    def from_lines(cls, lines=None, file_path=None, start_at=0):
        """
        Creates a new CleverDict object and loads data from a line ('\n')
        delimited object or file.

        keys: line numbers, starting Pythonically with zero
        values: line contents (str)
        """
        if lines and file_path:
            raise ValueError("both lines and file_path specified")
        if not (lines or file_path):
            raise ValueError("neither lines nor file_path specified")
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.read()
        index = {k + start_at: v.strip() for k, v in enumerate(lines.split("\n"))}
        return cls(index)


    @classmethod
    def from_json(cls, json_data=None, file_path=None):
        """
        Creates a new CleverDict object and loads data from a JSON object or
        file.
        """
        if json_data and file_path:
            raise ValueError("both json_data and file_path specified")
        if not (json_data or file_path):
            raise ValueError("neither json_data nor file_path specified")

        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = json.loads(json_data)
        try:
            _mapping = {eval(k): v for k,v in data["_mapping_encoded"].items()}
            _aliases = {eval(k): v for k,v in data["_aliases_encoded"].items()}
            _vars = data["_vars"]
            return cls(_mapping, _aliases=_aliases, _vars=_vars)
        except KeyError:
            return(cls(data))

    def create_save_file(self):
        """
        Creates a skeleton to store autosave data if one doesn't already exist.
        """
        if self.save_path.is_file():
            return
        try:
            os.makedirs(self.save_path.parent)
        except FileExistsError:
            pass
        with open(self.save_path, "w", encoding="utf-8") as file:
            file.write('{"empty": True}')  # Create skeleton .json file



    def to_json(self, file_path=None, fullcopy=False):

        """
        Return CleverDict serialised to JSON.

        If never_save is not specified, the class variable .never_save is used

        never_save: Exclude field in CleverDict.never_save if True eg passwords
        file: Save to file if True or filepath

        """
        never_save = set(CleverDict.never_save) | {"_aliases", "never_save"}
        _mapping = {k: v for k, v in self.items() if k not in never_save}
        if not fullcopy:
            json_str = json.dumps(_mapping, indent=4)
        else:
            for k, v in self._aliases.items():
                if k in never_save and v in _mapping:
                    del _mapping[v]
            _aliases = {k: v for k, v in self._aliases.items() if k not in self and v in _mapping}
            _mapping_encoded = {repr(k): v for k, v in _mapping.items()}
            _aliases_encoded = {repr(k): v for k, v in _aliases.items()}
            _vars = {k: v for k, v in vars(self).items() if k not in never_save}
            json_str = json.dumps({'_mapping_encoded':_mapping_encoded, '_aliases_encoded': _aliases_encoded, '_vars':_vars}, indent=4)
        if file_path:
            with open(Path(file_path), "w", encoding="utf-8") as file:
                file.write(json_str)
        else:
            return json_str

    def save(self, name, value):
        """
        Called every time a CleverDict value is created or change.
        Overwrite with your own custome save() method e.g. to automatically
        write values to file/database/cloud, send a notification etc.

        CleverDict.delete = custom_save_method
        """
        pass

    def delete(self, name):
        """
        Called every time a CleverDict value is deleted.  Overwrite with your
        own custome delete() method e.g. to automatically delete values from
        file/database/cloud, send a confirmation request/notification etc.

        CleverDict.delete = custom_delete_method
        """
        pass

    def _auto_save_data(self, key=None, value=None):
        """
        Calls _auto_save_json to save a copy of the data dictionary (only) in
        JSON format, without any mappings, aliases, and directly set attributes.

        If .autosave() is called on an object, this method overwrites the
        default .save() method and is called every time a value changes or is
        created.
        """
        if not hasattr(self, "save_path"):
            # For new instances created while autosave is active
            path = self.get_new_save_path().with_suffix(".json")
            self.setattr_direct("save_path", Path(path))
        self.to_json(file_path=self.save_path)

    def _auto_save_fullcopy(self, key=None, value=None):
        """
        Calls _auto_save_json to save a full copy of the CleverDict instance in
        JSON format, in with all mappings, aliases, and directly set attributes.

        If .autosave(fullcopy=True) is called on an object, this method
        overwrites the default .save() method and is called every time a value
        changes or is created.
        """
        self._auto_save_json(key=key, value=value, fullcopy=True)

    def _auto_save_json(self, key=None, value=None, fullcopy=False):
        """
        If .autosave("json") is called on an object, this overwrites
        the default .save() method and is called every time a value changes or
        is created.

        NB JSON can only serialise certain datatypes.  Python sets, for example,
        are not currently supported, and would therefore need to be simplified
        further to avoid TypError.
        """
        if not hasattr(self, "save_path"):
            # For new instances created while autosave is active
            path = self.get_new_save_path().with_suffix(".json")
            self.setattr_direct("save_path", Path(path))
        self.to_json(file_path=self.save_path, fullcopy=fullcopy)

    def _auto_delete(self, key=None):
        """Currently just calls CleverDict.save but could be overwritten with
        something more sophisticated.

        If .autosave() is called on an object, this method overwrites the
        default .delete() method and is called every time a value changes or is
        created.
        """
        CleverDict.save(self, key=key)


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
        If .expand == True (the 'normal' case), .delete_alias will remove all
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

    def info(self, as_str=False):
        """
        Prints or returns a string showing variable name equivalence
        and object attribute/dictionary key equivalence.
        """
        indent = "    "
        frame = inspect.currentframe().f_back.f_locals
        ids = sorted(k for k, v in frame.items() if v is self)
        result = [self.__class__.__name__ + ":"]
        if ids:
            if len(ids) > 1:
                result.append(indent + " is ".join(ids))
            id = ids[0]  # If more than one variable has the same name, use the first in the list
        else:
            id = "x"
        for k, v in self.items():
            parts = []
            for ak, av in self._aliases.items():
                if av == k:
                    parts.append(f"{id}[{repr(ak)}]")
            for ak, av in self._aliases.items():
                if av == k and isinstance(ak, str) and ak.isidentifier() and not keyword.iskeyword(ak):
                    parts.append(f"{id}.{ak}")
            parts.append(f"{repr(v)}")
            result.append(indent + " == ".join(parts))
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


def get_app_dir(app_name, roaming=True, force_posix=False):
    """
    this is a self contained copy of click.get_app_dir
    """
    import sys

    CYGWIN = sys.platform.startswith("cygwin")
    MSYS2 = sys.platform.startswith("win") and ("GCC" in sys.version)
    # Determine local App Engine environment, per Google's own suggestion
    APP_ENGINE = "APPENGINE_RUNTIME" in os.environ and "Development/" in os.environ.get("SERVER_SOFTWARE", "")
    WIN = sys.platform.startswith("win") and not APP_ENGINE and not MSYS2

    def _posixify(name):
        return "-".join(name.split()).lower()

    if WIN:
        key = "APPDATA" if roaming else "LOCALAPPDATA"
        folder = os.environ.get(key)
        if folder is None:
            folder = os.path.expanduser("~")
        return os.path.join(folder, app_name)
    if force_posix:
        return os.path.join(os.path.expanduser("~/.{}".format(_posixify(app_name))))
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~/Library/Application Support"), app_name)
    return os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), _posixify(app_name))

