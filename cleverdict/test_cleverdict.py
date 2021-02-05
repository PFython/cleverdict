from cleverdict import CleverDict, Expand, all_aliases
import pytest
import os
from collections import UserDict
from textwrap import dedent
import json
from pathlib import Path
import keyring
from itertools import permutations


def example_save_function(self, name=None, value=None):
    """
    Example of a custom function which can be called by self._save()
    whenever the value of a CleverDict instance is created or changed.
    Required arguments are: self, name: any and value: any
    Specify this (or any other) function as the default 'save' function as follows:
    CleverDict.save = example_save_function
    """
    if name != "_aliases":
        output = f"Notional save to database: .{name} = {value} {type(value)}"
        with open("example.log", "a") as file:
            file.write(output + "\n")


def invalid_save_function(self, key, value):
    pass


def example_delete_function(self, name=None):
    """ Example """
    output = f"Notional DELETE to database: .{name}"
    with open("example.log", "a") as file:
        file.write(output + "\n")


def invalid_delete_function(self, name, value):
    pass


def get_data(path):
    with open(path, "r") as file:
        data = file.read()
    return data


def delete_log():
    try:
        os.remove("example.log")
        return True
    except FileNotFoundError:
        return False


class Test_Initialisation:
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
        """ Works for initiating >1 keys with the same value"""
        x = CleverDict().fromkeys(["a", 1, "what?"], "val")
        assert x.a == "val"
        assert x._1 == "val"
        assert x.what_ == "val"

    def test_creation_using_list(self):
        """ Works for initiating using a list of iterables """
        x = CleverDict([(1, "one"), [2, "two"], (3, "three")])
        assert x._1 == "one"
        assert x._2 == "two"
        assert x._3 == "three"


class Test_Core_Features:
    def test_tolist(self):
        """
        Create a list of (k,v) tuples e.g. for serialising dictionaries
        with numeric keys (which isn't supported in json.dumps/.loads)
        """
        x = CleverDict({1: "one", 2: "two"})
        assert x.to_list() == [(1, "one"), (2, "two")]

    def test_use_as_dict(self):
        d = dict.fromkeys((0, 1, 23, "what?", "a"), "test")
        x = CleverDict(d)
        x.setattr_direct("b", 2)
        assert dict(x) == d

    def test_add_alias_delete_alias(self):
        """
        Aliases are created automatically after expanding 1, True
        for example.  add_alias() and delete_alias() allow us to specify
        additional attribute names as aliases, such that if the value of one
        changes, the value changes for all.
        It is not possible to delete a key.
        """
        x = CleverDict({"red": "a lovely colour", "blue": "a cool colour"})
        alias_list = ["crimson", "burgundy", "scarlet", "normalise~me"]

        x.add_alias("red", alias_list[0])
        x.add_alias("red", alias_list)
        # setting an alias that is already defined for another key is not allowed
        with pytest.raises(KeyError):
            x.add_alias("blue", alias_list[0])
        # setting via an alias is also valid
        x.add_alias("scarlet", "rood")
        assert x.rood == "a lovely colour"

        for alias in alias_list[:-1]:
            assert getattr(x, alias) == "a lovely colour"
            assert x[alias] == "a lovely colour"
        assert getattr(x, "normalise_me") == "a lovely colour"
        assert x["normalise_me"] == "a lovely colour"

        # Updating one alias (or primary Key) should update all:
        x.burgundy = "A RICH COLOUR"
        assert x.scarlet == "A RICH COLOUR"

        x.delete_alias(["scarlet"])
        with pytest.raises(AttributeError):
            x.scarlet
        assert x.crimson == "A RICH COLOUR"

        x.crimson = "the best colour of all"
        assert x.burgundy == "the best colour of all"

        with pytest.raises(KeyError):
            x.delete_alias(["scarlet"])
        # can't delete the  key element
        with pytest.raises(KeyError):
            x.delete_alias("red")

        # test 'expansion' of alias
        x.add_alias("red", True)
        assert x._True is x[True] is x._1 is x[1] is x["red"]

        x = CleverDict()
        x["2"] = 1
        x.add_alias("2", True)
        assert x.get_aliases("2") == ["2", "_2", True, "_1", "_True"]
        # removes True, '_1' and '_True'
        x.delete_alias(True)
        assert x.get_aliases("2") == ["2", "_2"]

        x = CleverDict()
        x["2"] = 1
        x.add_alias("2", True)
        assert x.get_aliases("2") == ["2", "_2", True, "_1", "_True"]
        # only remove True,not '_1' and '_True'
        with Expand(False):
            x.delete_alias(True)
        assert x.get_aliases("2") == ["2", "_2", "_1", "_True"]

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
        # can't double assign
        with pytest.raises(KeyError):
            x["+1"] = 1
        x.setattr_direct("who", "Peter")
        x.who = "Ruud"
        assert x.who == "Ruud"

    def test_info(self, capsys):
        global c  # globals are not 'seen' by info()
        z = b = a = c = CleverDict.fromkeys((0, 1, 2, "a", "what?", "return"), 0)
        c.add_alias(1, "one")
        c.delete_alias("_True")
        c.setattr_direct("b", "B")
        c.info()  # this prints to stdout
        out, err = capsys.readouterr()
        assert out == dedent(
            """\
CleverDict:
    a is b is z
    a[0] == a['_0'] == a['_False'] == a._0 == a._False == 0
    a[1] == a['_1'] == a['one'] == a._1 == a.one == 0
    a[2] == a['_2'] == a._2 == 0
    a['a'] == a.a == 0
    a['what?'] == a['what_'] == a.what_ == 0
    a['return'] == a['_return'] == a._return == 0
    a.b == 'B'
"""
        )
        z = b = a = c = CleverDict.fromkeys(["a"], "A")
        assert (
            c.info(as_str=True)
            == "CleverDict:\n    a is b is z\n    a['a'] == a.a == 'A'"
        )
        del a
        assert (
            c.info(as_str=True) == "CleverDict:\n    b is z\n    b['a'] == b.a == 'A'"
        )
        del b
        assert c.info(as_str=True) == "CleverDict:\n    z['a'] == z.a == 'A'"
        del z
        assert c.info(as_str=True) == "CleverDict:\n    x['a'] == x.a == 'A'"


