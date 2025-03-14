"""
Test cases for Nimble semantic analysis. See also the `testhelpers`
module.

Test harnesses have been provided for testing correct semantic
analysis of valid and invalid expressions.

**You will need to provide your own testing mechanisms for varDecs,
statements and higher-level constructs as appropriate.**


Group members: OCdt Shirritt, NCdt Murray, OCdt Wooltorton

Version: 2025-02-23

Instructor's version: 2023-02-08
"""

import unittest

from errorlog import Category
from symboltable import PrimitiveType, FunctionType
from testhelpers import do_semantic_analysis, pretty_types

VALID_EXPRESSIONS = [
    # Each entry is a pair: (expression source, expected type)
    # Due to the way the inferred_types are stored, using ctx.getText() as the key,
    # expressions must contain NO WHITE SPACE for the tests to work. E.g.,
    # '59+a' is fine, '59 + a' won't work.
    ('37', PrimitiveType.Int),
    ('-37', PrimitiveType.Int),



    #logical negation
    ('!true', PrimitiveType.Bool),
    ('!false',PrimitiveType.Bool),
    ('!(3<5)',PrimitiveType.Bool),

    #comparison
    ("5<3", PrimitiveType.Bool),
    ("5==3", PrimitiveType.Bool),
    ("5<=3", PrimitiveType.Bool),
    ("true==false", PrimitiveType.Bool),

    #parens
    ('(5)',PrimitiveType.Int),
    ('(true)',PrimitiveType.Bool),
    ('(3+5)',PrimitiveType.Int),

    #addsub
    ('5+3',PrimitiveType.Int),
    ('5-3',PrimitiveType.Int),
    ('"hello"+"world"', PrimitiveType.String),

    #muldiv
    ('5*3',PrimitiveType.Int),
    ('6/3',PrimitiveType.Int),

]

INVALID_EXPRESSIONS = [
    # Each entry is a pair: (expression source, expected error category)
    # As for VALID_EXPRESSIONS, there should be NO WHITE SPACE in the expressions.
    ('!37', Category.INVALID_NEGATION),
    ('!!37', Category.INVALID_NEGATION),

    #comparison
    ("false<3", Category.INVALID_BINARY_OP),
    ("5==true", Category.INVALID_BINARY_OP),
    ("true<false", Category.INVALID_BINARY_OP),

    #addsub
    ('true-5', Category.INVALID_BINARY_OP),

    # muldiv
    ('true*3', Category.INVALID_BINARY_OP),
    ('"haggis"/5', Category.INVALID_BINARY_OP),

    # variable
    ('x', Category.UNDEFINED_NAME)
]


def print_debug_info(source, indexed_types, error_log):
    """
    Can be called from test cases when things aren't going as expected
    and you need a look at the inferred types and error_log. See commented-out
    examples in test_valid_expressions and test_invalid_expressions below
    """
    print('\n------------------------------')
    print(f'{source}\n')
    print(pretty_types(indexed_types))
    if error_log.total_entries():
        print(f'\n{error_log}')


