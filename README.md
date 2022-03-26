# `CleverDict`
<p align="center">
    <a href="https://pypi.python.org/pypi/cleverdict"><img alt="PyPI" src="https://img.shields.io/pypi/v/cleverdict.svg"></a>
	<a href="https://pypi.python.org/pypi/cleverdict"><img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/cleverdict.svg"></a>
    <a href="https://pepy.tech/project/cleverdict"><img alt="Downloads" src="https://pepy.tech/badge/cleverdict"></a>
    <a href="#Contribution" title="Contributions are welcome"><img src="https://img.shields.io/badge/contributions-welcome-green.svg"></a>
    <a href="https://github.com/pfython/cleverdict/releases" title="CleverDict"><img src="https://img.shields.io/github/release-date/pfython/cleverdict?color=green&label=updated"></a>
    <img alt="PyPI - License" src="https://img.shields.io/pypi/l/cleverdict">
    <img alt="PyPI - Status" src="https://img.shields.io/pypi/status/cleverdict">
    <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/pfython/cleverdict">
    <a href="https://twitter.com/@appawsom" title="Follow us on Twitter"><img src="https://img.shields.io/twitter/follow/appawsom.svg?style=social&label=Follow"></a>
</p>

![cleverdict cartoon](https://raw.githubusercontent.com/PFython/cleverdict/master/resources/cleverdict%20cartoon.png)

## >CONTENTS

1. [OVERVIEW](#1-overview)
2. [INSTALLATION](#2-installation)
3. [IMPORTING INTO CLEVERDICT](#3-importing-to-cleverdict)
4. [EXPORTING FROM CLEVERDICT](#4-exporting-from-cleverdict)
5. [ATTRIBUTE NAMES AND ALIASES](#5-attribute-names-and-aliases)
6. [DEEPER DIVE INTO ATTRIBUTE NAMES](#6-deeper-dive-into-attribute-names)
7. [SETTING AN ATTRIBUTE WITHOUT CREATING A DICTIONARY ITEM](#7-setting-an-attribute-without-creating-a-dictionary-item)
8. [THE AUTO-SAVE FEATURE](#8-the-auto-save-feature)
9. [CREATING YOUR OWN AUTO-SAVE FUNCTION](#9-creating-your-own-auto-save-function)
10. [CONTRIBUTING](#10-contributing)
11. [CREDITS](#11-credits)


## 1. OVERVIEW

`CleverDict` is a hybrid Python data class which allows both `object.attribute` and `dictionary['key']` notation to be used simultaneously and interchangeably.  It's particularly handy when your code is mainly object-orientated but you want a 'DRY' and extensible way to import data in json/dictionary/list format into your objects... or vice versa... without having to write extra code just to handle the translation.

Python dictionaries are simple yet powerful, but many people find `object.attribute` syntax easier to type and more intuitive to read, so why not have the best of both worlds?

    >>> from cleverdict import CleverDict
    >>> x = CleverDict({'total':6, 'usergroup': "Knights of Ni"})

    >>> x.total
    6
    >>> x['total']
    6

    >>> x.usergroup
    'Knights of Ni'
    >>> x['usergroup']
    'Knights of Ni'

    >>> x['life'] = 42
    >>> x.life += 1
    >>> x['life']
    43

    >>> del x['life']
    >>> x.life
    AttributeError: 'life'

`CleverDict` automatically generates **Aliases** which map to your original dictionary keys, handling various edge cases we've unearthed along the way so you don't have to.  You can add and delete your own custom **Aliases** too, which is really handy for adding shortcuts, mapping API responses to existing data structures, local language variants, and more.

`CleverDict` plays nicely with JSON and also includes some great convenience functions for importing/export lists, dicts, and lines.  It even offers two built-in `.autosave()` options and you can specify your own autosave/autodelete functions to be called automatically whenever an attribute changes.  No more explicitly writing lines to save your data or prompt for confirmation etc. every... single... time... a value changes (or *worse*, forgetting to...).

## 2. INSTALLATION

Very lightweight - no dependencies:

    pip install cleverdict

or to cover all bases...

    python -m pip install cleverdict --upgrade


## 3. IMPORTING TO CLEVERDICT

You can create a `CleverDict` instance using keyword arguments:

    >>> x = CleverDict(created = "today", review = "tomorrow")

    >>> x.created
    'today'
    >>> x['review']
    'tomorrow'

Or use a list of tuple pairs and/or list pairs:

    >>> x = CleverDict([("value1", "one"), ["value2", "two"], ("value3", "three")])

    >>> x.value1
    'one'
    >>> x['value2']
    'two'
    >>> getattr(x, "value3")
    'three'

Or use an existing `CleverDict` object as input:

    >>> x = CleverDict({1: "one", 2: "two"})
    >>> y = CleverDict(x)

    >>> y
    CleverDict({1: 'one', 2: 'two'}, _aliases={'_1': 1, '_True': 1, '_2': 2}, _vars={})

    >>> y.items()
    dict_items([(1, 'one'), (2, 'two')])

> *(\*) See Sections 5 and 7 to understand `_aliases={}` and `_vars={}` shown in the output above...*

A really nice feature is the ability to import JSON strings or files using `.from_json()` (try with `resources/mydata.json`):

    >>> json_data = '{"None": null}'
    >>> x = CleverDict.from_json(json_data)
    >>> x
    CleverDict({'None': None}, _aliases={'_None': 'None'}, _vars={})

    >>> y = CleverDict.from_json(file_path="mydata.json")

And the built-in dictionary method `.fromkeys()` works as normal, like this:

    >>> x = CleverDict.fromkeys(["Abigail", "Tino", "Isaac"], "Year 9")

    >>> x
    CleverDict({'Abigail': 'Year 9', 'Tino': 'Year 9', 'Isaac': 'Year 9'}, _aliases={}, _vars={})

You can also use `vars()` to import another object's data (but not its methods):

    >>> class X: pass
    >>> a = X(); a.name = "Percival"
    >>> x = CleverDict(vars(a))

    >>> x
    CleverDict({'name': 'Percival'}, _aliases={}, _vars={})

## 4. EXPORTING FROM CLEVERDICT

To return a regular Python `dict` from `CleverDict`'s main data dictionary:

    >>> x.to_dict()
    {'name': 'Percival'}

You can export to JSON with `.to_json()` but be aware that your nested values/objects will not be touched, and must therefore be capable of being serialised to JSON individually.  If they're not essential to your output, you can simply add the  `ignore=` (or `exclude=`) argument to exclude them entirely:

    >>> x.to_json()
    '{\n    "name": "Percival"\n}'

    >>> x.now = datetime.datetime.now()
    >>> x.to_json()
    TypeError: Object of type datetime is not JSON serializable

    >>> x.to_json(ignore=["now"])
    '{\n    "name": "Percival"\n}'

    # Or output to a file:
    >>> x.to_json(file_path="mydata.json")

You can also use the `.to_list()` method to generate a list of key/value pairs:

    >>> x = CleverDict({1: "one", 2: "two"})

    >>> x.to_list()
    [(1, 'one'), (2, 'two')]

And you can import/export text files using `.from_lines()` and `.to_lines()` which is useful for things like subtitles, README files, code, and to-do lists:

    >>> lines ="This is my first line\nMy second...\n\n\n\n\nMy LAST\n"
    >>> x = CleverDict.from_lines(lines)

    >>> from pprint import pprint
    >>> pprint(x)
    {1: 'This is my first line',
     2: 'My second...',
     3: '',
     4: '',
     5: '',
     6: '',
     7: 'My LAST',
     8: ''}

     >>> x.to_lines(file_path="lines.txt")

By default `.from_lines()` uses 'human' numbering starting with key 1 (integer) but you can specify another starting number with `start_from_key=`:

    >>> x = CleverDict.from_lines(lines, start_from_key=0)
    >>> pprint(x)

    {0: 'This is my first line',
     1: 'My second...',
     2: '',
     3: '',
     4: '',
     5: '',
     6: 'My LAST',
     7: ''}

If you want to start your output from a specific line you can again use `start_from_key=`, this time with `.to_lines()`:

    >>> x.to_lines(start_from_key=6)
    'My LAST\n'

> That '`\n`' at the end of the output is actually Line 7 which is empty.


Although primarily intended for numerical indexing, you can also use *strings* with `.to_lines()`, which is handy for setting 'bookmarks' for example.  You can choose between creating an **alias** (recommended - see next Section) or actually creating/overwriting with a new **key**:

    >>> x.add_alias(6, "The End")
    >>> new_lines = x.to_lines(start_from_key="The End")
    >>> new_lines
    'My LAST\n'

    >>> x.footnote1 = "Source: Wikipedia"
    >>> x.update({8:"All references to living persons are accidental"})
    >>> x.to_lines(start_from_key="footnote1")
    'Source: Wikipedia\nAll references to living persons are accidental'

> NB:  Like regular dictionaries from Python 3.6 onwards, `CleverDict`,  stores values **in the order you create them**.  By default though `pprint` will helpfully (!) **sort** the keys, so don't panic if they seem out of order... Just use `repr()` to confirm the actual order, or `.info()` which is explained more fully in Section 6.

![Keep Calm](https://raw.githubusercontent.com/PFython/cleverdict/master/resources/keep_calm_use_info.png)

If you want to *only* include particular keys in the output of `.to_json()`, `.to_list()`, `.to_dict`, `.to_lines()`, `.info()` and even `__repr__()`, you can use the `only=` argument followed by a list of attribute/key names:

    >>> x = CleverDict({"Apple": "Green", "Banana": "Yellow", "Orange": "Blue"})
    >>> x.to_dict(only=["Apple", "Orange"])
    {'Apple': 'Green', 'Orange': 'Blue'}

And finally, if you want to **exclude** (perhaps sensitive) attributes such as `.password`, just add the argument `ignore=` (or `exclude=`)  to ignore:

    >>> x.password = "Top Secret - don't ever save to file!"

    >>> x.to_lines(start_from_key=6)
    "My LAST\n\nTop Secret - don't ever save to file!"

    >>> x.to_lines(start_from_key=6, ignore=["password"])
    'My LAST\n'

You can add common exceptions at a *class* level too:

    >>> CleverDict.ignore
    {"_aliases", "save_path", "save", "delete"}

     >>> CleverDict.ignore.add("password")

## 5. ATTRIBUTE NAMES AND ALIASES

Python dictionaries accept keywords, null strings, strings incorporating punctuation marks, and integers as their keys, but these *aren't* valid names for object attributes.  `CleverDict` helps by generating valid names where a straight copy of the dictionary keys would otherwise fail.    So for example `CleverDict` will automatically create the attribute name`"_7"` (string) to map to a dictionary key of `7` (integer):

    >>> x = CleverDict({7: "Seven"})

    >>> x._7
    'Seven'
    >>> x
    CleverDict({7: 'Seven'}, _aliases={'_7': 7}, _vars={})

```CleverDict``` keeps the original dictionary keys and values unchanged and remembers any normalised attribute names as aliases in ```._aliases```.  You can add or delete further aliases with ```.add_alias``` and ```.delete_alias```, but the original dictionary key will never be deleted, even if all aliases and attributes are removed:

    >>> x.add_alias(7, "NumberSeven")
    >>> x.add_alias(7, "zeven")

    >>> x
    CleverDict({7: 'Seven'}, _aliases={'_7': 7, 'NumberSeven': 7, 'zeven': 7}, _vars={})

    >>> x.get_aliases()
    [7, '_7', 'NumberSeven', 'zeven']

`CleverDict` objects continue to work as dictionaries even if you accidentally use any of the built-in method names for dictionary keys or aliases.  As you'd expect and hope, it won't overwrite those methods, and the dictionary will remain intact:

    >>> 'to_list' in dir(CleverDict)
    True

    >>> y = CleverDict({'to_list': "Some information"})

    >>> y['to_list']
    'Some information'

    >>> type(y.to_list)
    <class 'method'>

Back to our **alias** example, if you specify `ignore=` (or `exclude=`) when using `.to_json()`, `.to_list()`, `.info()`, `to_lines()`, `.to_dict`, or `__repr__()`, you can rest easy knowing that all aliases *and* the primary key(s) you've specified will be excluded too:

    >>> x.info(ignore=[7])
    CleverDict:

    >>> x.to_dict(ignore=["zeven"])
    {}

    >>> x.to_list(ignore=["NumberSeven"])
    []

As you probably guessed, you can safely delete an alias with `.delete_alias()`, and the original dictionary key will be retained until/unless you use `del`:

    >>> x.delete_alias(["_7","NumberSeven"])

    >>> x
    "CleverDict({7: 'Seven'}, _aliases={'zeven': 7}, _vars={})"

    >>> x._7
    AttributeError: '_7'

    >>> x.delete_alias([7])
    KeyError: "primary key 7 can't be deleted"

    >>> del x[7]
    >>> x
    CleverDict({}, _aliases={}, _vars={})


## 6. DEEPER DIVE INTO ATTRIBUTE NAMES


**QUIZ QUESTION:** Did you know that since [PEP3131](https://www.python.org/dev/peps/pep-3131/) many (but not all) unicode characters are valid in attribute names?

    >>> x = CleverDict(значение = "znacheniyeh: Russian word for 'value'")
    >>> x.значение
    "znacheniyeh: Russian word for 'value'"

`CleverDict` replaces all *invalid* characters such as (most) punctuation marks with "`_`" on a *first come, first served* basis.  To avoid duplicates or over-writing, a `KeyError` is raised in the event of a 'clash', which is your **strong hint** to rename one of the offending dictionary keys to something that won't result in a duplicate alias.  For example:

    >>> x = CleverDict({"one-two": "hypen",
                        "one/two": "forward slash"})
    KeyError: "'one_two' already an alias for 'one-two'"

    >>> x = CleverDict({"one-two": "hypen",
                        "one_or_two": "forward slash"})

**BONUS QUESTION:** Did you also know that the dictionary keys `0`, `0.0`, and `False` are considered the same in Python?  Likewise `1`, `1.0`, and `True`, and `1234` and `1234.0`?  If you create a regular dictionary using more than one of these different identities, they'll appear to 'overwrite' each other, keeping the **first Key** specified but the **last Value** specified, reading left to right:

    >>> x = {1: "one", True: "the truth"}

    >>> x
    {1: 'the truth'}

You'll be relieved to know `CleverDict` handles these cases but we thought it was worth mentioning in case you came across them first and wondered what the heck was going on!  *"Explicit is better than implicit"*, right?  If in doubt, you can inspect all the keys, `.attributes`, and aliases using the `.info()` method, as well as any aliases linking to the object itself:

    >>> x = y = z = CleverDict({1: "one", True: "the truth"})
    >>> x.info()

    CleverDict:
    x is y is z
    x[1] == x['_1'] == x['_True'] == x._1 == x._True == 'the truth'


And if you use `info(as_str=True)` you'll get the results as a printable string:

    >>> x.info(as_str=True)

    "CleverDict:\n    x is y is z\n    x[1] == x['_1'] == x['_True'] == x._1 == x._True == 'the truth'"


## 7. SETTING AN ATTRIBUTE WITHOUT CREATING A DICTIONARY ITEM
We've included the `.setattr_direct()` method in case you want to set an attribute *without* creating the corresponding dictionary key/value.  This could be useful for storing 'internal' data, objects and methods for example, and is used by `CleverDict` itself to store aliases in `._aliases` and the location of the autosave file in `save_path`.  Any variables which are set directly with `.setattr_direct()` are stored in `_vars`:

    >>> x = CleverDict()
    >>> x.setattr_direct("direct", True)

    >>> x
    CleverDict({}, _aliases={}, _vars={'direct': True})

Neither `._vars`, nor `_aliases`, nor any of `CleverDict`'s own functions/methods/variables are included in the output of `.to_json()`, `.to_lines()`, and `.to_list()` etc. ***unless*** you specify `(fullcopy=True)`.  Otherwise the output will simply be your basic data dictionary, since `CleverDict` is a *dictionary* first and foremost.

Subject to normal JSON limitations, you can *completely reconstruct* your original `CleverDict` using one created with `.from_json(fullcopy=True)`:

    >>> x = CleverDict({"total":6, "usergroup": "Knights of Ni"})
    >>> x.add_alias("usergroup", "knights")
    >>> x.setattr_direct("Quest", "The Holy Grail")
    >>> x.to_json(file_path="mydata.json", fullcopy=True)

    >>> y = CleverDict.from_json(file_path="mydata.json")
    >>> y == x
    True

    >>> y
    CleverDict({'total': 6, 'usergroup': 'Knights of Ni'}, _aliases={'knights': 'usergroup'}, _vars={'Quest': 'The Holy Grail'})

This even solves the pesky problem of `json.dumps()` converting numeric keys to strings e.g. `{1: "one"}` to `{"1": "one"}`.  By recording the mappings as part of the JSON, `CleverDict` is able to remember whether your initial key was numeric or a string.  Niiiiice.


## 8. THE AUTO-SAVE FEATURE


Following the "*batteries included*" philosophy, we've included not one but **two** powerful autosave/autodelete options which, when activated, will save your `CleverDict` data to the recommended 'Settings' folder of whichever Operating System you're using.

---

**AUTOSAVE OPTION #1: DICTIONARY DATA ONLY**


    >>> x = CleverDict({"Patient Name": "Wobbly Joe", "Test Result": "Positive"})
    >>> x.autosave()

    ⚠ Autosaving to:
    C:\Users\Peter\AppData\Roaming\CleverDict\2021-01-20-15-03-54-30.json

    >>> x.Prognosis = "Not good"

If you browse the json file, you should see `.Prognosis` has been saved along with any other new/changed values.  Any values you delete will be automatically removed.

---
**AUTOSAVE OPTION #2: FULL COPY**

In **Section 7** you saw how to use `.to_json(fullcopy=True)` to create a complete image of your `CleverDict` as a JSON string or file.  You can set this as the autosave/autodelete method using the same simple syntax:

    >>> x.autosave(fullcopy=True)

With this autosave option, **all dictionary data**, **all aliases** (in `_aliases`), and **all attributes** (including `_vars`) will be saved whenever they're created, changed, or deleted.

---


In both `.autosave()` options above, the file location is stored as `.save_path` using `.setattr_direct()` which you read about above (unless you skipped or fell asleep!).

    >>> x.save_path
    WindowsPath('C:/Users/Peter/AppData/Roaming/CleverDict/2021-01-20-15-03-54-30.json')

To disable autosaving/autodeletion  just enter:

    >>> x.autosave("off")

    ⚠ Autosave disabled.

    ⓘ Previous updates saved to:
       C:\Users\Peter\AppData\Roaming\CleverDict\2021-01-20-15-03-54-30.json

To deactivate `.save()` or `.delete()` separately:

    >>> x.set_autosave()
    >>> x.set_autodelete()

> If you want to periodically open the `CleverDict` save folder to check for orphaned `.json` files from time to time, a handy shortcut is:

    >>> import webbrowser
    >>> webbrowser.open(x.save_path.parent)

## 9. CREATING YOUR OWN AUTO-SAVE/AUTO-DELETE FUNCTION

As well as autosave/autodelete options baked in to `CleverDict`, you can set pretty much any custom function to run **automatically** when a `CleverDict` value is *created, changed, or deleted*, for example to update a database, save to a file, or synchronise with cloud storage etc.  Less code for you, and less chance you'll forget to explicitly call that crucial update function...

This can be enabled at a *class* level, or by creating subclasses of `CleverDict` with different options, or an *object/instance* level.  We strongly recommend the *object/instance* approach wherever possible, but you have the choice.

### **Autosaving a particular object/instance:**

You can either overwrite the `.save()` / `.delete()` methods when you create your object, or use `.set_autosave()` / `.set_autodelete()` after the event:

    >>> x = CleverDict({"Patient Name": "Wobbly Joe", "Test Result": "Positive"},
        save=your_save_function)

    # Or for an existing object:
    >>> x.set_autosave(your_save_function)


    >>> x = CleverDict({"Patient Name": "Wobbly Joe", "Test Result": "Positive"},
        delete=your_delete_function)

    # Or for an existing object:
    >>> x.set_autodelete(your_delete_function)

### **Autosaving at a class level:**

Simple to do, but beware this could change all existing `CleverDict` instances as well as all future ones:

    >>> CleverDict.save = your_save_function
    >>> CleverDict.delete = your_delete_function

### **Creating Subclasses:**

If you create a subclass of `CleverDict` remember to call `super().__init__()` *before* trying to set any further class or object attributes, otherwise you'll run into trouble:

    class AutoStore(CleverDict):
        def __init__(self, *args, **kwargs):
            self.setattr_direct('index', [])
            super().__init__(*args, **kwargs)

        def save(self, name, value):
            """ Keep a separate 'store' for data in .index """
            self.index.append((name, value))

    class AutoConfirm(CleverDict): pass
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def save(self, name, value):
            """ Print confirmation of the latest change """
            print(f"{name.title()}: {value.upper()}")

> NB: The `.append()` method  in `AutoStore.save()` above doesn't trigger the `.save()` method again itself (thankfully) otherwise we'd in a whole world of recursion pain...  If we'd used `self.index +=`, the `.save()` method *would* have been called recursively.

### **Writing Your Own Function:**

When writing your own `.save()` function, you'll need to accept three arguments as shown in the following example:

    >>> def your_save_function(self, name, value):
            """ Custom save function by you """
            print(f" ⓘ  .{name} (object type: {self.__class__.__name__}) = {value} {type(value)}")

    >>> CleverDict.delete = your_delete_function
    >>> x=CleverDict()
    >>> x.new = "Novelty"
    ⓘ  .new (object type: CleverDict) = Novelty <class 'str'>

    >>> x.save.__doc__
    ' Custom save function by you '

* **self**: because we're dealing with objects and classes...
* **key**: a valid Python `.attribute` or *key* name preferably, otherwise you'll only be able to access it using `dictionary['key']` notation later on.
* **value**: anything

When writing your own `.delete()` function, the same applies, except there is no `value` parameter supplied.

## 10. CONTRIBUTING

We'd love to see Pull Requests (and relevant tests) from other contributors, particularly if you can help:

* Evolve `CleverDict` to make it play nicely with other classes and formats.  [For example: `datetime`](https://github.com/PFython/cleverdict/issues/5).
* Put the finishing touches on the **docstrings** to enable autocompletion in modern IDEs (this is neither the author's strong suit nor his passion!).
* Improve the structure and coverage of `test_cleverdict.py`.

For a list of all outstanding **Feature Requests** and (heaven forbid!) actual *Issues* please have a look here and maybe you can help out?

https://github.com/PFython/cleverdict/issues?q=is%3Aopen+is%3Aissue


## 11. CREDITS
`CleverDict` was developed jointly by Ruud van der Ham, Peter Fison, Loic Domaigne, and Rik Huygen who met on the friendly and excellent Pythonista Cafe forum (www.pythonistacafe.com).  Peter got the ball rolling after noticing a super-convenient, but not fully-fledged feature in Pandas that allows you to (mostly) use `object.attribute` syntax or `dictionary['key']` syntax interchangeably. Ruud, Loic and Rik then started swapping ideas for a hybrid  dictionary/data class, originally based on `UserDict` and the magic of `__getattr__` and `__setattr__`.

> **Fun Fact:** `CleverDict` was originally called `attr_dict` but several confusing flavours of this and `AttrDict` exist on PyPi and Github already.  Hopefully this new tongue-in-cheek name is more memorable and raises a smile ;)

If you find `cleverdict` helpful, please feel free to:

<a href="https://www.buymeacoffee.com/pfython" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/arial-yellow.png" alt="Buy Me A Coffee" width="217px" ></a>