class Test_Misc:
    def test_exclude(self):
        """ exclude=(Marshmallow syntax) should act as an alias for ignore= """
        x = CleverDict({"Yes": "include me", "No": "exclude/ignore me"})
        for (
            func
        ) in "__repr__() to_json() to_dict() to_list() to_lines() info(,as_str=True)".split():
            ignore = eval("x." + func.replace("(", "(ignore=['No']"))
            exclude = eval("x." + func.replace("(", "(exclude=['No']"))
            assert ignore == exclude

    def test_only(self):
        """only=[list] should return output ONLY matching the given keys"""
        x = CleverDict({"Apples": "Green", "Bananas": "Yellow", "Oranges": "Purple"})
        a_and_o = CleverDict({"Apples": "Green", "Oranges": "Purple"})
        for func in "__repr__ to_json to_dict to_list to_lines info".split():
            as_str = {"as_str": True} if func == "info" else {}
            result1 = getattr(x, func)(only=["Apples", "Oranges"], **as_str)
            result2 = getattr(a_and_o, func)(
                **({"as_str": True} if func == "info" else {})
            )
            assert str(result1) == str(result2).replace("a_and_o", "x")

    def test_only_edge_cases(self):
        x = CleverDict({"Apples": "Green", "Bananas": "Yellow", "Oranges": "Purple"})
        with pytest.raises(TypeError):
            x.to_list(exclude=[], only=[])
            x.to_list(ignore=[], only=[])
            x.to_list(exclude=[], ignore=[])
            x.to_list(exclude=[], ignore=[], only=[])
        x.to_list(
            ignore=CleverDict.ignore, exclude=CleverDict.ignore, only=CleverDict.ignore
        )

        x = CleverDict({0: "Zero", 1: "One"})
        assert x.to_list(only=[1]) == [(1, "One")]
        assert x.to_list(ignore=[0]) == [(1, "One")]
        assert x.to_list(exclude=[0]) == [(1, "One")]
        assert x.to_list(only=1) == [(1, "One")]
        assert x.to_list(ignore=0) == [(1, "One")]
        assert x.to_list(exclude=0) == [(1, "One")]

    def test_permissive(self):
        """
        only= exclude= ignore= should accept iterables AND single items strings.
        """
        x = CleverDict({"Apples": "Green", "Bananas": "Yellow", "Oranges": "Purple"})
        assert x.__repr__(only="Apples") == x.__repr__(only=["Apples"])
        assert x.__repr__(ignore="Apples") == x.__repr__(ignore=["Apples"])
        assert x.to_json(ignore="Apples") == x.to_json(ignore=["Apples"])
        assert x.to_json(exclude="Apples") == x.to_json(exclude=["Apples"])
        assert x.to_dict(exclude="Apples") == x.to_dict(exclude=["Apples"])
        assert x.to_dict(ignore="Apples") == x.to_dict(ignore=["Apples"])
        assert x.to_list(only="Apples") == x.to_list(only=["Apples"])
        assert x.to_list(ignore="Apples") == x.to_list(ignore=["Apples"])
        assert x.to_lines(only="Apples") == x.to_lines(only=["Apples"])
        assert x.to_lines(ignore="Apples") == x.to_lines(ignore=["Apples"])
        assert x.info(exclude="Apples", as_str=True) == x.info(
            exclude=["Apples"], as_str=True
        )
        assert x.info(ignore="Apples", as_str=True) == x.info(
            ignore=["Apples"], as_str=True
        )

    def test_fullcopy_plus_filter(self):
        """ fullcopy= can be used with other arguments only= ignore= or exclude=.  Error must be handled gracefully."""
        x = CleverDict({"Apples": "Green", "Bananas": "Yellow", "Oranges": "Purple"})
        assert "Apples" not in x.to_json(fullcopy=True, ignore="Apples")
        assert "Apples" not in x.to_json(fullcopy=True, exclude="Apples")
        assert "Oranges" not in x.to_json(fullcopy=True, only="Apples")
        assert "Bananas" not in x.to_json(fullcopy=True, only="Apples")

    def test_only_OR_ignore_OR_exclude_as_args(self):
        """Only one of only=, ignore=, or exclude= can be given as an argument
        for supported functions.  Error must be handled gracefully."""
        x = CleverDict({"Yes": "include me", "No": "exclude/ignore me"})
        for (
            func
        ) in "__repr__() to_json() to_dict() to_list() to_lines() info(as_str=True)".split():
            perms = list(permutations(["only=", "ignore=", "exclude="]))
            perms += list(permutations(["only=", "ignore=", "exclude="], 2))
            perms = ["".join(list(x)).replace("=", "=['Yes'],") for x in perms]
            for args in perms:
                with pytest.raises(TypeError):
                    eval("x." + func.replace("(", "(" + args))

    def test_filters_with_init(self):
        """
        only= exclude= ignore= should work as part of object instantiation.
        """
        # dict
        x = CleverDict(
            {"Apples": "Green", "Bananas": "Yellow", "Oranges": "Purple"}, only="Apples"
        )
        assert list(x.keys()) == ["Apples"]
        x = CleverDict(
            {"Apples": "Green", "Bananas": "Yellow", "Oranges": "Purple"},
            only=["Apples", "Bananas"],
        )
        assert list(x.keys()) == ["Apples", "Bananas"]

        x = CleverDict(
            {"Apples": "Green", "Bananas": "Yellow", "Oranges": "Purple"},
            ignore="Apples",
        )
        assert list(x.keys()) == ["Bananas", "Oranges"]
        x = CleverDict(
            {"Apples": "Green", "Bananas": "Yellow", "Oranges": "Purple"},
            exclude=["Apples", "Bananas"],
        )
        assert list(x.keys()) == ["Oranges"]

        # CleverDict
        x = CleverDict({"Apples": "Green", "Bananas": "Yellow", "Oranges": "Purple"})
        y = CleverDict(x, only="Apples")
        assert list(y.keys()) == ["Apples"]
        y = CleverDict(x, exclude="Apples")
        assert list(y.keys()) == ["Bananas", "Oranges"]

        # list of tuples/lists
        x = CleverDict(
            [("value1", "one"), ["value2", "two"], ("value3", "three")],
            ignore=["value1", "value2"],
        )
        assert list(x.keys()) == ["value3"]
        x = CleverDict(
            [("value1", "one"), ["value2", "two"], ("value3", "three")], only=["value1"]
        )
        assert list(x.keys()) == ["value1"]

        # fromkeys
        x = CleverDict.fromkeys(["Abigail", "Tino", "Isaac"], "Year 9", only="Abigail")
        assert list(x.keys()) == ["Abigail"]
        x = CleverDict.fromkeys(
            ["Abigail", "Tino", "Isaac"], "Year 9", exclude="Abigail"
        )
        assert list(x.keys()) == ["Tino", "Isaac"]

        # from_json
        json_data = '{"None": null, "data": "123xyz"}'
        x = CleverDict.from_json(json_data, exclude="data")
        assert list(x.keys()) == ["None"]
        json_data = '{"None": null, "data": "123xyz"}'
        x = CleverDict.from_json(json_data, only="data")
        assert list(x.keys()) == ["data"]

        # from_lines
        lines = "Green\nYellow\nPurple"
        x = CleverDict.from_lines(lines, exclude="Yellow")
        assert list(x.values()) == ["Green", "Purple"]
        x = CleverDict.from_lines(lines, only="Purple")
        assert list(x.values()) == ["Purple"]

        # Refactor bool block into be_permissive

    def test_too_many_filters_with_init(self):
        """
        __init__ can only take one of only= exclude= ignore=.
        Otherwise should fail gracefully.
        """
        perms = list(permutations(["only=[1],", "ignore=[2],", "exclude=[3],"]))
        perms += list(permutations(["only=[1],", "ignore=[2],", "exclude=[3],"], 2))
        perms = ["".join(list(x)) for x in perms]
        for args in perms:
            with pytest.raises(TypeError):
                eval(f"CleverDict({{1:1, 2:2, 3:3}}, {args})")

    def test_to_lines(self, tmpdir):
        d = CleverDict()
        d[1] = "een"
        d[2] = "twee"
        d[3] = "drie"
        d[4] = "vier"
        d[5] = "vijf"
        d[6] = "zes"
        d[7] = "zeven"
        d.add_alias(1, "one")
        d.add_alias(2, "two")
        d.add_alias(3, "three")
        d.add_alias(4, "four")
        d.add_alias(5, "five")
        d.add_alias(6, "six")
        d.add_alias(7, "7")
        # default start_from_key == first alias
        assert d.to_lines() == "een\ntwee\ndrie\nvier\nvijf\nzes\nzeven"
        assert d.to_lines(start_from_key=4) == "vier\nvijf\nzes\nzeven"
        assert d.to_lines(start_from_key="7") == "zeven"
        d_nul = CleverDict({0: "nul"})
        d_nul.update(d)
        d_nul.add_alias(0, "zero")
        assert d_nul.to_lines() == "nul\neen\ntwee\ndrie\nvier\nvijf\nzes\nzeven"
        with pytest.raises(KeyError):
            assert d.to_lines(start_from_key=999)
        file_path = Path(tmpdir) / "tmp.txt"
        d.to_lines(file_path=file_path)
        with open(file_path, "r") as f:
            assert f.read() == d.to_lines()
        os.remove(file_path)

    def test_to_json(self, tmpdir):
        d = CleverDict()
        d["zero"] = "nul"
        d["one"] = "een"
        d["two"] = "twee"
        d["three"] = "drie"
        d["four"] = "vier"
        d["five"] = "vijf"
        d["six"] = "zes"
        d[7] = "zeven"
        result = CleverDict(d)
        del result[7]
        result["7"] = "zeven"
        assert CleverDict.from_json(d.to_json()) == result
        assert CleverDict.from_json(d.to_json(ignore=["one"])) == eval(
            result.__repr__(ignore=["one"])
        )
        assert CleverDict.from_json(d.to_json(ignore=["one", "two"])) == eval(
            result.__repr__(ignore=["one", "two"])
        )
        assert CleverDict.from_json(d.to_json(ignore=["one", 7])) == eval(
            result.__repr__(ignore=["one", "7"])
        )

    def test_from_lines(self, tmpdir):
        d0 = CleverDict()
        d0[0] = "alpha"
        d0[1] = "beta"
        d0[2] = "gamma"
        d0[3] = "delta"
        d0[4] = "epsilon"
        lines = d0.to_lines(start_from_key=0)
        assert d0 == CleverDict.from_lines(lines, start_from_key=0)
        # Values should remain intact with different start_from_key
        assert list(d0.to_dict().values()) == list(
            CleverDict.from_lines(lines, start_from_key=1).to_dict().values()
        )
        assert d0.keys() != CleverDict.from_lines(lines, start_from_key=1).keys()

        file_path = Path(tmpdir) / "tmp.txt"
        d0.to_lines(file_path=file_path, start_from_key=0)
        d = CleverDict.from_lines(file_path=file_path, start_from_key=0)
        assert d.to_dict() == {
            0: "alpha",
            1: "beta",
            2: "gamma",
            3: "delta",
            4: "epsilon",
        }
        d = CleverDict.from_lines(file_path=file_path, start_from_key=10)
        assert d.to_dict() == {
            10: "alpha",
            11: "beta",
            12: "gamma",
            13: "delta",
            14: "epsilon",
        }

        with pytest.raises(TypeError):
            d = CleverDict.from_lines(file_path=file_path, start_from_key="10")

        with pytest.raises(ValueError):
            CleverDict.from_lines()

        with pytest.raises(ValueError):
            CleverDict.from_lines(lines=lines, file_path=file_path)
        os.remove(file_path)

    def test_from_json(self, tmpdir):
        d = CleverDict()
        d["zero"] = "nul"
        d["one"] = "een"
        d["two"] = "twee"
        d["three"] = "drie"
        d["four"] = "vier"
        d["five"] = "vijf"
        d["six"] = "zes"
        d["7"] = "zeven"
        json_data = d.to_json()
        result = CleverDict.from_json(json_data)
        assert result == d
        file_path = Path(tmpdir) / "tmp.txt"
        d.to_json(file_path=file_path)
        result = CleverDict.from_json(file_path=file_path)
        assert d == result

        with pytest.raises(ValueError):
            CleverDict.from_json()

        with pytest.raises(ValueError):
            CleverDict.from_json(json_data=json_data, file_path=file_path)

    def test_ignore(self):
        """CleverDict.ignore lists aliases and keys which should never be
        converted to json or saved including:

        password
        save_path
        _aliases
        """
        x = CleverDict({"password": "Top Secret", "userid": "Michael Palin"})
        x.add_alias("password", "keyphrase")
        x.autosave(silent=True)
        path = x.save_path
        ignore = "password Password PASSWORD".split()
        lines = x.to_lines(ignore=ignore)
        for output in [x.to_json(ignore=ignore), repr(x.to_list(ignore=ignore)), lines]:
            assert "password" not in output
            assert "Top Secret" not in output
            assert "auto_save" not in output
            assert "_aliases" not in output
            if output != lines:
                assert "userid" in output
        x.autosave("off", silent=True)

    def test_to_and_from_json_1(self):
        """It should be possible to completely reconstruct a CleverDict
        object, excluding _vars (attributes set directly without updating
        the dictionary) after .to_json followed by .from_json"""
        d = CleverDict({"one": "een"})
        d.add_alias("one", "ONE")
        j = d.to_json(fullcopy=True)
        new_d = CleverDict.from_json(j)
        assert new_d == d

    def test_to_and_from_json_2(self):
        """Automatically created aliases should be presevered after .to_json
        followed by .from_json"""
        d = CleverDict({"#1": 1})
        j = d.to_json()
        new_d = CleverDict.from_json(j)
        assert d._1 is d["#1"]
        assert new_d._1 is new_d["#1"]
        new_d._1 += 1
        assert new_d._1 == new_d["#1"]

    def test_to_and_from_json_3(self):
        def example_user_code(clever_dict):
            """Typical use of CleverDict is aliases to provide interchangeable
            attributes.  In this case .number and .Number.  Quite subtle and easy
            to overlook when debugging"""
            clever_dict.number += 1
            return clever_dict.Number

        """ example_user_code should work equally well after .to_json followed
        by .from_json """
        d = CleverDict({"number": 1})
        d.add_alias("number", "Number")
        j = d.to_json(fullcopy=True)
        new_d = CleverDict.from_json(j)
        assert d.number == d.Number == new_d.number == new_d.Number
        assert example_user_code(d) == 2
        assert example_user_code(new_d) == 2

    def test_to_and_from_json_4(self):
        """
        Attributes created with setattr_direct are saved with fullcopy=True
        """
        d = CleverDict({1: 2, 3: 4, 0: 5, "string": 6})
        d.setattr_direct("extra", 42)
        j = d.to_json(fullcopy=True)
        new_d = CleverDict.from_json(j)
        assert new_d.extra == 42

    def test_to_and_from_json_5(self):
        """
        Aliases created with add_alias are saved with fullcopy=True
        """
        d = CleverDict({1: 2, 3: 4, 0: 5, "string": 6})
        d.add_alias(3, "nul")
        j = d.to_json(fullcopy=True)
        new_d = CleverDict.from_json(j)
        assert new_d.nul == 4

    def test_default_to_from_json(self):
        """Only data dictionary should be copied with .to_json() by default"""
        d = CleverDict({"1": 2, "3": 4, "0": 5, "string": 6})
        d.setattr_direct("extra", 42)
        d.add_alias("3", "nul")
        j = d.to_json()
        new_d = CleverDict.from_json(j)
        assert new_d.items() == d.items()
        with pytest.raises(AttributeError):
            new_d.nul
        with pytest.raises(KeyError):
            new_d["extra"]

    def test_get_default_settings_path(self):
        path = CleverDict.get_new_save_path()
        info = "test"
        with open(path, "w") as file:
            file.write(info)

        with open(path, "r") as file:
            assert file.read() == info
        path.unlink()
        # when called a second time, should be different:
        assert CleverDict.get_new_save_path() != path

    def test_get_app_dir(self):
        """
        tests whether the cleverdict implementation of get_app_dir is ok (can only be tested if click is installed)
        it will test only the right output on the OS the test is running on
        """
        try:
            import click
            from cleverdict import get_app_dir

            assert click.get_app_dir("x") == get_app_dir("x")
        except ModuleNotFoundError:
            pytest.skip("could not import click or cleverdict")

    def test_import_existing_cleverdict(test):
        x = CleverDict({"name": "Peter", "nationality": "British"})
        x.add_alias("name", "nom")
        x.setattr_direct("private", "parts")
        x.autosave(silent=True)
        y = CleverDict(x)
        assert y.nom == "Peter"
        assert y.private == "parts"
        assert list(y.keys()) == ["name", "nationality"]
        y = CleverDict(x, only="name")
        assert list(y.keys()) == ["name"]
        y = CleverDict(x, exclude="name")
        assert list(y.keys()) == ["nationality"]


