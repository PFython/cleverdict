# CleverDict

![simplicity](https://image.slidesharecdn.com/iotshifts20150911-151021225240-lva1-app6891/95/smart-citizens-populating-smart-cities-iotshifts-19-638.jpg?cb=1506979421)

## 1. OVERVIEW

```CleverDict``` is a hybrid Python data class which allows both ```object.attribute``` and ```dictionary['key']``` notation to be used simultaneously and interchangeably.  It's particularly handy when your code is mainly object-orientated but you want a 'DRY' and extensible way to import data in json/dictionary format into your objects... or vice versa... without having to write extra code just to handle the translation.

```CleverDict``` also calls a ```.save``` method whenever an attribute or dictionary value is created or changed.  Initially the ```.save```method does nothing, but you can overwrite it with your own function to do useful things automatically every time an attribute changes in future e.g. pickle, encode, save data to a file or database, upload to the cloud etc. No more slavishly writing a call your own "save" function every... single... time...


## 2. INSTALLATION
No dependencies.  Very lightweight:

    pip install cleverdict

or to cover all bases...

    python -m pip install cleverdict --upgrade --user




## 3. BASIC USE

```CleverDict``` objects behave like normal Python dictionaries, but with the convenience of immediately offering read and write access to their data (keys and values) using the ```object.attribute``` syntax, which many people find easier to type and more intuitive to read and understand.

You can create a ```CleverDict``` object in exactly the same way as a regular Python dictionary:

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

The values are then immediately available using either dictionary or .attribute syntax:

    >>> x['life'] = 42
    >>> x.life += 1
    >>> x['life']
    43

    >>> del x['life']
    >>> x.life
    # KeyError: 'life'


## 4. OTHER WAYS TO GET STARTED
You can also create a ```CleverDict``` instance using keyword arguments like this:

    >>> x = CleverDict(created = "today", review = "tomorrow")

    >>> x.created
    'today'
    >>> x['review']
    'tomorrow'

Or using a list of tuple/list pairs:

    >>> x = CleverDict().fromlist([(1, "one"), [2, "two"], (3, "three")])

    >>> x._1
    'one'
    >>> x._2
    'two'
    >>> x._3_
    'three'

    This can be helpful for serialisation issues like ```json.dumps()``` converting numeric dictionary keys to strings, and for use with Client/Server apps where there are limits on what object can be passed between the Client and Server (*).


Or using the ```.fromkeys()``` method like this:

    >>> x = CleverDict.fromkeys(["Abigail", "Tino", "Isaac"], "Year 9")

    >>> x
    CleverDict({'Abigail': 'Year 9', 'Tino': 'Year 9', 'Isaac': 'Year 9'}, _aliases={}, _vars={})

Or by using ```vars()``` to import another object's data (but not its methods):

    >>> class X: pass
    >>> a = X(); a.name = "Percival"
    >>> x = CleverDict(vars(a))

    >>> x
    CleverDict({'name': 'Percival'}, _aliases={}, _vars={})


(*) You can use the ```.tolist()``` method to generate a list of key/value pairs from a ```CleverDict``` object:

    >>> x = CleverDict({1: "one", 2: "two"})

    >>> x.tolist()
    [(1, 'one'), (2, 'two')]




## 5. ATTRIBUTE NAMES AND ALIASES

By default ```CleverDict``` tries to find valid attribute names for dictionary keys which would otherwise fail.  This includes keywords, null strings, most punctuation marks, and keys starting with a numeral.  So for example ```7``` (integer) becomes ```"_7"``` (string):

    >>> x = CleverDict({7: "Seven"})

    >>> x._7
    'Seven'
    >>> x
    CleverDict({7: 'Seven'}, _aliases={'_7': 7}, _vars={})

```CleverDict``` keeps the original dictionary keys and values unchanged and remembers any normalised attribute names as aliases in ```._alias```.  You can add or delete further aliases with ```.add_alias``` and ```.delete_alias```, but the original key will never be deleted, even if all aliases and .attributes are removed:

    >>> x.add_alias(7, "NumberSeven")

    >>> x
    CleverDict({7: 'Seven'}, _aliases={'_7': 7, 'NumberSeven': 7}, _vars={})

    >>> x.delete_alias(["_7","NumberSeven"])

    >>> x
    CleverDict({7: 'Seven'}, _aliases={}, _vars={})
    >>> x._7
    AttributeError: '_7'


## 6. DEEPER DIVE INTO ATTRIBUTE NAMES

Did you know that the dictionary keys ```0```, ```0.0```, and ```False``` are considered the same in Python?  Likewise ```1```, ```1.0```, and ```True```, and ```1234``` and ```1234.0```?  If you create a regular dictionary using more than one of these different identities, they'll appear to 'overwrite' each other, keeping the **first Key** specified but the **last Value** specified, reading left to right:

    >>> x = {1: "one", True: "the truth"}

    >>> x
    {1: 'the truth'}

You'll be relieved to know ```CleverDict``` handles these cases but we thought it was worth mentioning in case you came across them first and wondered what the heck was going on!  *"Explicit is better than implicit"*, right?  You can inspect all the key names and .attribute aliases using the ```.info()``` method, as well as any aliases for the object itself:

    >>> x = y = z = CleverDict({1: "one", True: "the truth"})
    >>> x.info()

    CleverDict:
    x is y is z
    x[1] == x['_1'] == x['_True'] == x._1 == x._True == 'the truth'

    # Use 'as_str=True' to return the results as a string
    >>> x.info(as_str=True)

    "CleverDict:\n    x is y is z\n    x[1] == x['_1'] == x['_True'] == x._1 == x._True == 'the truth'"

Did you also know that since [PEP3131](https://www.python.org/dev/peps/pep-3131/) many unicode letters are valid in attribute names?  ```CleverDict``` handles this and replaces all remaining *invalid* characters such as punctuation marks with "```_```" on a first come, first served basis.  This can result in a ```KeyError```, which you can get round by renaming the offending dictionary keys.  For example:

    >>> x = CleverDict({"one-two": "hypen",
                        "one/two": "forward slash"})
    KeyError: "'one_two' already an alias for 'one-two'"

    >>> x = CleverDict({"one-two": "hypen",
                        "one_or_two": "forward slash"})

## 7. SETTING AN ATTRIBUTE WITHOUT CREATING A DICTIONARY ITEM
We've included the ```.setattr_direct()``` method in case you want to set an object attribute *without* creating the corresponding dictionary key/value.  This could be useful for storing save data for example, and is used internally to store aliases in ```._aliases```.  Variables which have been set directly in this way are stored in ```_vars```.

    >>> x = CleverDict()
    >>> x.setattr_direct("direct", False)

    >>> x
    CleverDict({}, _aliases={}, _vars={'direct': False})

Here's one way you could create a ```.store``` attribute and customise the auto-save behaviour for example:

    class SaveDict(CleverDict):
        def __init__(self, *args, **kwargs):
            self.setattr_direct('store', [])
            super().__init__(*args, **kwargs)

        def save(self, name, value):
            self.store.append((name, value))

## 8. THE AUTO-SAVE FEATURE
You can set pretty much any function to run automatically whenever a ```CleverDict``` value is created or changed.  There's an example function in ```cleverict.test_cleverdict``` which demonstrates how you just need to overwrite the ```.save``` method with your own:

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

**NB**: The ```.save``` method is a *class* method, so changing ```CleverDict.save``` will apply the new ```.save``` method to all previously created ```CleverDict``` objects as well as future ones.


## 9. CREATING YOUR OWN AUTO-SAVE FUNCTION
When writing your own ```.save``` function, you'll need to specify three arguments as follows:


    >>> def your_function(self, key: str, value: any):
    ...     print("Ni!")


* **self**: because we're dealing with objects and classes...
* **key**: a valid Python ```.attribute``` key preferably, otherwise you'll only be able to access it using ```dictionary['key']``` notation later on.
* **value**: anything

## 10. SETTING DIFFERENT AUTO-SAVE FUNCTIONS FOR DIFFERENT OBJECTS
If you want to specify different ```.save``` behaviours for different objects, consider creating subclasses that inherit from ```CleverDict``` and set a different
```.save``` function for each subclass e.g.:

    >>> class Type1(CleverDict): pass
    >>> Type1.save = my_save_function1

    >>> class Type2(CleverDict): pass
    >>> Type2.save = my_save_function2


## 11. CONTRIBUTING

We'd love to see Pull Requests (and relevant tests) from other contributors, particularly if you can help evolve ```CleverDict``` to make it play nicely with other classes simply using inheritance, without causing recursion or requiring a rewrite/overwrite of the original class.

For example it would be great if we could graft on the CleverDict methods to other Classes, something like this:

    >>> class MyDatetime(datetime.datetime, CleverDict):
    ...     pass

    >>> mdt = MyDatetime.now()
    >>> mdt.hour
    4
    >>> mdt['hour']
    4

Unfortunately at the moment this raises an error:
```TypeError: multiple bases have instance lay-out conflict```

... which is beyond the author's current Python level!


## 12. CREDITS
```CleverDict``` was developed jointly by Ruud van der Ham, Peter Fison, Loic Domaigne, and Rik Huygen who met on the friendly and excellent Pythonista Cafe forum (www.pythonistacafe.com).  Peter got the ball rolling after noticing a super-convenient, but not fully-fledged feature in Pandas that allows you to (mostly) use ```object.attribute``` syntax or ```dictionary['key']``` syntax interchangeably. Ruud, Loic and Rik then started swapping ideas for a hybrid  dictionary/data class, originally based on ```UserDict``` and the magic of ```__getattr__``` and ```__setattr__```.

>(\*) ```CleverDict``` was originally called ```attr_dict``` but several confusing flavours of this and ```AttrDict``` exist on PyPi and Github already.  Hopefully this new tongue-in-cheek name is more memorable and raises a smile as you think about the Clever Dicks who created it ;)
