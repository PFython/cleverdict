import os
import json
import inspect
import keyword
import itertools
from pathlib import Path
from pprint import pprint
from datetime import datetime
import types
import inspect

"""
Change log
==========

version 1.9.1
-------------
Handles edge cases handling errors where only=/ignore=/exclude= 0 and 1 (int)

version 1.9.0
-------------
Added exclude= as an alternative for ignore= (for Marshmallow fans)
Added only= (for Marshmallow fans)
Added exclude= ignore= and only= to __init__ for selective import
Made exclude= ignore= and only= permissive (lists OR single item strings)
Refactored using _preprocess_options()
y=CleverDict(x) now imports a fullcopy of x e.g. including _aliases/_vars

version 1.8.1
---------------------------
Added to_json() and from_json()
Added to_lines() and from_lines()
Added to_dict()
Added set_autosave (which works on individual objects, not the whole class)
Added set_autodelete (which works on individual objects, not the whole class)
Added autosave (which works on individual objects, not the whole class)
Added the ability to fully recreate a CleverDict with to_json(fullcopy=True)
Added cartoon!
Added logo!
Removed dependency on click
Revamped README
Removed identify_self()
Removed print output except for for autosave, but with 'silent' option
delattr removes attributes created using setattr_direct
Attributes created using setattr_direct update correctly.
Applied ignore=[] to: to_lines, to_list, to_json, info, to_dict, and repr
More consistent repr
._aliases and ._vars accessible as regular attributes
Substantially more and better tests


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

The __repr__ method now provides the vars as well, thus also showing attributes
set with setattr_direct.

The __repr__ method output is more readable

In order to support evalation from __repr__, the __init__ method has been changed.

The implemenation of several methods is more compact and more stable by reusing functionality.

More and improved tests.
"""


def save(self, name=None, value=None):
    """
    Called every time a CleverDict value is created or change.
    Overwrite with your own custome save() method e.g. to automatically
    write values to file/database/cloud, send a notification etc.

    self.set_autosave(your_save_function)

    Parameters
    ----------
    name: int | str
        Dictionary key name or object attribute name.
    value: any
        Dictionary value or object.attribute value

    Note
    ----
    This function should handle name is None properly.
    """
    pass


def delete(self, name=None):
    """
    Called every time a CleverDict key/attribute is deleted.  Overwrite with your
    own custome delete() method e.g. to automatically delete values from
    file/database/cloud, send a confirmation request/notification etc.

    self.set_autosave(your_save_function)

    Parameters
    ----------
    name: int | str
        Dictionary key name or object attribute name.

    Note
    ----
    This function should handle name is None properly.
    """
    pass


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

            norm_name = "".join(
                ch if ("A"[:i] + ch).isidentifier() else "_"
                for i, ch in enumerate(norm_name)
            )
            if name != norm_name:
                result.append(norm_name)
    return result


def get_app_dir(app_name, roaming=True, force_posix=False):
    """
    This is a self contained copy of click.get_app_dir
    """
    import sys

    CYGWIN = sys.platform.startswith("cygwin")
    MSYS2 = sys.platform.startswith("win") and ("GCC" in sys.version)
    # Determine local App Engine environment, per Google's own suggestion
    APP_ENGINE = "APPENGINE_RUNTIME" in os.environ and "Development/" in os.environ.get(
        "SERVER_SOFTWARE", ""
    )
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
        return os.path.join(
            os.path.expanduser("~/Library/Application Support"), app_name
        )
    return os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        _posixify(app_name),
    )


