# CleverDict

![simplicity](https://twitter.com/InspiringThinkn/status/929220940025626625/photo/1)

## Overview

```CleverDict``` is a hybrid Python data class which allows both ```object.attribute``` and ```dictionary['key']``` notation to be used simultaneously and interchangeably.  It's particularly handy when your code is mainly object-orientated but you want a 'DRY' and extensible way to import data in json/dictionary format into your objects... or vice versa... without having to write extra code just to handle the translation.

The class also optionally triggers a ```.save()``` method (which you can adapt or overwrite) which it calls whenever an attribute or dictionary value is created or changed.  This is especially useful if you want your object's values to be automatically pickled, encoded, saved to a file or database, uploaded to the cloud etc. without having to explicitly call your update function after every single operation where attributes (might) change.


## Installation
No dependencies.  Very lightweight:

    pip install cleverdict

or to cover all bases...

    python -m pip install cleverdict --upgrade --user

## Quickstart

```CleverDict``` objects behave like normal Python dictionaries, but with the convenience of immediately offering read and write access to their data (keys and values) using the ```object.attribute``` syntax, which many people find easier to type and more intuitive to read and understand:

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

You can also supply keyword arguments like this:

    >>> x = CleverDict(created = "today", review = "tomorrow")

    >>> x.created
    'today'
    >>> x['review']
    'tomorrow'

Regardless of which syntax you use, new values are immediately available via both methods:

    >>> x['life'] = 42
    >>> x.life += 1
    >>> x['life']
    43

    >>> del x['life']
    >>> x.life
    # KeyError: 'life'

You can import an existing object's data (but not its methods) directly using ```vars()```:

    x = CleverDict(vars(my_existing_object))

    >>> list(x.items())
    [('total', 6), ('usergroup', 'Knights of Ni'), ('life', 42)]

You can set pretty much any function to run automatically whenever a ```CleverDict``` value is created or changed.  There's an example function in ```cleverict.test_cleverdict``` which illustrates this option:

    >>> from cleverdict.test_cleverdict import my_example_save_function
    >>> CleverDict.save = my_example_save_function

    >>> x = CleverDict({'total':6, 'usergroup': "Knights of Ni"})
    Notional save to database: .total = 6 <class 'int'>
    Notional save to database: .usergroup = Knights of Ni <class 'str'>

    >>> x.life = 42
    Notional save to database: .life = 42 <class 'int'>


The example function above also appends output to a file, which you might want for debugging, auditing,  further analysis etc.:

    >>> with open("example.log","r") as file:
    ...     log = file.read()

    >>> log.splitlines()
    ["Notional save to database: .age = 10 <class 'int'>",
    "Notional save to database: .total = 6 <class 'int'>",
    "Notional save to database: .usergroup = Knights of Ni <class 'str'>"]

**NB**: The ```.save()``` method is a *class* method, so changing ```CleverDict.save``` will apply the new ```.save()``` method to all previously created ```CleverDict``` objects as well.

If you want to specify different ```.save()``` behaviours for different objects, consider creating sublasses that inherit from ```CleverDict``` and set a different
```.save()``` function for each subclass e.g.:

    >>> class Type1(CleverDict): pass
    >>> Type1.save = my_save_function1

    >>> class Type2(CleverDict): pass
    >>> Type2.save = my_save_function2

When writing your own ```.save()``` function, you'll need to specify three arguments as follows:


    >>> def your_function(self, name: str = "", value: any = ""):
    ...     print("Ni!")


* **self**: because we're dealing with objects and classes...
* **name**: a valid Python ```.attribute``` name preferably, otherwise you'll only be able to access it using ```dictionary['key']``` notation later on.
* **value**: anything

If you want to overwrite the ```__str__``` method with your own function, or delete it so ```print()``` and ```str()``` default to ```__repr__``` that's easy enough too:

    >>> print(x)
    .total = 6 <class 'int'>
    .usergroup = Knights of Ni <class 'str'>

    >>> def my__str__replacement(self):
    ...     return str(type(self))

    >>> setattr(CleverDict, "__str__", my__str__replacement)
    >>> print(x)
    <class 'cleverdict.cleverdict.CleverDict'>

    >>> delattr(CleverDict, "__str__")
    >>> print(x)
    CleverDict({'total':6, 'usergroup':'Knights of Ni'})

## Contributing

We'd love to see Pull Requests (and relevant tests) from other contributors, particularly if you can help with one of the following items on our wish-list:

1. It would be great if ```CleverDict``` behaviour could be easily 'grafted on' to existing classes using inheritance, without causing recursion or requiring a rewrite/overwrite of the original class.

    For example if it were as easy as:

    ```
    >>> class MyDatetime(datetime.datetime, CleverDict):
    ...     pass

    >>> mdt = MyDatetime.now()
    >>> mdt.hour
    4
    >>> mdt['hour']
    4
    ```

2. Although ```CleverDict``` does accept dictionary keys such as " " and "" and strings with characters not allowed in ```object.attribute``` names, it can't create the corresponding ```.attributes```. except if the first character is a number - it adds an underscore '_' to the attribute name:


    ```
    >>> x = CleverDict({1: "One"})

    >>> x._1
    'One'
    ```

    Is it worth creating other mappings e.g. replacing punctuation, spaces, and null strings somehow, or does that just over-complicate things when you can at least access the original keys through the dictionary?  Maybe we can offer this as an option in future versions e.g.

    ```
    >>> x = CleverDict({1: "One"}, auto_key_names = True)
    ```



## Credits
```CleverDict``` was developed jointly by Peter Fison, Ruud van der Ham, Loic Domaigne, and Rik Huygen who met on the friendly and excellent Pythonista Cafe forum (www.pythonistacafe.com).  Peter got the ball rolling after noticing a super-convenient, but not fully-fledged feature in Pandas that allows you to (mostly) use ```object.attribute``` syntax or ```dictionary['key']``` syntax interchangeably. Ruud, Loic and Rik then started swapping ideas for a hybrid  dictionary/data class based on ```UserDict``` and the magic of ```__getattr__``` and ```__setattr__```, and ```CleverDict``` was born*.

>(\*) ```CleverDict``` was originally called ```attr_dict``` but serveral confusing flavours of this and ```AttrDict``` exist on PyPi and Github already.  Hopefully the current name raises a wry smile too...