class Test_Internal_Logic:
    def test_raises_error(self):
        """
        Attribute and Key errors should be raised as with normal objects/dicts
        """
        x = CleverDict()
        with pytest.raises(AttributeError):
            x.a
        with pytest.raises(KeyError):
            x["a"]

    def test_conversions(self):
        x = CleverDict({1: "First Entry", " ": "space", "??": "question"})
        assert x._1 == "First Entry"
        assert x["_1"] == "First Entry"
        assert x[1] == "First Entry"
        with pytest.raises(KeyError):
            x["1"] = 5
        with pytest.raises(KeyError):
            x = CleverDict({1: "First Entry", "1": "space", "??": "question"})
        x["else"] = "is else"
        assert x["else"] == "is else"
        assert x["_else"] == "is else"
        assert x._else == "is else"
        with pytest.raises(KeyError):
            x["?else"] = "other"
        x._4 = "abc"
        with pytest.raises(KeyError):
            x["4"] = "def"
        x[12345.0] = "klm"
        assert x._12345 == "klm"
        x[2.0] = "two-point-0"
        assert x._2 == "two-point-0"
        x["11a23bccà~£#@q123b/=€впВМвапрй"] = "abc"
        assert x._11a23bccà____q123b___впВМвапрй == "abc"
        assert x["11a23bccà~£#@q123b/=€впВМвапрй"] == "abc"
        assert x["_11a23bccà____q123b___впВМвапрй"] == "abc"

    def test_data_attribute(self):
        x = CleverDict()
        x["data"] = "data"
        assert x["data"] == "data"
        assert x.data == "data"

    def test_normalise_unicode(self):
        """
        Most unicode letters are valid in attribute names
        """
        x = CleverDict({"ветчина_и_яйца$a": "ham and eggs"})
        x.ве = "ve"
        x["1ве"] = "1ve"
        assert x.ветчина_и_яйца_a == "ham and eggs"
        assert x.ве == "ve"
        assert x._1ве == "1ve"

    def test_True_False_None_functionality(self):
        """
        When setting dictionary keys in Python:
        d[0] is d[0.0] is d[False]
        d[1] is d[1.0] is d[True]
        d[1234.0] is d[1234]
        If the same key is set in different ways e.g.
            d = {0: "Zero", False: "Untrue"}
        the last (rightmost) value overwrites any previous values, so
            d[0] == "Untrue"
        Furthermore, keywords like True and False can't be used as attributes.
        """
        x = CleverDict()
        x[0] = 0
        x[False] = 1
        x[1] = 2
        x[True] = 3
        x[None] = "nothing"
        assert x[0] == 1
        assert x[False] == 1
        assert x["_0"] == 1
        assert x["_False"] == 1
        assert x._0 == 1
        assert x._False == 1
        assert x[1] == 3
        assert x[True] == 3
        assert x["_1"] == 3
        assert x["_True"] == 3
        assert x._1 == 3
        assert x._True == 3
        assert x[None] == "nothing"
        assert x["_None"] == "nothing"
        with pytest.raises(KeyError):
            x["None"]

    def test_repr_and_eq(self):
        """
        Tests that the output from __repr__ can be used to reconstruct the
        CleverDict object, and __eq__ can be used to compare CleverDict objects."""
        x = CleverDict()
        x[0] = 0
        x[False] = 1
        x[1] = 2
        x[True] = 3
        x.a = 4
        x["what?"] = 5
        x.add_alias("a", "c")
        y = eval(repr(x))
        assert x == y
        y.b = 6
        assert x != y
        x = CleverDict()
        assert eval(repr(x)) == x
        with Expand(False):
            x = CleverDict({True: 1})
            assert len(x.get_aliases()) == 1
            assert CleverDict(eval(repr(x))) == x
            # check whether _expand has been properly reset
            x = CleverDict({True: 1})
            assert len(x.get_aliases()) == 1
        # empty dict with one variable
        x = CleverDict()
        x.setattr_direct("a", 1)
        assert len(x.get_aliases()) == 0
        assert eval(repr(x)) == x

    def testupdate(self):
        x = CleverDict.fromkeys((0, 1, 2, "a", "what?", "return"), 0)
        y = CleverDict({0: 2, "c": 3})
        x.update(y)
        assert x == CleverDict(
            {0: 2, 1: 0, 2: 0, "a": 0, "what?": 0, "return": 0, "c": 3}
        )

    def test_del(self):
        """ __delattr__ should delete dict items regardless of alias """
        x = CleverDict()
        x[1] = 1
        del x[1]
        with pytest.raises(KeyError):
            x[1]
        x[1] = 1
        del x["_1"]
        with pytest.raises(KeyError):
            x[1]
        x[1] = 1
        del x._1
        with pytest.raises(KeyError):
            x[1]
        with pytest.raises(KeyError):
            del x[1]
        with pytest.raises(AttributeError):
            del x._1

    def test_del_with_setattr_direct(self):
        """ __delattr__ should delete attributes created with setattr_direct"""
        x = CleverDict()
        x.setattr_direct("direct_variable", "direct_value")
        assert hasattr(x, "direct_variable")
        del x.direct_variable
        assert not hasattr(x, "direct_variable")

    def testget_key(self):
        x = CleverDict.fromkeys(("a", 0, 1, "what?"), 1)
        x.add_alias(0, "zero")
        for key in x.keys():
            for name in x.get_aliases(key):
                assert x.get_key(name) == key
        assert x.get_key(True) == 1
        assert x.get_key("_True") == 1
        assert x.get_key("zero") == 0

    def test_Expand(self):
        with Expand(False):
            x = CleverDict.fromkeys(("a", 0, 1, "what?"), 1)
            x.add_alias(0, 2)
        assert x.get_aliases("a") == ["a"]
        assert x.get_aliases(0) == [0, 2]
        assert x.get_aliases(1) == [1]

        x = CleverDict.fromkeys(("a", 0, 1, "what?"), 1)
        x.add_alias(0, 2)
        assert x.get_aliases("a") == ["a"]
        assert x.get_aliases(0) == [0, "_0", "_False", 2, "_2"]
        assert x.get_aliases(1) == [1, "_1", "_True"]

        with Expand(True):
            x = CleverDict.fromkeys(("a", 0, 1, "what?"), 1)
            x.add_alias(0, 2)
        assert x.get_aliases("a") == ["a"]
        assert x.get_aliases(0) == [0, "_0", "_False", 2, "_2"]
        assert x.get_aliases(1) == [1, "_1", "_True"]

        CleverDict.expand = False
        x = CleverDict({1: 1})
        with pytest.raises(AttributeError):
            x._1
        CleverDict.expand = True
        x = CleverDict({1: 1})
        x._1

    def test_expand_context_manager(self):
        with Expand(False):
            assert not CleverDict.expand
        assert CleverDict.expand
        with Expand(True):
            assert CleverDict.expand
        assert CleverDict.expand

        CleverDict.expand = False
        with Expand(False):
            assert not CleverDict.expand

        assert not CleverDict.expand
        with Expand(True):
            assert CleverDict.expand
        assert not CleverDict.expand

        CleverDict.expand = True

    def test_all_aliases(self):
        assert all_aliases("a") == ["a"]
        assert all_aliases(True) == [True, "_1", "_True"]
        assert all_aliases("3test test") == ["3test test", "_3test_test"]
        with Expand(False):
            assert all_aliases("a") == ["a"]
            assert all_aliases(True) == [True]
            assert all_aliases("3test test") == ["3test test"]

    def test_setattr_direct(self):
        """
        Sets an attribute directly, i.e. without making it into an item.
        Attributes set via setattr_direct will
        expressly not appear in the result of repr().  They will appear in the result of str() however.
        """
        x = CleverDict()
        x.setattr_direct("a", "A")
        assert x.a == "A"
        with pytest.raises(KeyError):
            x["a"]
            x.get_key("a")
        assert x.get_aliases() == []