def _preprocess_options(ignore, exclude, only):
    """
    Performs preparatory transformations of ignore, exclude and only, inculding:

    - Convert to iterables if single item string supplied.
    - Check that only one argument is not None (to avoid logic bombs).
    - Fail gracefully if not.
    - Set ignore if exclude was used, and reset exclude (to avoid logic bombs)
    - Convert ignore to set() neither it nor exclude are specified

    Parameters
    ----------
    ignore: None | iterable
        Items to ignore during subsequent processing
    exclude: None | iterable
        Alias for ignore
    only: None | iterable
        Items to exclusively include during subsequent processing

    Returns
    -------
    tuple
        (ignore, only)
    """

    def make_set(arg):
        if arg is None:
            return set()
        return (
            set(arg) if hasattr(arg, "__iter__") and not isinstance(arg, str) else {arg}
        )

    if ignore == CleverDict.ignore:
        ignore = None
    if exclude == CleverDict.ignore:
        exclude = None

    if sum(x is not None for x in (ignore, exclude, only)) > 1:
        raise TypeError(
            f"Only one argument from ['only=', 'ignore=', 'exclude='] allowed."
        )

    if only is not None:  # leave only is None for proper only tests
        only = (
            set(only)
            if hasattr(only, "__iter__") and not isinstance(only, str)
            else {only}
        )

    return make_set(ignore) | make_set(exclude) | CleverDict.ignore, only


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
            key : name of an alias.
            value : value to which this key belongs. This key *must* be defined!

    _vars : dict
        a dictionary that contains items as follows:
            key: attribute which, when set, will *not* become an item of the Clever Dictionary.
            value : value of this attribute.
    """

    # Add .save & / .delete methods and create 'vanilla' copies to revert to
    original_save = save = save
    original_delete = delete = delete

    # Always ignore these objects (incl. methods and non JSON serialisables)
    ignore = {"_aliases", "save_path", "save", "delete"}

    # Used by .delete_alias:
    expand = True

    def __init__(
        self,
        mapping=(),
        _aliases=None,
        _vars={},
        save=None,
        delete=None,
        only=None,
        ignore=None,
        exclude=None,
        **kwargs,
    ):
        ignore, only = _preprocess_options(ignore, exclude, only)
        self.setattr_direct("_aliases", {})
        if isinstance(mapping, CleverDict):
            # for key, alias in mapping._aliases.items():
            #     if key != alias:
            #         self.add_alias(key, alias)
            for attribute, value in mapping._vars.items():
                self.setattr_direct(attribute, value)
            self._aliases = mapping._aliases
        else:
            data = None
        with Expand(CleverDict.expand if _aliases is None else False):
            if save is not None:
                self.set_autosave(save)
            if delete is not None:
                self.set_autodelete(delete)
            if ignore:
                if isinstance(mapping, dict):
                    mapping = {k: v for k, v in mapping.items() if k not in ignore}
                if isinstance(mapping, list):
                    mapping = {k: v for k, v in mapping if k not in ignore}
            if only is not None:
                if isinstance(mapping, dict):
                    mapping = {k: v for k, v in mapping.items() if k in only}
                if isinstance(mapping, list):
                    mapping = {k: v for k, v in mapping if k in only}
            self.update(mapping, **kwargs)
            if _aliases is not None:
                for k, v in _aliases.items():
                    self._add_alias(v, k)
            for k, v in _vars.items():
                self.setattr_direct(k, v)

    def __setattr__(self, name, value):
        if name in vars(self).keys():
            super().__setattr__(name, value)
        else:
            if name in self._aliases:
                name = self._aliases[name]
            elif name not in self:
                for al in all_aliases(name):
                    self._add_alias(name, al)
            super().__setitem__(name, value)
        self.save(name=name, value=value)

    __setitem__ = __setattr__

    def __getitem__(self, name):
        name = self.get_key(name)
        return super().__getitem__(name)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(e)

    def __delitem__(self, name):
        name = self.get_key(name)
        super().__delitem__(name)
        self.delete(name=name)
        for ak, av in list(self._aliases.items()):
            if av == name:
                del self._aliases[ak]

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError as e:
            if hasattr(self, name):
                super().__delattr__(name)
                self.delete(name=name)
            else:
                raise AttributeError(e)

    def __eq__(self, other):
        if isinstance(other, CleverDict):
            return self.items() == other.items() and vars(self) == vars(other)
        return NotImplemented

    def __repr__(self, ignore=None, exclude=None, only=None):
        """
        Parameters
        ----------

        ignore: iterable | str
            Any keys or aliases to exclude from output.

        exclude: iterable | str
            Alias for ignore

        only: iterable | str
            Only return output for specified keys
        """
        ignore, only = _preprocess_options(ignore, exclude, only)
        mapping = self._filtered_mapping(ignore, only)
        _aliases = {
            k: v for k, v in self._aliases.items() if k not in self and v in mapping
        }
        _vars = {k: v for k, v in vars(self).items() if k not in ignore}
        return f"{self.__class__.__name__}({repr(mapping)}, _aliases={repr(_aliases)}, _vars={repr(_vars)})"

    @property
    def _vars(self):
        """
        Returns a dict of any 'direct' attributes set with .setattr_direct()
        """
        return {k: v for k, v in vars(self).items() if k not in CleverDict.ignore}

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

    def _filtered_mapping(self, ignore=None, only=False):
        """
        Internal method
        The user should use to_dict !

        Returns a dictionary of items not excluded by 'ignore' list

        Parameters
        ----------
        ignore: iterable | str
            Any keys or aliases to exclude from output.

        exclude: iterable | str
            Alias for ignore

        only: iterable | str
            Only return output for specified keys

        Returns
        -------
        Values with keys and aliases from ignore filtered out : dict

        Note
        ----
        The CleverDict.ignore items are not filtered out.
        """
        mapping = {k: v for k, v in self.items() if k not in ignore}
        for k, v in self._aliases.items():
            if k in ignore and v in mapping:
                del mapping[v]
        if only is not None:
            return {k: v for k, v in mapping.items() if k in only}
        else:
            return mapping

    def update(self, mapping=(), **kwargs):
        """
        Parameters
        ----------
        The same as dict.update(), i.e.
            D.update([E, ]**F) -> None.  Update D from dict/iterable E and F.
            If E is present and has a .keys() method, then does:  for k in E: D[k] = E[k]
            If E is present and lacks a .keys() method, then does:  for k, v in E: D[k] = v
            In either case, this is followed by: for k in F:  D[k] = F[k]
        """
        if hasattr(mapping, "items"):
            mapping = getattr(mapping, "items")()

        for k, v in itertools.chain(mapping, getattr(kwargs, "items")()):
            self.__setitem__(k, v)

    def info(self, as_str=False, ignore=None, exclude=None, only=None):
        """
        Prints or returns a string showing variable name equivalence
        and object attribute/dictionary key equivalence.

        Parameters
        ----------
        as_str : bool
            if as_str is False, prints the information
            if as_str is True, returns the information as a string

        ignore: iterable | str
            Any keys or aliases to exclude from output.

        exclude: iterable | str
            Alias for ignore

        only: iterable | str
            Only return output for specified keys

        Returns
        -------
        information (if as_str is True): str
        None (if as_str is False)
        """
        ignore, only = _preprocess_options(ignore, exclude, only)
        mapping = self._filtered_mapping(ignore, only)
        indent = "    "
        frame = inspect.currentframe().f_back.f_locals
        ids = sorted(k for k, v in frame.items() if v is self)
        result = [self.__class__.__name__ + ":"]
        if ids:
            if len(ids) > 1:
                result.append(indent + " is ".join(ids))
            # If more than one variable has the same name, use the first:
            id = ids[0]
        else:
            id = "x"
        for k, v in mapping.items():
            parts = []
            for ak, av in self._aliases.items():
                if av == k:
                    parts.append(f"{id}[{repr(ak)}]")
            for ak, av in self._aliases.items():
                if (
                    av == k
                    and isinstance(ak, str)
                    and ak.isidentifier()
                    and not keyword.iskeyword(ak)
                ):
                    parts.append(f"{id}.{ak}")
            parts.append(f"{repr(v)}")
            result.append(indent + " == ".join(parts))
        for k, v in vars(self).items():
            if k not in ignore:
                result.append(f"{indent}{id}.{k} == {repr(v)}")
        output = "\n".join(result)
        if as_str:
            return output
        else:
            print(output)

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

    def _add_alias(self, name, alias):
        """
        Internal method for error handling while adding and alias, and finally
        adding to .alias.

        Used by add_alias, __init__ and __setattr__.
        """
        if alias in self._aliases and self._aliases[alias] != name:
            raise KeyError(
                f"{repr(alias)} already an alias for {repr(self._aliases[alias])}"
            )
        self._aliases[alias] = name

    def add_alias(self, name, alias):
        """
        Adds an alias to a given key/name.

        Parameters
        ----------
        name : any
            must be an existing key or an alias

        alias : scalar or iterable
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
        self.save(name=None, value=None)

    def delete_alias(self, alias):
        """
        deletes an alias

        Parameters
        ----------
        alias : scalar or list of scalars
            alias(es) to be deleted

        Notes
        -----
        If .expand == True (the 'normal' case), .delete_alias will remove all
        the specified alias AND all other aliases (apart from the original key).
        If .expand == False (most likely set via the Expand context manager),
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
                # Ignore the key, which is at the front of ._aliases:
                if alx in list(self._aliases.keys())[1:]:
                    del self._aliases[alx]
        self.save(name=None, value=None)

    def setattr_direct(self, name, value):
        """
        Sets an attribute directly, i.e. without making it into an item.
        This can be useful to store save data.

        Used internally to create the _aliases dict.

        Parameters
        ----------
        name : str
            name of attribute to be set. Should be a name that can be used as an identifier

        value : any
            value of the attribute
        """
        super().__setattr__(name, value)
        if name not in CleverDict.ignore:
            self.save(name, value)

    def to_list(self, ignore=None, exclude=None, only=None):
        """
        Creates a list of k,v pairs as a list of tuples.
        Main use case is Client/Server apps where returning a CleverDict object
        or a dictionary with numeric keys (which get converted to strings by
        json.dumps for example).

        Paramters
        ---------
        ignore: iterable | str
            Any keys or aliases to exclude from output.

        exclude: iterable | str
            Alias for ignore

        only: iterable | str
            Only return output for specified keys

        Returns
        -------
        A list of k,v pairs as a list of tuples e.g.
        [(1, "one"), (2, "two")]

        """
        ignore, only = _preprocess_options(ignore, exclude, only)
        mapping = self._filtered_mapping(ignore, only)
        return [(k, v) for k, v in mapping.items()]

    def to_dict(self, ignore=None, exclude=None, only=None):
        """
        Returns a regular dict of the core data dictionary

        Parameters
        ----------
        ignore: iterable | str
            Any keys or aliases to exclude from output.

        exclude: iterable | str
            Alias for ignore

        only: iterable | str
            Only return output for specified keys

        Returns
        -------
        dict
        """
        ignore, only = _preprocess_options(ignore, exclude, only)
        return self._filtered_mapping(ignore=ignore, only=only)

    @classmethod
    def fromkeys(cls, iterable, value, ignore=None, exclude=None, only=None):
        """
        Instantiates an object using supplied keys/aliases and values e.g.

        >>> x = CleverDict().fromkeys(["Abigail", "Tino", "Isaac"], "Year 9")

        Parameters
        ----------
        iterable: iterable
            used as the keys for the new CleverDict

        value: any
            used as the values for the new CleverDict

        ignore: iterable | str
            Any keys/aliases to ignore from output.  Ignoring an alias ignores
            all other aliases and the primary key; likewise ignoring the key.

        exclude: iterable | str
            Alias for ignore

        only: iterable | str
            Only return output for specified keys

        Returns
        -------
        New CleverDict with keys from iterable and values equal to value.
        """
        ignore, only = _preprocess_options(ignore, exclude, only)
        if ignore:
            iterable = {k: value for k in iterable if k not in ignore}
        if only is not None:
            iterable = {k: value for k in iterable if k in only}
        return CleverDict({k: value for k in iterable})

    def to_lines(
        self, file_path=None, start_from_key=None, ignore=None, exclude=None, only=None
    ):
        """
        Creates a line ("\n") delimited string or file using values for lines.

        Parameters
        ----------
        start_from_key: int | str
            The key (or alias) of the first line to export from.  Not to be
            confused with slicing e.g. x[0] will fail for x = CleverDict({1:1})
            String keys allow for keys/aliases to be references e.g. "Footnote"

        ignore: iterable | str
            Any keys/aliases to ignore from output.  Ignoring an alias ignores
            all other aliases and the primary key; likewise ignoring the key.

        exclude: iterable | str
            Alias for ignore

        only: iterable | str
            Only return output for specified keys

        file_path: str | pathlib.Path
            Path to the file (if any) to save to.

        Returns
        -------
        values joined by "\n" (if file_path is not specified) : str
        None (if file_path is specified)
        """
        ignore, only = _preprocess_options(ignore, exclude, only)
        mapping = self._filtered_mapping(ignore, only)
        if start_from_key is None:
            start_from_key = self.get_aliases()[0]
        else:
            try:
                start_from_key = self._aliases[start_from_key]
            except KeyError:
                raise
        lines = {}
        for k, v in mapping.items():
            if k == start_from_key or lines:
                lines.update({k: v})
        lines = "\n".join(lines.values())
        if not file_path:
            return lines
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(lines)

    @classmethod
    def from_lines(
        cls,
        lines=None,
        file_path=None,
        start_from_key=1,
        ignore=None,
        exclude=None,
        only=None,
    ):
        """
        Creates a new CleverDict object and loads data from a line ('\n')
        delimited string or file.

        Parameters
        ----------
        lines: str
            Text values separated by "\n"

        file_path: str | pathlib.Path
            Path to the file (if any) to load from.

        start_from_key: int
            The  (numeric) key to start the data dictionary with.  Default=1.
            Typically set to 0 for Pythonic line counting (starting at 0 not 1).

        ignore: iterable | str
            Any keys/aliases to ignore from output.  Ignoring an alias ignores
            all other aliases and the primary key; likewise ignoring the key.

        exclude: iterable | str
            Alias for ignore

        only: iterable | str
            Only return output for specified keys

        Returns
        -------
        New CleverDict: CleverDict

        Notes
        -----
        specifying both lines and file_path raises a ValueError
        """
        ignore, only = _preprocess_options(ignore, exclude, only)
        if not isinstance(start_from_key, int):
            raise TypeError(".from_lines(start_from_key=) must be an integer")
        if lines and file_path:
            raise ValueError("both lines and file_path specified")
        if not (lines or file_path):
            raise ValueError("neither lines nor file_path specified")
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.read()
        index = {k + start_from_key: v.strip() for k, v in enumerate(lines.split("\n"))}
        if only is not None:
            index = {k: v for k, v in index.items() if v in only}
        if ignore:
            index = {k: v for k, v in index.items() if v not in ignore}
        return cls(index)

    def to_json(
        self, file_path=None, fullcopy=False, ignore=None, exclude=None, only=None
    ):

        """
        Generates a JSON formatted string representing the CleverDict data and
        optionally saves to file.

        Parameters
        ----------
        file_path: str | pathlib.Path
            Path to the file (if any) to save to.

        fullcopy: bool
             Includes ._aliases and ._vars if True

        ignore: iterable | str
            Any keys/aliases to ignore from output.  Ignoring an alias ignores
            all other aliases and the primary key; likewise ignoring the key.

        exclude: iterable | str
            Alias for ignore

        only: iterable | str
            Only return output for specified keys

        Returns
        -------
        JSON formatted string if no file_path supplied : str
        None if file_path is supplied

        Notes
        -----
        Derived only from dictionary data if fullcopy==False
        Includes ._aliases and ._vars if fullcopy==True
        """
        ignore, only = _preprocess_options(ignore, exclude, only)
        mapping = self._filtered_mapping(ignore, only)

        if not fullcopy:
            json_str = json.dumps(mapping, indent=4)
        else:
            _aliases = {
                k: v for k, v in self._aliases.items() if k not in self and v in mapping
            }
            _mapping_encoded = {repr(k): v for k, v in mapping.items()}
            _aliases = {k: v for k, v in _aliases.items() if k != v}
            _vars = {k: v for k, v in vars(self).items() if k not in ignore}
            json_str = json.dumps(
                {
                    "_mapping_encoded": _mapping_encoded,
                    "_aliases": _aliases,
                    "_vars": _vars,
                },
                indent=4,
            )
        if file_path:
            with open(Path(file_path), "w", encoding="utf-8") as file:
                file.write(json_str)
        else:
            return json_str

    @classmethod
    def from_json(
        cls, json_data=None, file_path=None, ignore=None, exclude=None, only=None
    ):
        """
        Creates a new CleverDict object and loads data from a JSON object or
        file.

        Parameters
        ----------
        file_path: str | pathlib.Path
            Path to the file (if any) to save to.

        json_data: str
            JSON formatted string, typically created by json.dumps() : str

        ignore: iterable | str
            Any keys/aliases to ignore from output.  Ignoring an alias ignores
            all other aliases and the primary key; likewise ignoring the key.

        exclude: iterable | str
            Alias for ignore

        only: iterable | str
            Only return output for specified keys

        Returns
        -------
        New CleverDict: CleverDict
        """
        ignore, only = _preprocess_options(ignore, exclude, only)
        kwargs = {"ignore": ignore, "only": only}
        if json_data and file_path:
            raise ValueError("both json_data and file_path specified")
        if not (json_data or file_path):
            raise ValueError("neither json_data nor file_path specified")
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = json.loads(json_data)
        if set(data.keys()) == {"_mapping_encoded", "_aliases", "_vars"}:
            mapping = {eval(k): v for k, v in data["_mapping_encoded"].items()}
            _aliases = {k: v for k, v in data["_aliases"].items()}
            _vars = data["_vars"]
            return cls(mapping, _aliases=_aliases, _vars=_vars, **kwargs)
        else:
            return cls(data, **kwargs)

    @classmethod
    def get_new_save_path(cls):
        """
        Get Operating System specific default for settings folder;
        Return a (hopefully) unique filename comprising time and variable name

        e.g. 2020-12-06-03-30-57-892234.json
        """
        timestamp = "".join([x if x.isnumeric() else "-" for x in str(datetime.now())])
        id = f"{timestamp}.json"
        dir = Path(get_app_dir("CleverDict"))
        if not dir.is_dir():
            dir.mkdir(parents=True)
        return dir / id

    def create_save_file(self):
        """
        Creates a skeleton file to store autosave data if one doesn't already exist.

        Directory/folder is created if they don't already exist, based on
        .save_path
        An (almost) empty file is created, based on .save_path.name
        """
        if self.save_path.is_file():
            return
        try:
            os.makedirs(self.save_path.parent)
        except FileExistsError:
            pass
        with open(self.save_path, "w", encoding="utf-8") as file:
            file.write('{"empty": True}')

    def set_autosave(self, savefunc=None):
        """
        Overwrites the default (dummy) save method of an instance with a new custom function.

        Parameters
        ----------
        savefunc: function
            The new function which will be called whenever values change.
            If no function specified, resets to original (inactive) method.
            The function header should be (name, value)
        """
        if savefunc is None:
            savefunc = CleverDict.original_save
        params = tuple(list(inspect.signature(savefunc).parameters.keys())[1:])
        if params != ("name", "value"):
            raise TypeError(
                f"save function signature not (name, value), but ({', '.join(params)})"
            )
        super().__setattr__("save", types.MethodType(savefunc, CleverDict))

    def set_autodelete(self, deletefunc=None):
        """
        Overwrites the default (inactive) delete method of an instance with a new custom function.

        Parameters
        ----------
        deletefunc: function
            The new function which will be called whenever keys are deleted.
            If no function specified, resets to original (dummy) method.
            The function header should be (name)

        """
        if deletefunc is None:
            deletefunc = CleverDict.original_delete
        params = tuple(list(inspect.signature(deletefunc).parameters.keys())[1:])
        if params != ("name",):
            raise TypeError(
                f"delete function signature not (name), but ({', '.join(params)})"
            )
        super().__setattr__("delete", types.MethodType(deletefunc, CleverDict))

    def autosave(self, fullcopy=False, silent=False):
        """Toggles autosave to a config file.

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
                self.set_autosave()
                self.set_autodelete()
                if not silent:
                    print("\n ⚠  Autosave disabled.")
                    print(f"\nⓘ  Previous updates saved to:\n  {self.save_path}\n")
                del self.save_path
            except AttributeError as E:
                # Attempted to turn autosave off before it was ever enabled
                print(f"\n ⚠  Error with autosave(fullcopy=off): {E}")
                return
        else:
            path = self.get("save_path") or self.get_new_save_path()
            path = path.with_suffix(".json")
            self.setattr_direct("save_path", Path(path))
            if not path.is_file():
                self.create_save_file()
            if fullcopy:
                # Save and delete events trigger a call to the same method:
                super().__setattr__(
                    "save", types.MethodType(CleverDict._auto_save_fullcopy, self)
                )
                super().__setattr__(
                    "delete", types.MethodType(CleverDict._auto_save_fullcopy, self)
                )
            else:
                super().__setattr__(
                    "save", types.MethodType(CleverDict._auto_save_data, self)
                )
                super().__setattr__(
                    "delete", types.MethodType(CleverDict._auto_save_data, self)
                )
            self.save(name=None, value=None)
            if not silent:
                print(f"\n ⚠  Autosaving to:\n  {path}\n")

    def _auto_save_data(self, name=None, value=None):
        """
        Internal method

        Calls _auto_save_json to save a copy of the data dictionary (only) in
        JSON format, without any mappings, aliases, and directly set attributes.

        If .autosave() is called on an object, this method overwrites the
        default .save() method and is called every time a value changes or is
        created.

        """
        if not hasattr(self, "save_path"):
            path = self.get_new_save_path().with_suffix(".json")
            self.setattr_direct("save_path", Path(path))
        self.to_json(file_path=self.save_path)

    def _auto_save_fullcopy(self, name=None, value=None):
        """
        Internal method

        Calls _auto_save_json to save a full copy of the CleverDict instance in
        JSON format, in with all mappings, aliases, and directly set attributes.

        If .autosave(fullcopy=True) is called on an object, this method
        overwrites the default .save() method and is called every time a value
        changes or is created.
        """
        self._auto_save_json(name=name, value=value, fullcopy=True)

    def _auto_save_json(self, name=None, value=None, fullcopy=False):
        """
        Internal method

        If .autosave("json") is called on an object, this overwrites
        the default .save() method and is called every time a value changes or
        is created.

        NB JSON can only serialise certain datatypes.  Python sets, for example,
        are not currently supported, and would therefore need to be simplified
        further to avoid TypError.
        """
        if not hasattr(self, "save_path"):
            path = self.get_new_save_path().with_suffix(".json")
            self.setattr_direct("save_path", Path(path))
        self.to_json(file_path=self.save_path, fullcopy=fullcopy)
