# jsonParser.py
#
# Implementation of a simple JSON parser, returning a hierarchical
# ParseResults object support both list- and dict-style data access.
#
# Copyright 2006, by Paul McGuire
#
# Updated 8 Jan 2007 - fixed dict grouping bug, and made elements and
#   members optional in array and object collections
#
# Updated 9 Aug 2016 - use more current pyparsing constructs/idioms
#
json_bnf = """
object
    { members }
    {}
members
    string : value
    members , string : value
array
    [ elements ]
    []
elements
    value
    elements , value
value
    string
    number
    object
    array
    true
    false
    null
"""

import pyparsing as pp
from pyparsing import pyparsing_common as ppc


def make_keyword(kwd_str, kwd_value):
    return pp.Keyword(kwd_str).set_parse_action(pp.replace_with(kwd_value))


# set to False to return ParseResults
# NOTE: When RETURN_PYTHON_COLLECTIONS = False, jsonObject and jsonArray return
# ParseResults objects instead of native Python dict/list. This has an important
# behavioral difference for empty collections:
#   - Empty object {}  → empty ParseResults: len() == 0, bool() == False
#   - Empty array []   → empty ParseResults: len() == 0, bool() == False
# Since bool(empty_ParseResults) is False, code like "if result.EmptyField:"
# may incorrectly treat an explicitly present-but-empty field as missing.
# When RETURN_PYTHON_COLLECTIONS = True, empty dict/list are returned as native
# Python {}, [] which also have bool() == False, but in that case the field
# is accessible as a key in the dict — the falsiness is expected Python behavior.
RETURN_PYTHON_COLLECTIONS = True

TRUE = make_keyword("true", True)
FALSE = make_keyword("false", False)
NULL = make_keyword("null", None)

LBRACK, RBRACK, LBRACE, RBRACE, COLON = map(pp.Suppress, "[]{}:")

jsonString = pp.dbl_quoted_string().set_parse_action(pp.remove_quotes)
jsonNumber = ppc.number().set_name("jsonNumber")

jsonObject = pp.Forward().set_name("jsonObject")
jsonValue = pp.Forward().set_name("jsonValue")

jsonElements = pp.DelimitedList(jsonValue).set_name(None)
# jsonArray = pp.Group(LBRACK + pp.Optional(jsonElements, []) + RBRACK)
# jsonValue << (
#     jsonString | jsonNumber | pp.Group(jsonObject) | jsonArray | TRUE | FALSE | NULL
# )
# memberDef = pp.Group(jsonString + COLON + jsonValue).set_name("jsonMember")

jsonArray = pp.Group(
    LBRACK + pp.Optional(jsonElements) + RBRACK, aslist=RETURN_PYTHON_COLLECTIONS
).set_name("jsonArray")

jsonValue << (jsonString | jsonNumber | jsonObject | jsonArray | TRUE | FALSE | NULL)

memberDef = pp.Group(
    jsonString + COLON + jsonValue, aslist=RETURN_PYTHON_COLLECTIONS
).set_name("jsonMember")

jsonMembers = pp.DelimitedList(memberDef).set_name(None)
# jsonObject << pp.Dict(LBRACE + pp.Optional(jsonMembers) + RBRACE)
jsonObject << pp.Dict(
    LBRACE + pp.Optional(jsonMembers) + RBRACE, asdict=RETURN_PYTHON_COLLECTIONS
)

jsonComment = pp.cpp_style_comment
jsonObject.ignore(jsonComment)


if __name__ == "__main__":
    testdata = """
    {
        "glossary": {
            "title": "example glossary",
            "GlossDiv": {
                "title": "S",
                "GlossList": [
                    {
                    "ID": "SGML",
                    "SortAs": "SGML",
                    "GlossTerm": "Standard Generalized Markup Language",
                    "TrueValue": true,
                    "FalseValue": false,
                    "Gravity": -9.8,
                    "LargestPrimeLessThan100": 97,
                    "AvogadroNumber": 6.02E23,
                    "EvenPrimesGreaterThan2": null,
                    "PrimesLessThan10" : [2,3,5,7],
                    "Acronym": "SGML",
                    "Abbrev": "ISO 8879:1986",
                    "GlossDef": "A meta-markup language, used to create markup languages such as DocBook.",
                    "GlossSeeAlso": ["GML", "XML", "markup"],
                    "EmptyDict" : {},
                    "EmptyList" : []
                    }
                ]
            }
        }
    }
    """

    results = jsonObject.parse_string(testdata)

    results.pprint()
    if RETURN_PYTHON_COLLECTIONS:
        from pprint import pprint

        pprint(results)
    else:
        results.pprint()
    print()

    def testPrint(x):
        print(type(x), repr(x))

    if RETURN_PYTHON_COLLECTIONS:
        results = results[0]
        print(list(results["glossary"]["GlossDiv"]["GlossList"][0].keys()))
        testPrint(results["glossary"]["title"])
        testPrint(results["glossary"]["GlossDiv"]["GlossList"][0]["ID"])
        testPrint(results["glossary"]["GlossDiv"]["GlossList"][0]["FalseValue"])
        testPrint(results["glossary"]["GlossDiv"]["GlossList"][0]["Acronym"])
        testPrint(
            results["glossary"]["GlossDiv"]["GlossList"][0]["EvenPrimesGreaterThan2"]
        )
        testPrint(results["glossary"]["GlossDiv"]["GlossList"][0]["PrimesLessThan10"])
    else:
        print(list(results.glossary.GlossDiv.GlossList.keys()))
        testPrint(results.glossary.title)
        testPrint(results.glossary.GlossDiv.GlossList.ID)
        testPrint(results.glossary.GlossDiv.GlossList.FalseValue)
        testPrint(results.glossary.GlossDiv.GlossList.Acronym)
        testPrint(results.glossary.GlossDiv.GlossList.EvenPrimesGreaterThan2)
        testPrint(results.glossary.GlossDiv.GlossList.PrimesLessThan10)

        # Verify behavior of empty object and empty array in ParseResults mode.
        # Empty ParseResults have len() == 0 and bool() == False, which may be
        # surprising when checking for the presence of a field with "if result.field:".
        print()
        print("--- Empty collection behavior (RETURN_PYTHON_COLLECTIONS=False) ---")
        empty_dict = results.glossary.GlossDiv.GlossList.EmptyDict
        print("  EmptyDict:  type =", type(empty_dict).__name__,
              ", len =", len(empty_dict),
              ", bool =", bool(empty_dict))
        empty_list = results.glossary.GlossDiv.GlossList.EmptyList
        print("  EmptyList:  type =", type(empty_list).__name__,
              ", len =", len(empty_list),
              ", bool =", bool(empty_list))
        print("  (Both are falsy — use 'is not None' or explicit key check instead of 'if field')")
