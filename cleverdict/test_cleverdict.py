from cleverdict import CleverDict
import pytest
import os
from collections import UserDict


def my_example_save_function(self, name: str = "", value: any = ""):
    """
    Example of a custom function which can be called by self._save()
    whenever the value of a CleverDict instance is created or changed.
    Required arguments are: self, name: str and value: any
    Specify this (or any other) function as the default 'save' function as follows:
    CleverDict.save = my_example_save_function
    """
    output = f"Notional save to database: .{name} = {value} {type(value)}"
    print(output)
    with open("example.log", "a") as file:
        file.write(output)


class Test_Core_Functionality:
    def test_creation_using_existing_dict(self):
        """ CleverDicts can be creates from existing dictionaries """
        x = CleverDict({"total": 6, "usergroup": "Knights of Ni"})
        assert x.total == 6
        assert x["total"] == 6
        assert x.usergroup == "Knights of Ni"
        assert x["usergroup"] == "Knights of Ni"

    def test_creation_using_existing_UserDict(self):
        """ CleverDicts can be creates from existing UserDict objects """
        u = UserDict({"total": 6, "usergroup": "Knights of Ni"})
        x = CleverDict(u)
        assert x.total == 6
        assert x["total"] == 6
        assert x.usergroup == "Knights of Ni"
        assert x["usergroup"] == "Knights of Ni"

    def test_creation_using_keyword_arguments(self):
        """ CleverDicts can be created using keyword assignment """
        x = CleverDict(created="today", review="tomorrow")
        assert x.created == "today"
        assert x["created"] == "today"
        assert x.review == "tomorrow"
        assert x["review"] == "tomorrow"

    def test_creation_using_vars(self):
        """ Works for 'simple' data objects i.e. no methods just data """

        class My_class:
            pass

        m = My_class()
        m.subject = "Python"
        x = CleverDict(vars(m))
        assert x.subject == "Python"
        assert x["subject"] == "Python"

    def test_creation_using_fromkeys(self):
        """ Works for initiating with the same value"""
        x = CleverDict().fromkeys(["a", 1, "what?"], "val")
        assert x.a == "val"
        assert x._1 == "val"
        assert x.what_ == "val"

    def test_raises_error(self):
        x = CleverDict()
        with pytest.raises(AttributeError):
            a = x.a
        with pytest.raises(KeyError):
            a = x["a"]

    def test_normalizing(self):
        """
        x.1 is an invalid attribute name in Python, so CleverDict
        will convert this to x._1
        """
        x = CleverDict({1: "First Entry", " ": "space", "??": "question"})
        assert x._1 == "First Entry"
        assert x["-1"] == "First Entry"
        assert x[1] == "First Entry"
        with pytest.raises(AttributeError):
            x["1"] = 5
        with pytest.raises(AttributeError):
            x = CleverDict({1: "First Entry", "1": "space", "??": "question"})
        x["else"] = "is else"
        assert x["else"] == "is else"
        assert x["_else"] == "is else"
        assert x._else == "is else"
        with pytest.raises(AttributeError):
            x["?else"] = "other"
        x._4 = "abc"
        with pytest.raises(AttributeError):
            x["4"] = "def"
        x[12345.0] = "klm"
        assert x._12345 == "klm"

    def test_value_change(self):
        """ New attribute values should update dictionary keys & vice versa """
        x = CleverDict()
        x.life = 42
        x["life"] = 43
        assert x.life == 43
        assert x["life"] == 43
        x.life = 42
        assert x.life == 42
        assert x["life"] == 42
        x["1"] = 10
        assert x["1"] == 10
        assert x["_1"] == 10
        assert x._1 == 10
        x["_1"] = 11
        assert x["1"] == 11
        assert x["_1"] == 11
        assert x._1 == 11
        x._1 = 12
        assert x["1"] == 12
        assert x["_1"] == 12
        assert x._1 == 12

    def test_0_1_functionality(self):
        x = CleverDict()
        x[0] =0
        x[False] = 1
        x[1] = 2
        x[True] = 3
        assert x[0] == 1
        assert x[False] == 1
        assert x['_0'] == 1
        assert x['_False'] == 1
        assert x._0 == 1
        assert x._False == 1
        assert x[1] == 3
        assert x[True] == 3
        assert x['_1'] == 3
        assert x['_True'] == 3
        assert x._1 == 3
        assert x._True == 3
        x = CleverDict()
        x[False] =0
        x[0] = 1
        x[True] = 2
        x[1] = 3
        assert x[0] == 1
        assert x[False] == 1
        assert x['_0'] == 1
        assert x['_False'] == 1
        assert x._0 == 1
        assert x._False == 1
        assert x[1] == 3
        assert x[True] == 3
        assert x['_1'] == 3
        assert x['_True'] == 3
        assert x._1 == 3
        assert x._True == 3

    def test_repr_and_eq(self):
        x = CleverDict()
        x[0] =0
        x[False] = 1
        x[1] = 2
        x[True] = 3
        x.a = 4
        x['what?'] = 5
        y = eval(repr(x))
        assert x == y
        y.b = 6
        assert x!= y


class Test_Save_Functionality:
    def delete_log(self):
        try:
            os.remove("example.log")
        except FileNotFoundError:
            pass

    def test_save_on_creation(self):
        """ Once set, CleverDict.save should be called on creation """
        CleverDict.save = my_example_save_function
        self.delete_log()
        x = CleverDict({"total": 6, "usergroup": "Knights of Ni"})
        with open("example.log", "r") as file:
            log = file.read()
        assert (
            log
            == "Notional save to database: .total = 6 <class 'int'>Notional save to database: .usergroup = Knights of Ni <class 'str'>"
        )
        self.delete_log()

    def test_save_on_update(self):
        """ Once set, CleverDict.save should be called after updates """
        x = CleverDict({"total": 6, "usergroup": "Knights of Ni"})
        self.delete_log()
        CleverDict.save = my_example_save_function
        x.total += 1
        with open("example.log", "r") as file:
            log = file.read()
        assert log == "Notional save to database: .total = 7 <class 'int'>"
        self.delete_log()

    def test_save_misc(self):
        class SaveDict(CleverDict):
            def __init__(self, *args, **kwargs):
                self.setattr_direct('store', [])
                super().__init__(*args, **kwargs)

            def save(self, name, value):
                self.store.append((name, value))

        x = SaveDict({"a": 1, 2: 2})
        x.b = 3
        x["c"] = 4
        x[3] = 5
        x._3 = 6
        x[3] = 7
        x["_3"] = 8
        try:
            x["?3"] = 9
        except AttributeError:
            pass
        x._4 = 9
        x["_4"] = 10
        try:
            x["4"] = 11
        except AttributeError:
            pass
        assert x.store == [("a", 1), (2, 2), ("b", 3), ("c", 4), (3, 5), (3, 6), (3, 7), (3, 8), ("_4", 9), ("_4", 10)]


    def test_setattr_direct(self):
        x = CleverDict()
        x.setattr_direct("a", "A")
        assert x.a == "A"
        with pytest.raises(KeyError):
            a = x["A"]

if __name__ == "__main__":
    pytest.main(["-vv", "-s"])