class Test_Save_Functionality:
    def test_save_on_creation1(self):
        """ Once set, CleverDict.save should be called on creation """
        delete_log()
        CleverDict.save = example_save_function
        x = CleverDict({"total": 6, "usergroup": "Knights of Ni"})
        assert x.save.__name__ == "example_save_function"
        log = get_data("example.log")
        assert (
            log
            == """Notional save to database: .total = 6 <class 'int'>\nNotional save to database: .usergroup = Knights of Ni <class 'str'>\n"""
        )
        assert delete_log()
        CleverDict.save = CleverDict.original_save
        assert x.save.__name__ == "save"
        assert not delete_log()

    def test_save_on_creation2(self):
        """ Overwrites (inactive) original save method using __init__ """
        delete_log()
        x = CleverDict(
            {"total": 6, "usergroup": "Knights of Ni"}, save=example_save_function
        )
        assert x.save.__name__ == "example_save_function"
        log = get_data("example.log")
        assert (
            log
            == """Notional save to database: .total = 6 <class 'int'>\nNotional save to database: .usergroup = Knights of Ni <class 'str'>\n"""
        )
        assert delete_log()
        x.set_autosave()
        assert not delete_log()
        assert x.save.__name__ == "save"

    def test_save_on_creation3(self):
        delete_log()
        x = CleverDict()
        with pytest.raises(TypeError):
            x.set_autosave(invalid_save_function)
        assert not delete_log()
        with pytest.raises(TypeError):
            x.set_autodelete(invalid_save_function)
        assert not delete_log()

    def test_save_on_creation4(self):
        delete_log()
        x = CleverDict()
        x.set_autosave(example_save_function)
        assert x.save.__name__ == "example_save_function"
        x["total"] = 6
        x["usergroup"] = "Knights of Ni"
        log = get_data("example.log")
        assert (
            log
            == """Notional save to database: .total = 6 <class 'int'>\nNotional save to database: .usergroup = Knights of Ni <class 'str'>\n"""
        )
        assert delete_log()
        x.set_autosave()
        assert x.save.__name__ == "save"

    def test_save_on_update(self):
        """ Once set, CleverDict.save should be called after updates """
        x = CleverDict({"total": 6, "usergroup": "Knights of Ni"})
        delete_log()
        CleverDict.save = example_save_function
        x.total += 1
        log = get_data("example.log")
        assert log == "Notional save to database: .total = 7 <class 'int'>\n"
        assert delete_log()
        CleverDict.save = CleverDict.original_save

    def test_subclass_to_store_class(self):
        class SaveDict(CleverDict):
            def __init__(self, *args, **kwargs):
                self.setattr_direct("store", [])
                super().__init__(*args, **kwargs)

            def save(self, name, value):
                if name not in ("_aliases", "store"):
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
        except KeyError:
            pass
        x._4 = 9
        x["_4"] = 10
        try:
            x["4"] = 11
        except KeyError:
            pass

        assert x.store == [
            ("a", 1),
            (2, 2),
            ("b", 3),
            ("c", 4),
            (3, 5),
            (3, 6),
            (3, 7),
            (3, 8),
            ("_4", 9),
            ("_4", 10),
        ]


