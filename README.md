# CleverDict

![simplicity](https://image.slidesharecdn.com/iotshifts20150911-151021225240-lva1-app6891/95/smart-citizens-populating-smart-cities-iotshifts-19-638.jpg?cb=1506979421)

## OVERVIEW

```CleverDict``` is a hybrid Python data class which allows both ```object.attribute``` and ```dictionary['key']``` notation to be used simultaneously and interchangeably.  It's particularly handy when your code is mainly object-orientated but you want a 'DRY' and extensible way to import data in json/dictionary format into your objects... or vice versa... without having to write extra code just to handle the translation.

The class also optionally triggers a ```.save()``` method (which you can adapt or overwrite) which it calls whenever an attribute or dictionary value is created or changed.  This is especially useful if you want your object's values to be automatically pickled, encoded, saved to a file or database, uploaded to the cloud etc. without having to slavishly call your update function after every single operation where attributes (might) change.


## INSTALLATION
No dependencies.  Very lightweight:

    pip install cleverdict

or to cover all bases...

    python -m pip install cleverdict --upgrade --user

## QUICKSTART

```CleverDict``` objects behave like normal Python dictionaries, but with the convenience of immediately offering read and write access to their data (keys and values) using the ```object.attribute``` syntax, which many people find easier to type and more intuitive to read and understand.

### 1. BASIC USE

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

### 2. DATA FROM OTHER OBJECTS
You can import an existing object's data (but not its methods) directly using ```vars()``` and print a summary of all attributes using .info():

    >>> class X: pass
    >>> a = X(); a.name = "Percival"
    >>> x = y = z = CleverDict(vars(a))
    >>> x.info()

    CleverDict:
    x == y == z

    z['name'] == z.name == 'Percival'

    >>> x.info(as_str=True)  # Returns a string e.g. for further parsing
    "CleverDict: \nx == y == z\n\nz['name'] == z.name == 'Percival'"


### 3. KEYWORD ARGUMENTS
You can also supply keyword arguments like this:

    >>> x = CleverDict(created = "today", review = "tomorrow")

    >>> x.created
    'today'
    >>> x['review']
    'tomorrow'

Or using the ```.fromkeys()``` method like this:

    >>> x = CleverDict().fromkeys(["Abigail", "Tino", "Isaac"], "Year 9")

    >>> x
    CleverDict([('Abigail', 'Year 9'), ('Tino', 'Year 9'), ('Isaac', 'Year 9')])

Regardless of which syntax you use, new values are immediately available via both methods:

    >>> x['life'] = 42
    >>> x.life += 1
    >>> x['life']
    43

    >>> del x['life']
    >>> x.life
    # KeyError: 'life'


### 4. ATTRIBUTE NAMES AND ALIASES

By default ```CleverDict``` tries to find valid attribute names for dictionary keys which would otherwise fail.  This includes keywords, null strings, most punctuation marks, and keys starting with a numeral.  So for example ```7``` (integer) becomes ```"_7"``` (string):

    >>> x = CleverDict({7: "Seven"})

    >>> x._7
    'Seven'
    >>> x
    CleverDict({7: 'Seven'}, _aliases={'_7': 7}, _vars={})

```CleverDict``` keeps the original dictionary keys and values unchanged and remembers any normalised attribute names as aliases in ```._alias```.  You can add or delete further aliases with .add_alias and .delete_alias:

    >>> x.add_alias(7, "NumberSeven")
    >>> x
    CleverDict({7: 'Seven'}, _aliases={'_7': 7, 'NumberSeven': 7}, _vars={})

**Footnote 1** Most unicode letters are valid in attribute names since [PEP3131](https://www.python.org/dev/peps/pep-3131/), but ```CleverDict``` replaces other invalid characters such as punctuation marks with "```_```" on a first come, first served basis.  This can result in an ```KeyError``` (which you can get round by renaming the offending dictionary keys).  For example:

    >>> x = CleverDict({"one-two": "hypen", "one/two": "forward slash"})
    KeyError: "'one_two' already an alias for 'one-two'"

**Footnote 2** Not everyone knows that when creating a Python dictionary, the keys ```0```, ```0.0```, and ```False``` are considered the same in Python.  Likewise ```1```, ```1.0```, and ```True```, and ```1234``` and ```1234.0```.  Also if you create a regular dictionary using more than one of these different identities, they will appear to 'overwrite' each other keeping the first Key specified but the last Value specified:

    >>> x = {1: "one", True: "the truth"}
    >>> x
    {1: 'the truth'}

You'll be relieved to know ```CleverDict``` handles these cases but we thought it was worth mentioning in case you came across them first and wondered what the heck was going on!  You can always work out what's going on 'under the hood' by looking at the aliases with ```.info()```.


### 5. ENABLING THE AUTO-SAVE FUNCTION
You can set pretty much any function to run automatically whenever a ```CleverDict``` value is created or changed.  There's an example function in ```cleverict.test_cleverdict``` which demonstrates this:

    >>> from cleverdict.test_cleverdict import example_save_function
    >>> CleverDict.save = example_save_function

    >>> x = CleverDict({'total':6, 'usergroup': "Knights of Ni"})
    Notional save to database: .total = 6 <class 'int'>
    Notional save to database: .usergroup = Knights of Ni <class 'str'>

    >>> x.life = 42
    Notional save to database: .life = 42 <class 'int'>


The example function above also appends output to a file, which you might want for debugging, auditing,  further analysis etc.:

    >>> with open("example.log","r") as file:
    ...     log = file.read()

    >>> log.splitlines()
    ["Notional save to database: .total = 6 <class 'int'>",
    "Notional save to database: .usergroup = Knights of Ni <class 'str'>"]

**NB**: The ```.save()``` method is a *class* method, so changing ```CleverDict.save``` will apply the new ```.save()``` method to all previously created ```CleverDict``` objects as well as future ones.


### 6. CREATING YOUR OWN AUTO-SAVE FUNCTION
When writing your own ```.save()``` function, you'll need to specify three arguments as follows:


    >>> def your_function(self, key: str, value: any):
    ...     print("Ni!")


* **self**: because we're dealing with objects and classes...
* **key**: a valid Python ```.attribute``` key preferably, otherwise you'll only be able to access it using ```dictionary['key']``` notation later on.
* **value**: anything

### 7. SETTING DIFFERENT AUTO-SAVE FUNCTIONS FOR DIFFERENT OBJECTS
If you want to specify different ```.save()``` behaviours for different objects, consider creating subclasses that inherit from ```CleverDict``` and set a different
```.save()``` function for each subclass e.g.:

    >>> class Type1(CleverDict): pass
    >>> Type1.save = my_save_function1

    >>> class Type2(CleverDict): pass
    >>> Type2.save = my_save_function2


### 8. SETTING AN ATTRIBUTE WITHOUT CREATING A DICTIONARY ITEM
We've included the ```.setattr_direct()``` method in case you want to set an object attribute *without* creating the corresponding dictionary key/value.  This could be useful for storing save data for example, and is used internally to store aliases in ```._aliases``` and ```_vars```.

Here's one way you could create a ```.store``` attribute and customise the auto-save behaviour for example:

    class SaveDict(CleverDict):
        def __init__(self, *args, **kwargs):
            self.setattr_direct('store', [])
            super().__init__(*args, **kwargs)

        def save(self, name, value):
            self.store.append((name, value))

## CONTRIBUTING

We'd love to see Pull Requests (and relevant tests) from other contributors, particularly if you can help with the following:

It would be great if a future evoloution of ```CleverDict``` allowed it to be  'grafted on' to existing classes simply using inheritance, without causing recursion or requiring a rewrite/overwrite of the original class.

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


## CREDITS
```CleverDict``` was developed jointly by Ruud van der Ham, Peter Fison, Loic Domaigne, and Rik Huygen who met on the friendly and excellent Pythonista Cafe forum (www.pythonistacafe.com).  Peter got the ball rolling after noticing a super-convenient, but not fully-fledged feature in Pandas that allows you to (mostly) use ```object.attribute``` syntax or ```dictionary['key']``` syntax interchangeably. Ruud, Loic and Rik then started swapping ideas for a hybrid  dictionary/data class based on ```UserDict``` and the magic of ```__getattr__``` and ```__setattr__```, and ```CleverDict``` was born*.

>(\*) ```CleverDict``` was originally called ```attr_dict``` but several confusing flavours of this and ```AttrDict``` exist on PyPi and Github already.  Hopefully the new name raises a wry smile as well as being more memorable...
