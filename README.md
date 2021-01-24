# CleverDict

![cleverdict logo](https://raw.githubusercontent.com/PFython/cleverdict/issues-and-enhancements/cleverdict.png)

## 1. OVERVIEW

`CleverDict` is a hybrid Python data class which allows both `object.attribute` and `dictionary['key']` notation to be used simultaneously and interchangeably.  It's particularly handy when your code is mainly object-orientated but you want a 'DRY' and extensible way to import data in json/dictionary format into your objects... or vice versa... without having to write extra code just to handle the translation.

`CleverDict` also calls a `.save()` method whenever an attribute or dictionary value is created or changed.  Initially the `.save()` method does nothing, but you either turn on the *"batteries included"* `.autosave()` feature (which automatically saves your data to a JSON file) or you can overwrite it with your own function to do other useful things automatically every time an attribute changes in future e.g.

* pickle
* encode
* encrypt
* serialise
* save data to a config file or database
* upload to the cloud
* etc.

No more slavishly writing your own "save" or "update" function and trying to remember to call it manually every... single... time... values change (or *might* change).

The other main feature of `CleverDict` is that it supports **Aliases** which link to the original dictionary keys.  This is really handy for data mapping e.g. taking an API response and making it play nicely with your own data structures.

If you just want to understand the core features of `CleverDict`, please read up to and including **Section 4**.  There are quite a few advanced features and "edge case" which are dealt with more thoroughly after that, but don't be daunted!  We've done the deep thinking so you don't have to... hopefully ;)


## 2. INSTALLATION
Very lightweight - no dependencies:

    pip install cleverdict



or to cover all bases...

    python -m pip install cleverdict --upgrade


## 3. BASIC USE

`CleverDict` objects behave like normal Python dictionaries, but with the convenience of immediately offering read and write access to their data (keys and values) using the `object.attribute` syntax, which many people find easier to type and more intuitive to read and understand.

You can create a `CleverDict` object in exactly the same way as a regular Python dictionary:

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

The values are then immediately available using either dictionary or `.attribute` syntax:

    >>> x['life'] = 42
    >>> x.life += 1
    >>> x['life']
    43

    >>> del x['life']
    >>> x.life
    # KeyError: 'life'

`CleverDict` objects can always be relied on to behave like dictionaries, but if you accidentally use any of its built-in method names as dictionary keys then (as you'd expect and hope) it won't overwrite those methods, but nor will its value be accessible using `.attribute` notation:

    >>> 'to_list' in dir(CleverDict)
    True

    >>> x = CleverDict({'to_list': "Some information"})

    >>> x['to_list']
    'Some information'

    >>> type(x.to_list)
    <class 'method'>

If you use JSON, you can export your dictionary data easily with `.to_json()` but all your values must be capable of being serialised to JSON obviously, so no Python sets or custom objects unless you convert them to something that JSON *can* handle first:

    >>> x.to_json()
    '{"total": 6, "usergroup": "Knights of Ni"}'

    # Or output to a file:
    >>> x.to_json(file_path="mydata.json")


You can also use the `.to_list()` method to generate a list of key/value pairs:

    >>> x = CleverDict({1: "one", 2: "two"})

    >>> x.to_list()
    [(1, 'one'), (2, 'two')]


## 4. OTHER EASY WAYS TO IMPORT/EXPORT DATA
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

You can also use the built-in dictionary method `.fromkeys()`  like this:

    >>> x = CleverDict.fromkeys(["Abigail", "Tino", "Isaac"], "Year 9")

    >>> x
    CleverDict({'Abigail': 'Year 9', 'Tino': 'Year 9', 'Isaac': 'Year 9'}, _aliases={}, _vars={})

> *(\*) See Sections 5 and 7 to understand `_aliases={}` and `_vars={}` in the output above...*

You can use an existing `CleverDict` object as input:

    >>> x = CleverDict({1: "one", 2: "two"})
    >>> y = CleverDict(x)

    >>> y
    CleverDict({'total': 6, 'usergroup': 'Knights of Ni'}, _aliases={}, _vars={})

    >>> y.items()
    dict_items([(1, 'one'), (2, 'two')])

Or use `vars()` to import another object's data (but not its methods):

    >>> class X: pass
    >>> a = X(); a.name = "Percival"
    >>> x = CleverDict(vars(a))

    >>> x
    CleverDict({'name': 'Percival'}, _aliases={}, _vars={})

A really nice feature is the ability to import/export JSON strings or files using `.from_json()` and `.to_json()`:

    >>> json_data = '{"None": null}'
    >>> x = CleverDict.from_json(json_data)
    >>> x
    CleverDict({'None': None}, _aliases={'_None': 'None'}, _vars={})

    >>> x.to_json(file_path="mydata.json")

    >>> y = CleverDict.from_json(file_path="mydata.json")
    >>> x == y
    True

And you can import/export line ("`\n`") delimited strings or files using `.from_lines()` and `.to_lines()`:

    >>> lines ="This is my first line\nMy second...\n\n\n\n\nMy LAST\n"
    >>> x=CleverDict.from_lines(lines, start_at=1)

    >>> x.to_list()
    [(1, 'This is my first line'), (2, 'My second...'), (3, ''), (4, ''), (5, ''), (6, ''), (7, 'My LAST'), (8, '')]

    >>> x.to_lines(start_at=7)
    'My LAST'

    >>> x.to_lines(file_path="lines.txt", start_at=1)

## 5. ATTRIBUTE NAMES AND ALIASES

By default `CleverDict` tries to find valid attribute names for dictionary keys which would otherwise fail.  This includes keywords, null strings, most punctuation marks, and keys starting with a numeral.  So for example `7` (integer) becomes `"_7"` (string):

    >>> x = CleverDict({7: "Seven"})

    >>> x._7
    'Seven'
    >>> x
    CleverDict({7: 'Seven'}, _aliases={'_7': 7}, _vars={})

`CleverDict` keeps the original dictionary keys and values unchanged and remembers any normalised attribute names as aliases in `._aliases`.  You can add or delete further aliases with `.add_alias()` and `.delete_alias()`, but the original dictionary key will never be deleted, even if all aliases and attributes are removed:

    >>> x.add_alias(7, "NumberSeven")

    >>> x
    CleverDict({7: 'Seven'}, _aliases={'_7': 7, 'NumberSeven': 7}, _vars={})
    >>> x.get_aliases()
    [7, 'NumberSeven']

    >>> x.delete_alias(["_7","NumberSeven"])

    >>> x
    CleverDict({7: 'Seven'}, _aliases={}, _vars={})
    >>> x._7
    AttributeError: '_7'


## 6. DEEPER DIVE INTO ATTRIBUTE NAMES


**QUIZ QUESTION:** Did you know that since [PEP3131](https://www.python.org/dev/peps/pep-3131/) many unicode letters are valid in attribute names?

    >>> x = CleverDict(значение = "znacheniyeh: Russian word for 'value'")
    >>> x.значение
    "znacheniyeh: Russian word for 'value'"

`CleverDict` handles this and replaces all remaining *invalid* characters such as punctuation marks with "`_`" on a *first come, first served* basis.  To avoid duplicates or over-writing, a `KeyError` is raised if required, which is your **strong hint** to rename the offending dictionary keys!  For example:

    >>> x = CleverDict({"one-two": "hypen",
                        "one/two": "forward slash"})
    KeyError: "'one_two' already an alias for 'one-two'"

    >>> x = CleverDict({"one-two": "hypen",
                        "one_or_two": "forward slash"})

**BONUS QUESTION:** Did you also know that the dictionary keys `0`, `0.0`, and `False` are considered the same in Python?  Likewise `1`, `1.0`, and `True`, and `1234` and `1234.0`?  If you create a regular dictionary using more than one of these different identities, they'll appear to 'overwrite' each other, keeping the **first Key** specified but the **last Value** specified, reading left to right:

    >>> x = {1: "one", True: "the truth"}

    >>> x
    {1: 'the truth'}

You'll be relieved to know `CleverDict` handles these cases but we thought it was worth mentioning in case you came across them first and wondered what the heck was going on!  *"Explicit is better than implicit"*, right?  You can inspect all the key names and `.attribute` aliases using the `.info()` method, as well as any aliases for the object itself:

    >>> x = y = z = CleverDict({1: "one", True: "the truth"})
    >>> x.info()

    CleverDict:
    x is y is z
    x[1] == x['_1'] == x['_True'] == x._1 == x._True == 'the truth'


And if you use `info('as_str=True')` you'll get the results as a printable string:

    >>> x.info(as_str=True)

    "CleverDict:\n    x is y is z\n    x[1] == x['_1'] == x['_True'] == x._1 == x._True == 'the truth'"


## 7. SETTING AN ATTRIBUTE WITHOUT CREATING A DICTIONARY ITEM
We've included the `.setattr_direct()` method in case you want to set an object attribute *without* creating the corresponding dictionary key/value.  This could be useful for storing save data for example, and is used internally by `CleverDict` to store aliases in `._aliases` and the location of the autosave file in `save_path`.  Any variables which are set directly with `.setattr_direct()` are stored in `_vars` and these, along with `CleverDict` functions/methods are NOT exported when using methods like `.to_json()`, `.to_lines()`, and `.to_list()`.

    >>> x = CleverDict()
    >>> x.setattr_direct("direct", True)

    >>> x
    CleverDict({}, _aliases={}, _vars={'direct': True})

By default `.to_json()` will ONLY export your data dictionary items.  After all, `CleverDict` is a *dictionary* first and foremost.  However, by specifying `.to_json(fullcopy=True)` you can include **all aliases** and **all attributes** created with `setattr_direct`.

This gives you a neat way of fully saving `CleverDict` objects with all mappings and the contents of `_vars` intact.  Then, subject to normal JSON limitations, you can *completely reconstruct* your original `CleverDict` using `.from_json`:

    >>> x.to_json(file_path="mydata.json", fullcopy=True)

    >>> y = CleverDict.from_json(file_path="mydata.json")
    >>> y == x
    True

    >>> j = x.to_json(fullcopy=True)
    >>> j
    {
    "_mapping_encoded": {
        "'total'": 6,
        "'usergroup'": "Knights of Ni"    },
    "_aliases_encoded": {},
    "_vars": {}
    }

    >>> y = CleverDict.from_json(j)
    >>> y == x
    True

## 8. THE AUTO-SAVE FEATURE

Following the "*batteries included*" philosophy, we've included two common autosave/autodelete options which will save your `CleverDict` data to the recommended 'Settings' folder of whichever Operating System you're using:

---

**BUILT-IN AUTOSAVE #1: DICTIONARY DATA ONLY**


    >>> x = CleverDict({"Patient Name": "Wobbly Joe", "Test Result": "Positive"})

    >>> x.autosave()

    ⚠ Autosaving to:
    C:\Users\Peter\AppData\Roaming\CleverDict\2021-01-20-15-03-54-30.json

    >>> x.Prognosis = "Not good"

If you browse the json file (a simple click on the Terminal output if you've enable this in some IDEs), you should see `.Prognosis` has been saved along with any other new/changed values.  Any values you delete will be automatically removed.

---
**BUILT-IN AUTOSAVE #2: FULL COPY**

In **Section 7** you saw how you can use `.to_json(fullcopy=True)` to create a fully reconstructable image of your `CleverDict` as a JSON string or file.  You can set this as your autosave/autodelete method using the same simple syntax:

    >>> x.autosave(fullcopy=True)

With this method all aliases (in `_aliases`) and directly set attributes (in `_vars`) will be saved whenever attributes are created, changed, or deleted as well the main dictionary data.

---


In both cases the file path is stored as `.save_path` using `.setattr_direct()` which you read about above (unless you skipped or fell asleep!).

    >>> x.save_path
    WindowsPath('C:/Users/Peter/AppData/Roaming/CleverDict/2021-01-20-15-03-54-30.json')

To disable autosave/autodelete activity just enter:

    >>> x.autosave("off")

    ⚠ Autosave disabled.

    ⓘ Previous updates saved to:
       C:\Users\Peter\AppData\Roaming\CleverDict\2021-01-20-15-03-54-30.json

Or for finer control:

    >>> CleverDict.save = CleverDict.original_save
    >>> CleverDict.delete = CleverDict.original_delete


## 9. CREATING YOUR OWN AUTO-SAVE FUNCTION

You can set pretty much any function to be run **automatically** when a `CleverDict` value is *created or changed*, for example to update a database, save to a file, or synchronise with cloud storage etc.  Less code for you, and less chance you'll forget to explicitly call that crucial update function...  You just need to overwrite the `CleverDict.save` method with your own one:

    >>> CleverDict.save = your_save_function

Similarly the `CleverDict.delete` method is called automatically when an attribute or value is *deleted*.  Like `.save`, it does nothing by default, but you can overwrite it with your own function e.g. for popping up a confirmation request or notification, creating a backup before deleting a record from your database, config file, cloud storage etc.

    >>> CleverDict.delete = your_delete_function

When writing your own `save` function, you'll need to specify three arguments as shown in the following example:

    >>> def your_save_function(self, name, value):
            print(f" ⓘ  .{name} (object type: {self.__class__.__name__}) = {value} {type(value)}")

* **self**: because we're dealing with objects and classes...
* **key**: a valid Python `.attribute` or *key* name preferably, otherwise you'll only be able to access it using `dictionary['key']` notation later on.
* **value**: anything


The `.save()` and `.delete()` methods are *class* methods, so changing `CleverDict.save` will apply the new `.save()` method to ***all*** previously created `CleverDict` objects as well as future ones.  If you want to specify different behaviours for different objects, you can create subclasses that inherit from `CleverDict`, then set a different `.save()` or `.delete()` function for each subclass e.g.:

    >>> class Type1(CleverDict): pass
    >>> Type1.save = my_save_function1

    >>> class Type2(CleverDict): pass
    >>> Type2.save = my_save_function2

But READ ON if you decide to subclass `CleverDict`...

## 10. SUBCLASSING

When you create a subclass of `CleverDict` remember to call `super().__init__()` *before* trying to set any further class or object attributes, otherwise you'll run into trouble:

    class Movie(CleverDict):
        index = []
        def __init__(self, title, **kwargs):
            super().__init__(**kwargs)
            self.title = title
            Movie.index += [self]

In the example above we created a simple class variable `.index` to keep a list of instances for future reference:

    >>> x = Movie("The Wizard of Oz")
    >>> print(Movie.index)
    [Movie({'title': 'The Wizard of Oz'}, _aliases={}, _vars={})]

    >>> x.info()
    Movie:
        self['title'] == self.title == 'The Wizard of Oz"

You could also over-write the `.save()` method and create an `.index` attribute for example:

    class SaveDict(CleverDict):
        def __init__(self, *args, **kwargs):
            self.setattr_direct('index', [])
            super().__init__(*args, **kwargs)

        def save(self, name, value):
            self.index.append((name, value))

> NB: `.append()` does not register as 'setting' a `CleverDict` value and so does NOT trigger the `.save()` method itself (thankfully) otherwise we'd in a whole world of recursion pain...

## 11. CONTRIBUTING

We'd love to see Pull Requests (including relevant tests) from other contributors, particularly if you can help evolve `CleverDict` to make it play nicely with other classes and formats.

For a list of all outstanding **Feature Requests** and (heaven forbid!) actual *Issues* please have a look here and maybe you can help out?

https://github.com/PFython/cleverdict/issues?q=is%3Aopen+is%3Aissue


## 12. CREDITS
`CleverDict` was developed jointly by Ruud van der Ham, Peter Fison, Loic Domaigne, and Rik Huygen who met on the friendly and excellent Pythonista Cafe forum (www.pythonistacafe.com).  Peter got the ball rolling after noticing a super-convenient, but not fully-fledged feature in Pandas that allows you to (mostly) use `object.attribute` syntax or `dictionary['key']` syntax interchangeably. Ruud, Loic and Rik then started swapping ideas for a hybrid  dictionary/data class, originally based on `UserDict` and the magic of `__getattr__` and `__setattr__`.

> **Fun Fact:** `CleverDict` was originally called `attr_dict` but several confusing flavours of this and `AttrDict` exist on PyPi and Github already.  Hopefully this new tongue-in-cheek name is more memorable and raises a smile ;)

If you find `cleverdict` helpful, please feel free to:

<a href="https://www.buymeacoffee.com/pfython" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/arial-yellow.png" alt="Buy Me A Coffee" width="217px" ></a>