class Test_Delete_Functionality:
    def test_delete_on_creation1(self):
        """ Once set, CleverDict.save should be called on creation """
        delete_log()
        CleverDict.delete = example_delete_function
        x = CleverDict({"total": 6, "usergroup": "Knights of Ni"})
        assert x.delete.__name__ == "example_delete_function"
        del x["usergroup"]
        log = get_data("example.log")
        assert log == "Notional DELETE to database: .usergroup\n"
        CleverDict.delete = CleverDict.original_delete
        assert x.delete.__name__ == "delete"
        assert delete_log()

    def test_delete_on_creation2(self):
        """ Overwrites (inactive) original delete method using __init__ """
        delete_log()
        x = CleverDict(
            {"total": 6, "usergroup": "Knights of Ni"}, delete=example_delete_function
        )
        assert x.delete.__name__ == "example_delete_function"
        del x.total
        log = get_data("example.log")
        assert log == "Notional DELETE to database: .total\n"
        assert delete_log()
        assert x.delete.__name__ == "example_delete_function"
        x.set_autodelete()
        assert not delete_log()
        assert x.delete.__name__ == "delete"


class Test_README_examples:
    def test_BASIC_USE_1(self):
        x = CleverDict({"total": 6, "usergroup": "Knights of Ni"})
        assert x.total == x["total"] == 6
        assert x.usergroup == x["usergroup"] == "Knights of Ni"

    def test_BASIC_USE_2(self):
        x = CleverDict()
        x["life"] = 42
        x.life += 1
        assert x["life"] == 43
        del x["life"]
        with pytest.raises(AttributeError):
            x.life

    def test_BASIC_USE_3(self):
        assert "to_list" in dir(CleverDict)
        x = CleverDict({"to_list": "Some information"})
        assert x["to_list"] == "Some information"
        assert str(type(x.to_list)) == "<class 'method'>"

    def test_BASIC_USE_4(self):
        x = CleverDict({"to_list": "Some information"})
        assert x.to_json() == '{\n    "to_list": "Some information"\n}'
        x.to_json(file_path="mydata.json")
        assert Path("mydata.json").is_file()
        with open("mydata.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        assert x == CleverDict(data)
        os.remove("mydata.json")

    def test_BASIC_USE_5(self):
        x = CleverDict({1: "one", 2: "two"})
        assert x.to_list() == [(1, "one"), (2, "two")]

    def test_IMPORT_EXPORT_1(self):
        x = CleverDict(created="today", review="tomorrow")
        assert x.created == "today"
        assert x["review"] == "tomorrow"

    def test_IMPORT_EXPORT_2(self):
        x = CleverDict([("value1", "one"), ["value2", "two"], ("value3", "three")])
        assert x.value1 == "one"
        assert x["value2"] == "two"
        assert getattr(x, "value3") == "three"

    def test_IMPORT_EXPORT_3(self):
        x = CleverDict.fromkeys(["Abigail", "Tino", "Isaac"], "Year 9")
        assert (
            repr(x)
            == "CleverDict({'Abigail': 'Year 9', 'Tino': 'Year 9', 'Isaac': 'Year 9'}, _aliases={}, _vars={})"
        )

    def test_IMPORT_EXPORT_4(self):
        x = CleverDict({1: "one", 2: "two"})
        y = CleverDict(x)
        assert (
            repr(y)
            == "CleverDict({1: 'one', 2: 'two'}, _aliases={'_1': 1, '_True': 1, '_2': 2}, _vars={})"
        )
        assert list(y.items()) == [(1, "one"), (2, "two")]

    def test_IMPORT_EXPORT_5(self):
        class X:
            pass

        a = X()
        a.name = "Percival"
        x = CleverDict(vars(a))
        assert repr(x) == "CleverDict({'name': 'Percival'}, _aliases={}, _vars={})"
        assert x.to_dict() == {"name": "Percival"}

    def test_IMPORT_EXPORT_7(self):
        json_data = '{"None": null}'
        x = CleverDict.from_json(json_data)
        assert (
            repr(x)
            == "CleverDict({'None': None}, _aliases={'_None': 'None'}, _vars={})"
        )
        x.to_json(file_path="mydata.json")
        y = CleverDict.from_json(file_path="mydata.json")
        os.remove("mydata.json")
        assert x == y

    def test_IMPORT_EXPORT_8(self):
        lines = "This is my first line\nMy second...\n\n\n\n\nMy LAST\n"
        x = CleverDict.from_lines(lines, start_from_key=1)
        assert (
            x.info(as_str=True)
            == "CleverDict:\n    x[1] == x['_1'] == x['_True'] == x._1 == x._True == 'This is my first line'\n    x[2] == x['_2'] == x._2 == 'My second...'\n    x[3] == x['_3'] == x._3 == ''\n    x[4] == x['_4'] == x._4 == ''\n    x[5] == x['_5'] == x._5 == ''\n    x[6] == x['_6'] == x._6 == ''\n    x[7] == x['_7'] == x._7 == 'My LAST'\n    x[8] == x['_8'] == x._8 == ''"
        )
        assert x.to_lines(start_from_key=7) == "My LAST\n"
        x.to_lines(file_path="lines.txt", start_from_key=1)
        with open("lines.txt", "r") as file:
            data = file.read()
        assert data == "This is my first line\nMy second...\n\n\n\n\nMy LAST\n"
        os.remove("lines.txt")

    def test_IMPORT_EXPORT_9(self):
        lines = "This is my first line\nMy second...\n\n\n\n\nMy LAST\n"
        x = CleverDict.from_lines(lines)  # start_from_key=1 by default
        x.password = "Top Secret - don't ever save to file!"
        assert (
            x.to_lines(start_from_key=7)
            == "My LAST\n\nTop Secret - don't ever save to file!"
        )
        assert x.to_lines(start_from_key=7, ignore=["password"]) == "My LAST\n"

    def test_IMPORT_EXPORT_10(self):
        lines = "This is my first line\nMy second...\n\n\n\n\nMy LAST\n"
        x = CleverDict.from_lines(lines)  # start_from_key=1 by default
        x.add_alias(7, "The End")
        new_lines = x.to_lines(start_from_key="The End")
        x.footnote1 = "Source: Wikipedia"
        x.update({9: "All references to living persons are accidental"})
        new_lines = x.to_lines(start_from_key="footnote1")
        assert (
            new_lines
            == "Source: Wikipedia\nAll references to living persons are accidental"
        )

    def test_NAMES_AND_ALIASES_1(self):
        x = CleverDict({7: "Seven"})
        assert x._7 == "Seven"
        assert repr(x) == "CleverDict({7: 'Seven'}, _aliases={'_7': 7}, _vars={})"
        x.add_alias(7, "NumberSeven")
        assert x._aliases == {7: 7, "_7": 7, "NumberSeven": 7}
        x.add_alias(7, "zeven")
        assert (
            repr(x)
            == "CleverDict({7: 'Seven'}, _aliases={'_7': 7, 'NumberSeven': 7, 'zeven': 7}, _vars={})"
        )
        assert x.get_aliases() == [7, "_7", "NumberSeven", "zeven"]
        assert x.info("as_str", ignore=[7]) == "CleverDict:"
        assert x.to_dict(ignore=["zeven"]) == {}
        assert x.to_list(ignore=["zeven"]) == []
        x.delete_alias(["_7", "NumberSeven"])
        assert repr(x) == "CleverDict({7: 'Seven'}, _aliases={'zeven': 7}, _vars={})"
        with pytest.raises(AttributeError):
            assert x._7
        with pytest.raises(KeyError):
            x.delete_alias([7])
        del x[7]
        assert repr(x) == "CleverDict({}, _aliases={}, _vars={})"

    def test_ATTRIBUTE_NAMES_1(self):
        x = CleverDict(значение="znacheniyeh: Russian word for 'value'")
        assert x.значение == "znacheniyeh: Russian word for 'value'"

    def test_ATTRIBUTE_NAMES_2(self):
        with pytest.raises(KeyError):
            x = CleverDict({"one-two": "hypen", "one/two": "forward slash"})
        assert CleverDict({"one-two": "hypen", "one_or_two": "forward slash"})

    def test_ATTRIBUTE_NAMES_3(self):
        x = {1: "one", True: "the truth"}
        assert repr(x) == "{1: 'the truth'}"

    def test_ATTRIBUTE_NAMES_4(self):
        x = y = z = CleverDict({1: "one", True: "the truth"})
        assert (
            x.info("as_str")
            == "CleverDict:\n    x is y is z\n    x[1] == x['_1'] == x['_True'] == x._1 == x._True == 'the truth'"
        )

    def test_SETTING_ATTRIBUTES_DIRECTLY_1(self):
        x = CleverDict()
        x.setattr_direct("direct", True)
        assert x._vars == {"direct": True}
        assert repr(x) == "CleverDict({}, _aliases={}, _vars={'direct': True})"
        x.to_json(file_path="mydata.json", fullcopy=True)
        y = CleverDict.from_json(file_path="mydata.json")
        assert y == x
        os.remove("mydata.json")
        j = x.to_json(fullcopy=True)
        assert (
            j
            == '{\n    "_mapping_encoded": {},\n    "_aliases": {},\n    "_vars": {\n        "direct": true\n    }\n}'
        )
        y = CleverDict.from_json(j)
        assert y == x

    def test_AUTOSAVE_1(self):
        """ Default option: data dictionary saved only """
        x = CleverDict({"Patient Name": "Wobbly Joe", "Test Result": "Positive"})
        assert not hasattr(x, "save_path")
        assert x.save.__name__ == "save"
        x.autosave(silent=True)
        assert x.save.__name__ == "_auto_save_data"
        assert x.delete.__name__ == "_auto_save_data"
        assert hasattr(x, "save_path")
        x.Prognosis = "Not good"
        assert '"Prognosis": "Not good"' in get_data(x.save_path)

    def test_AUTOSAVE_2(self):
        """ Changing from default to fullcopy changes save_path"""
        x = CleverDict({"Patient Name": "Wobbly Joe", "Test Result": "Positive"})
        x.autosave(silent=True)
        path = x.save_path
        x.autosave(silent=True, fullcopy=True)
        assert path != x.save_path  # New file with new autosave instruction
        path = x.save_path
        assert x.save.__name__ == "_auto_save_fullcopy"
        assert x.delete.__name__ == "_auto_save_fullcopy"

    def test_AUTOSAVE_3(self):
        """ .add_alias triggers autosave """
        x = CleverDict({"Patient Name": "Wobbly Joe", "Test Result": "Positive"})
        x.autosave(silent=True)
        x.add_alias("Patient Name", "name")
        assert '"name": "Patient Name"' not in get_data(x.save_path)
        x.delete_alias("name")
        x.autosave(silent=True, fullcopy=True)
        x.add_alias("Patient Name", "name")
        assert '"name": "Patient Name"' in get_data(x.save_path)

    def test_AUTOSAVE_4(self):
        """ .setattr_direct and del DON'T trigger autosave (default) """
        x = CleverDict({"Patient Name": "Wobbly Joe", "Test Result": "Positive"})
        x.autosave(silent=True)
        x.setattr_direct("internal_code", "xyz123")
        assert '"internal_code": "xyz123"' not in get_data(x.save_path)
        del x.internal_code
        assert '"internal_code": "xyz123"' not in get_data(x.save_path)

    def test_AUTOSAVE_5(self):
        """ .setattr_direct and del DO trigger autosave (fullcopy)"""
        x = CleverDict({"Patient Name": "Wobbly Joe", "Test Result": "Positive"})
        x.autosave(silent=True, fullcopy=True)
        x.setattr_direct("internal_code", "xyz123")
        assert '"internal_code": "xyz123"' in get_data(x.save_path)
        del x.internal_code
        assert '"internal_code": "xyz123"' not in get_data(x.save_path)

    def test_AUTOSAVE_6(self):
        """ 'off' reverts to inactive default save behaviour """
        x = CleverDict({"Patient Name": "Wobbly Joe", "Test Result": "Positive"})
        x.autosave(silent=True)
        assert x.save.__name__ == "_auto_save_data"
        assert x.delete.__name__ == "_auto_save_data"
        assert hasattr(x, "save_path")
        assert x.save_path.is_file()
        os.remove(x.save_path)
        x.autosave("off", silent=True)
        assert x.save.__name__ == "save"
        assert x.delete.__name__ == "delete"
        assert not hasattr(x, "save_path")
        x.autosave(silent=True, fullcopy=True)
        assert x.save.__name__ == "_auto_save_fullcopy"
        assert x.delete.__name__ == "_auto_save_fullcopy"
        assert hasattr(x, "save_path")
        assert x.save_path.is_file()
        os.remove(x.save_path)
        x.autosave("off", silent=True)
        assert x.save.__name__ == "save"
        assert x.delete.__name__ == "delete"

    def test_AUTOSAVE_7(self):
        """
        There might be a complicated problem when autosaving an inherited CleverDict e.g. via to_json/from_json.

        The super() might refer to CleverDict and might cause issues?

        Inheriting from another CleverDict should NOT inherit the autosave/save
        settings.
        """
        x = CleverDict({"total": 6, "usergroup": "Knights of Ni"})
        x.add_alias("usergroup", "knights")
        x.setattr_direct("Quest", "The Holy Grail")
        x.to_json(file_path="mydata.json", fullcopy=True)
        y = CleverDict.from_json(file_path="mydata.json")
        os.remove("mydata.json")
        assert y.save.__name__ == "save"
        y.autosave(fullcopy=True, silent=True)
        assert y.save.__name__ == "_auto_save_fullcopy"
        assert "knights" in y._aliases
        assert '"knights": "usergroup"' in get_data(y.save_path)
        y.delete_alias("knights")
        assert "knights" not in y._aliases
        assert '"knights": "usergroup"' not in get_data(y.save_path)
        assert y.Quest == "The Holy Grail"
        y.Quest = "Never completed"
        assert y.Quest == "Never completed"

    def test_AUTOSAVE_8(self):
        """
        There might be a complicated problem when autosaving an inherited CleverDict e.g. y= CleverDict(x) where x is a CleverDict.

        The super() might refer to CleverDict and might cause issues?

        Inheriting from another CleverDict should NOT inherit the autosave/save
        settings.
        """
        x = CleverDict({"total": 6, "usergroup": "Knights of Ni"})
        x.add_alias("usergroup", "knights")
        x.setattr_direct("Quest", "The Holy Grail")
        y = CleverDict(x)
        assert y.save.__name__ == "save"
        y.autosave(fullcopy=True, silent=True)
        assert y.save.__name__ == "_auto_save_fullcopy"
        assert "knights" in y._aliases
        assert '"knights": "usergroup"' in get_data(y.save_path)
        y.delete_alias("knights")
        assert "knights" not in y._aliases
        assert '"knights": "usergroup"' not in get_data(y.save_path)
        assert y.Quest == "The Holy Grail"
        y.Quest = "Never completed"
        assert y.Quest == "Never completed"

    def test_SETATTR_UPDATES(self):
        """Once created with setattr_direct, items in vars should update
        in the normal way"""
        x = CleverDict({"total": 6, "usergroup": "Knights of Ni"})
        x.setattr_direct("Quest", "The Holy Grail")
        x.Quest = "Complete!"
        assert x.Quest == "Complete!"
        x.Quest += "\nHurrah!"
        assert x.Quest == "Complete!\nHurrah!"

    def test_YOUR_OWN_AUTOSAVE_1(self):
        def your_save_function(self, name, value):
            """ Custom save function by you """
            print(
                f" ⓘ  .{name} (object type: {self.__class__.__name__}) = {value} {type(value)}"
            )

        CleverDict.save = your_save_function
        x = CleverDict()  # Ruud output should be checked in the test!
        assert x.save.__doc__ == " Custom save function by you "
        CleverDict.save = CleverDict.original_save

    def test_YOUR_OWN_AUTOSAVE_2(self):
        class Type1(CleverDict):
            def __init__(self, *args, **kwargs):
                self.setattr_direct("index", [])
                super().__init__(*args, **kwargs)

            def save(self, name, value):
                if name not in ("_aliases", "index"):
                    self.index.append((name, value))

        x = Type1(data="Useless information")
        assert x.index == [("data", "Useless information")]

    def test_SUBCLASSING_1(self):
        class Movie(CleverDict):
            index = []

            def __init__(self, title, **kwargs):
                super().__init__(**kwargs)
                self.title = title
                Movie.index += [self]

        x = Movie("The Wizard of Oz")
        assert (
            repr(Movie.index)
            == "[Movie({'title': 'The Wizard of Oz'}, _aliases={}, _vars={})]"
        )
        assert (
            x.info(as_str=True)
            == "Movie:\n    x['title'] == x.title == 'The Wizard of Oz'"
        )


class Test_at_property:
    class User:
        def __init__(self):
            self.username = "testname"
            self.account = "testaccount"

        @property
        def password(self):
            return keyring.get_password(self.account, self.username)

        @password.setter
        def password(self, value):
            keyring.set_password(self.account, self.username, value)

        @password.deleter
        def password(self):
            keyring.delete_password(self.account, self.username)

    user = User()
    user.password = "testpw"
    assert user.password == "testpw"
    assert keyring.get_password("testaccount", "testname") == "testpw"
    del user.password
    assert not user.password
    assert not keyring.get_password("testaccount", "testname") == "testpw"


if __name__ == "__main__":
    pytest.main(["-vv", "-s"])
