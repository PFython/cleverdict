from cleverdict import CleverDict, my_example_save_function
import pytest
import os
from collections import UserDict

class Test_Core_Functionality():
    def test_creation_using_existing_dict(self):
        """ CleverDicts can be creates from existing dictionaries """
        x = CleverDict({'total':6, 'usergroup': "Knights of Ni"})
        assert x.total == 6
        assert x['total'] == 6
        assert x.usergroup == "Knights of Ni"
        assert x['usergroup'] == "Knights of Ni"

    def test_creation_using_existing_UserDict(self):
        """ CleverDicts can be creates from existing UserDict objects """
        u = UserDict({'total':6, 'usergroup': "Knights of Ni"})
        x = CleverDict(u)
        assert x.total == 6
        assert x['total'] == 6
        assert x.usergroup == "Knights of Ni"
        assert x['usergroup'] == "Knights of Ni"

    def test_creation_using_keyword_arguments(self):
        """ CleverDicts can be created using keyword assignment """
        x = CleverDict(created = "today", review = "tomorrow")
        assert x.created == "today"
        assert x['created'] == "today"
        assert x.review == "tomorrow"
        assert x['review'] == "tomorrow"

    def test_creation_using_vars(self):
        """ Works for 'simple' data objects i.e. no methods just data """
        class My_class:
            pass
        m = My_class()
        m.subject = "Python"
        x = CleverDict(vars(m))
        assert x.subject == "Python"
        assert x['subject'] == "Python"

    def test_conversion_of_invalid_attribute_name(self):
        """
        x.1 is an invalid attribute name in Python, so CleverDict
        will convert this to x._1
        """
        x = CleverDict({1: "First Entry", " ": "space", "??": "question"})
        assert x._1 == "First Entry"

    def test_value_change(self):
        """ New attribute values should update dictionary keys & vice versa """
        x = CleverDict()
        x.life = 42
        x['life'] = 43
        assert x.life == 43
        assert x['life'] == 43
        x.life = 42
        assert x.life == 42
        assert x['life'] == 42

class Test_Save_Functionality():

    def delete_log(self):
        try:
            os.remove("example.log")
        except FileNotFoundError:
            pass

    def test_save_on_creation(self):
        """ Once set, CleverDict.save should be called on creation """
        CleverDict.save = my_example_save_function
        self.delete_log()
        x = CleverDict({'total':6, 'usergroup': "Knights of Ni"})
        with open("example.log","r") as file:
            log = file.read()
        assert log == "Notional save to database: .total = 6 <class 'int'>Notional save to database: .usergroup = Knights of Ni <class 'str'>"
        self.delete_log()

    def test_save_on_update(self):
        """ Once set, CleverDict.save should be called after updates """
        x = CleverDict({'total':6, 'usergroup': "Knights of Ni"})
        self.delete_log()
        CleverDict.save = my_example_save_function
        x.total += 1
        with open("example.log","r") as file:
            log = file.read()
        assert log == "Notional save to database: .total = 7 <class 'int'>"
        self.delete_log()

class MyClass(CleverDict):
    def __init__(self,id):
        self.id = id