class TypeTests(unittest.TestCase):

    def test_valid_expressions(self):
        """
        For each pair (expression source, expected type) in VALID_EXPRESSIONS, verifies
        that the expression's inferred type is as expected, and that there are no errors
        in the error_log.
        """
        for expression, expected_type in VALID_EXPRESSIONS:
            error_log, global_scope, indexed_types = do_semantic_analysis(expression, 'expr')
            # this is an example of how to use the print_debug_info function to understand errors
            # if expression == '-37':
            #     print_debug_info(expression, indexed_types, error_log)
            with self.subTest(expression=expression, expected_type=expected_type):
                self.assertEqual(expected_type, indexed_types[1][expression])
                self.assertEqual(0, error_log.total_entries())

    def test_invalid_expressions(self):
        """
        For each pair (expression source, expected error category) in INVALID_EXPRESSIONS,
        verifies that the expression is assigned the ERROR type and that there is a error_logged
        error of the expected category relating to the expression.
        """
        for expression, expected_category in INVALID_EXPRESSIONS:
            error_log, global_scope, indexed_types = do_semantic_analysis(expression, 'expr')
            # if expression == '!!37':
            #     print_debug_info(expression, indexed_types, error_log)
            with self.subTest(expression=expression,
                              expected_category=expected_category):
                self.assertEqual(PrimitiveType.ERROR, indexed_types[1][expression])
                self.assertTrue(error_log.includes_exactly(expected_category, 1, expression))

    #     """
    #     This is an example of a slightly more complicated test. When run with the
    #     provided code it will fail, since variables aren't yet handled.
    #
    #     TODO: Make this test case pass (eventually; other things to do first)
    #     """
    def test_simple_var_dec(self):
        #for statement, expected_type in VALID_STATEMENTS:
        error_log, global_scope, indexed_types = do_semantic_analysis('var x : Int x = 5', 'script')
        self.assertEqual(0, error_log.total_entries())
        main_scope = global_scope.child_scope_named('$main')
        symbol = main_scope.resolve('x')
        self.assertIsNotNone(symbol, 'variable x not defined')
        self.assertEqual(PrimitiveType.Int, symbol.type)

    def test_failed_var_dec_with_value(self):
        #for statement, expected_type in VALID_STATEMENTS:
        error_log, global_scope, indexed_types = do_semantic_analysis('var x : Bool x = 5', 'script')
        self.assertEqual(1, error_log.total_entries())
        main_scope = global_scope.child_scope_named('$main')
        symbol = main_scope.resolve('x')
        self.assertIsNotNone(symbol, 'variable x not defined')
        self.assertEqual(PrimitiveType.Bool, symbol.type)

    def test_simple_var_dec_with_value(self):
        #Declare variable
        # call variable#
        #for statement, expected_type in VALID_STATEMENTS:
        error_log, global_scope, indexed_types = do_semantic_analysis('var x : Int = 5', 'script')
        self.assertEqual(0, error_log.total_entries())
        main_scope = global_scope.child_scope_named('$main')
        symbol = main_scope.resolve('x')
        self.assertIsNotNone(symbol, 'variable x not defined')
        self.assertEqual(PrimitiveType.Int, symbol.type)

    def test_assignment_fail(self):
        # for statement, expected_type in VALID_STATEMENTS:
        error_log, global_scope, indexed_types = do_semantic_analysis('var x : Int x = true', 'script')
        self.assertEqual(1, error_log.total_entries())
        main_scope = global_scope.child_scope_named('$main')
        symbol = main_scope.resolve('x')
        self.assertIsNotNone(symbol, 'variable x not defined')
        self.assertEqual(PrimitiveType.Int, symbol.type)

#=================================LAB 4 TEST CASES START================================

    # def test_funcDef_returning_void(self):
    #     # Declare variable
    #     # call variable#
    #     # for statement, expected_type in VALID_STATEMENTS:
    #     error_log, global_scope, indexed_types = do_semantic_analysis('func f() {var x : Int = 3 print x} func g() { var x : String = "abc" print x f()} var x : Bool = true print x g()', 'script')
    #     important_scope_list = global_scope.resolve('f')
    #     self.assertEqual(PrimitiveType.Void, important_scope_list.type)
    #     important_scope_list = global_scope.resolve('g')
    #     self.assertEqual(PrimitiveType.Void, important_scope_list.type)
    #
    # def test_funcDef_returning_int(self):
    #     # Declare variable
    #     # call variable#
    #     # for statement, expected_type in VALID_STATEMENTS:
    #     error_log, global_scope, indexed_types = do_semantic_analysis('func f() -> Int {var x : Int = 3 print x} func g() { var x : String = "abc" print x f()} var x : Bool = true print x g()', 'script')
    #     important_scope_list = global_scope.resolve('f')
    #     self.assertEqual(PrimitiveType.Int, important_scope_list.type)
    #     important_scope_list = global_scope.resolve('g')
    #     self.assertEqual(PrimitiveType.Void, important_scope_list.type)
    #
    # def test_funcDef_returning_str(self):
    #     # Declare variable
    #     # call variable#
    #     # for statement, expected_type in VALID_STATEMENTS:
    #     error_log, global_scope, indexed_types = do_semantic_analysis('func f() -> String {var x : Int = 3 print x} func g() { var x : String = "abc" print x f()} var x : Bool = true print x g()', 'script')
    #     important_scope_list = global_scope.resolve('f')
    #     self.assertEqual(PrimitiveType.String, important_scope_list.type)
    #     important_scope_list = global_scope.resolve('g')
    #     self.assertEqual(PrimitiveType.Void, important_scope_list.type)

    def test_funcDef_returning_bool(self):
        # Declare variable
        # call variable#
        # for statement, expected_type in VALID_STATEMENTS:
        error_log, global_scope, indexed_types = do_semantic_analysis('func f(a : Int) -> Bool {var x : Int = 3 print x} func g() { var x : String = "abc" print x f()} var x : Bool = true print x g()', 'script')
        important_scope_list = global_scope.resolve('f')
        print(important_scope_list.type)
        #self.assertEqual(FunctionType([PrimitiveType.Int], PrimitiveType.Bool), important_scope_list.type)
        important_scope_list = global_scope.resolve('g')
        #self.assertEqual(PrimitiveType.Void, important_scope_list.type)