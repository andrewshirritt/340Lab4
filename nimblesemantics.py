"""
Group members: OCdt Shirritt, NCdt Murray, OCdt Wooltorton

Version: 2025-02-23

The nimblesemantics module contains classes sufficient to perform a semantic analysis
of Nimble programs.

The analysis has two major tasks:

- to infer the types of all expressions in a Nimble program and to add appropriate type
annotations to the program's ANTLR-generated syntax tree by storing an entry in the `node_types`
dictionary for each expression node, where the key is the node and the value is a
`symboltable.PrimitiveType` or `symboltable.FunctionType`.

- to identify and flag all violations of the Nimble semantic specification
using the `errorlog.ErrorLog` and other classes in the `errorlog` module.

There are two phases to the analysis:

1. DefineScopesAndSymbols, and

2. InferTypesAndCheckSemantics.

In the first phase, `symboltable.Scope` objects are created for all scope-defining parse
tree nodes: the script, each function definition, and the main. These are stored in the
`self.scopes` dictionary. Also in this phase, all declared function types must be recorded
in the appropriate scope.

Parameter and variable types can be recorded in the appropriate scope in either the first
phase or the second phase.

In the second phase, type inference is performed and all other semantic constraints are
checked.

"""

from errorlog import ErrorLog, Category
from nimble import NimbleListener, NimbleParser
from symboltable import PrimitiveType, Scope, FunctionType


class DefineScopesAndSymbols(NimbleListener):

    def __init__(self, error_log: ErrorLog, global_scope: Scope, types: dict):
        self.error_log = error_log
        self.current_scope = global_scope
        self.type_of = types

    #Set scope as main
    def enterMain(self, ctx: NimbleParser.MainContext):
        self.current_scope = self.current_scope.create_child_scope('$main', PrimitiveType.Void)

    #set scope as global
    def exitMain(self, ctx: NimbleParser.MainContext):
        self.current_scope = self.current_scope.enclosing_scope

    #Creates new scope for each function and sets as new scope
    def enterFuncDef(self, ctx:NimbleParser.FuncDefContext):
        if ctx.TYPE():
            if ctx.TYPE().getText() == 'Int':
                self.current_scope = self.current_scope.create_child_scope(ctx.ID().getText(), PrimitiveType.Int)
            elif ctx.TYPE().getText() == 'Bool':
                self.current_scope = self.current_scope.create_child_scope(ctx.ID().getText(), PrimitiveType.Bool)
            elif ctx.TYPE().getText() == 'String':
                self.current_scope = self.current_scope.create_child_scope(ctx.ID().getText(), PrimitiveType.String)
        else:
            self.current_scope = self.current_scope.create_child_scope(ctx.ID().getText(), PrimitiveType.Void)

    #define the function and its type in the global scope
    def exitFuncDef(self, ctx:NimbleParser.FuncDefContext):
        #generates a list of parameters
        type_list = []
        for param in ctx.parameterDef():
            type_list.append(param.TYPE())
        #manages function types
        if ctx.TYPE():
            if ctx.TYPE().getText() == 'Int':
                x = FunctionType(type_list, PrimitiveType.Int)
                self.current_scope.enclosing_scope.define(ctx.ID().getText(), x)
            elif ctx.TYPE().getText() == 'Bool':
                x = FunctionType(type_list, PrimitiveType.Bool)
                self.current_scope.enclosing_scope.define(ctx.ID().getText(), x)
            elif ctx.TYPE().getText() == 'String':
                x = FunctionType(type_list, PrimitiveType.String)
                self.current_scope.enclosing_scope.define(ctx.ID().getText(), x)
            #throw error if invalid type
            else:
                self.error_log.add(ctx, Category.INVALID_RETURN,
                                   f"error: type {ctx.TYPE().getText()} is not a valid return type for "
                                   f"{ctx.expr().getText()}.")
        else:
            x = FunctionType(type_list, PrimitiveType.Void)
            self.current_scope.define(ctx.ID().getText(), x)


        #rolls up to parent scope
        self.current_scope = self.current_scope.enclosing_scope

class InferTypesAndCheckConstraints(NimbleListener):
    """
    The type of each expression parse tree node is calculated and stored in the
    `self.type_of` dictionary, where the key is the node object, and the value is
    an instance of `symboltable.PrimitiveType`.

    The types of declared variables are stored in `self.variables`, which is a dictionary
    mapping from variable names to `symboltable.PrimitiveType` instances.

    Any semantic errors detected, e.g., undefined variable names,
    type mismatches, etc., are logged in the `error_log`
    """

    def __init__(self, error_log: ErrorLog, global_scope: Scope, types: dict):
        self.error_log = error_log
        self.current_scope = global_scope
        self.type_of = types

    # --------------------------------------------------------
    # Program structure
    # --------------------------------------------------------

    def exitScript(self, ctx: NimbleParser.ScriptContext):
        pass

    #in main scope if in main
    def enterMain(self, ctx: NimbleParser.MainContext):
        self.current_scope = self.current_scope.child_scope_named('$main')

    #back to global
    def exitMain(self, ctx: NimbleParser.MainContext):
        self.current_scope = self.current_scope.enclosing_scope

    #In function scope
    def enterFuncDef(self, ctx:NimbleParser.FuncDefContext):
        self.current_scope = self.current_scope.child_scope_named(ctx.ID().getText())


    #Define the parameters as variables in the function scope
    def exitFuncDef(self, ctx:NimbleParser.FuncDefContext):
        for i in range(len(ctx.parameterDef())):
            if ctx.parameterDef()[i].TYPE().getText() == 'Int':
                self.current_scope.define(ctx.parameterDef(i).ID().getText(), PrimitiveType.Int, True)
            elif ctx.parameterDef()[i].TYPE().getText() == 'Bool':
                self.current_scope.define(ctx.parameterDef(i).ID().getText(), PrimitiveType.Bool, True)
            elif ctx.parameterDef()[i].TYPE().getText() == 'String':
                self.current_scope.define(ctx.parameterDef(i).ID().getText(), PrimitiveType.String, True)

        #back to global
        self.current_scope = self.current_scope.enclosing_scope

        # check that the function is defined
        # create scope
    def exitFuncCall(self, ctx: NimbleParser.FuncCallContext):
        # check that function is defined. If it is defined it must also be declared. Check in the child scope list of the current scope for a matching name.
        # check number and type of parameters and that parameters are in order.
        for scope in self.current_scope.child_scopes.values():
            if ctx.ID().getText() == scope.name:
                # Scope is defined! Next to check number of parameters.
                # firstly, corner case: no params
                params = [self.current_scope.parameters()]
                if not ctx.expr() and len(params) == 0:
                    self.type_of[ctx] = self.current_scope.child_scope_named(ctx.ID().getText()).return_type
                elif len(ctx.expr()) == len(self.current_scope.parameters()):
                    # amounts are right. Check types now.
                    params = [self.current_scope.parameters()]
                    for param_index in range(len(params)):
                        if self.type_of[ctx.expr(param_index)] != params[param_index].type:
                            # test failed, params are not the same.
                            self.error_log.add(ctx, Category.INVALID_CALL,
                                               f"error: parameter types for {ctx.expr().getText()}.")
                            return
                    # success! parameters are all the same.
                    self.type_of[ctx] = self.current_scope.child_scope_named(ctx.ID().getText()).return_type
                    return
        self.error_log.add(ctx, Category.INVALID_CALL,
                           f"error: No definition for function call {ctx.expr().getText()}.")


    #checks that the return type of the current scope aka function has the same type as the expression
    def exitReturn(self, ctx: NimbleParser.ReturnContext):
        if ctx.expr():
            if not (self.current_scope.return_type == PrimitiveType.Int and self.type_of[ctx.expr()] == PrimitiveType.Int):
                self.error_log.add(ctx, Category.INVALID_RETURN,
                                   f"INVALID RETURN TYPES - RETURNING {ctx.expr().getText()} IS NOT THE SAME AS"
                                   f" THE FUNCTION RETURN TYPE {self.current_scope.return_type}")
            elif not (self.current_scope.return_type == PrimitiveType.Bool and self.type_of[ctx.expr()] == PrimitiveType.Bool):
                self.error_log.add(ctx, Category.INVALID_RETURN,
                                   f"INVALID RETURN TYPES - RETURNING {ctx.expr().getText()} IS NOT THE SAME AS"
                                   f" THE FUNCTION RETURN TYPE {self.current_scope.return_type}")
            elif not (self.current_scope.return_type == PrimitiveType.String and self.type_of[ctx.expr()] == PrimitiveType.String):
                self.error_log.add(ctx, Category.INVALID_RETURN,
                                   f"INVALID RETURN TYPES - RETURNING {ctx.expr().getText()} IS NOT THE SAME AS"
                                   f" THE FUNCTION RETURN TYPE {self.current_scope.return_type}")
        # no explicit type implies the type is void
        else:
            if not self.current_scope.return_type == PrimitiveType.Void:
                self.error_log.add(ctx, Category.INVALID_RETURN,
                                   f"INVALID RETURN TYPES - RETURNING VOID IS NOT THE SAME AS"
                                   f" THE FUNCTION RETURN TYPE {self.current_scope.return_type}")

        self.current_scope = self.current_scope.enclosing_scope
    # --------------------------------------------------------
    # Variable declarations
    # --------------------------------------------------------

    def exitVarDec(self, ctx: NimbleParser.VarDecContext):
        if self.current_scope.resolve_locally(ctx.ID().getText()) is None:
            if ctx.TYPE().getText() == "Int":
                self.current_scope.define(ctx.ID().getText(), PrimitiveType.Int)
            elif ctx.TYPE().getText() == "String":
                self.current_scope.define(ctx.ID().getText(), PrimitiveType.String)
            elif ctx.TYPE().getText() == "Bool":
                self.current_scope.define(ctx.ID().getText(), PrimitiveType.Bool)
            else:
                self.error_log.add(ctx, Category.ASSIGN_TO_WRONG_TYPE,
                                   f"{self.type_of[ctx].name} is invalid type name")
                return
            if ctx.expr():
                x = self.current_scope.resolve_locally(ctx.ID().getText())
                if x.type !=self.type_of[ctx.expr()]:
                    self.error_log.add(ctx, Category.ASSIGN_TO_WRONG_TYPE,
                                           f"cannot assign {ctx.expr().getText()} to type {ctx.TYPE().getText()}")

        else:

            self.error_log.add(ctx, Category.DUPLICATE_NAME,
                                   f"var {ctx.ID().getText()} already declared")





    # --------------------------------------------------------
    # Statements
    # --------------------------------------------------------

    def exitAssignment(self, ctx: NimbleParser.AssignmentContext):
        #is x declared
        if self.current_scope.resolve_locally(ctx.ID().getText()) is None:
            self.type_of[ctx] = PrimitiveType.ERROR
            self.error_log.add(ctx, Category.UNDEFINED_NAME, f"var {ctx.ID().getText()} is not declared")
        else:
            x = self.current_scope.resolve_locally(ctx.ID().getText())
            if x.type != self.type_of[ctx.expr()]:
                self.type_of[ctx] = PrimitiveType.ERROR
                self.error_log.add(ctx, Category.ASSIGN_TO_WRONG_TYPE, f"Incompatible type")



    def exitWhile(self, ctx: NimbleParser.WhileContext):
        if self.type_of[ctx.expr()] != PrimitiveType.Bool:
            self.type_of[ctx] = PrimitiveType.ERROR
            self.error_log.add(ctx, Category.CONDITION_NOT_BOOL, f"Expression must be of type bool")

    def exitIf(self, ctx: NimbleParser.IfContext):
        if self.type_of[ctx.expr()] != PrimitiveType.Bool:
            self.type_of[ctx] = PrimitiveType.ERROR
            self.error_log.add(ctx, Category.CONDITION_NOT_BOOL, f"Expression must be of type bool")

    def exitPrint(self, ctx: NimbleParser.PrintContext):
        if self.type_of[ctx.expr()] == PrimitiveType.ERROR or PrimitiveType.Void:
            self.type_of[ctx] = PrimitiveType.ERROR
            self.error_log.add(ctx, Category.UNPRINTABLE_EXPRESSION, "expression cannot be printed")

    # --------------------------------------------------------
    # Expressions
    # --------------------------------------------------------

    def exitIntLiteral(self, ctx: NimbleParser.IntLiteralContext):
        self.type_of[ctx] = PrimitiveType.Int

    def exitNeg(self, ctx: NimbleParser.NegContext):
        """ TODO: Extend to handle boolean negation. """
        if ctx.op.text == '-' and self.type_of[ctx.expr()] == PrimitiveType.Int:
            self.type_of[ctx] = PrimitiveType.Int
        elif ctx.op.text == '!' and self.type_of[ctx.expr()] == PrimitiveType.Bool:
            self.type_of[ctx] = PrimitiveType.Bool
        else:
            self.type_of[ctx] = PrimitiveType.ERROR
            self.error_log.add(ctx, Category.INVALID_NEGATION,
                               f"Can't apply {ctx.op.text} to {self.type_of[ctx].name}")

    def exitParens(self, ctx: NimbleParser.ParensContext):
        self.type_of[ctx] = self.type_of[ctx.expr()]

    def exitMulDiv(self, ctx: NimbleParser.MulDivContext):
        if self.type_of[ctx.expr(0)] == PrimitiveType.Int and self.type_of[ctx.expr(1)] == PrimitiveType.Int and (
                ctx.op.text == '*' or ctx.op.text == '/'):
            self.type_of[ctx] = PrimitiveType.Int
        else:
            self.type_of[ctx] = PrimitiveType.ERROR
            self.error_log.add(ctx, Category.INVALID_BINARY_OP,
                               f'cant mul or div {ctx.expr(0)} and {ctx.expr(1)} together')

    def exitAddSub(self, ctx: NimbleParser.AddSubContext):
        if self.type_of[ctx.expr(0)] == PrimitiveType.Int and self.type_of[ctx.expr(1)] == PrimitiveType.Int and (
                ctx.op.text == '+' or ctx.op.text == ('-')):
            self.type_of[ctx] = PrimitiveType.Int
        elif self.type_of[ctx.expr(0)] == PrimitiveType.String and self.type_of[
            ctx.expr(1)] == PrimitiveType.String and ctx.op.text == '+':
            self.type_of[ctx] = PrimitiveType.String
        else:
            self.type_of[ctx] = PrimitiveType.ERROR
            self.error_log.add(ctx, Category.INVALID_BINARY_OP,
                               f'cant add or sub {ctx.expr(0)} and {ctx.expr(1)} together')

    def exitCompare(self, ctx: NimbleParser.CompareContext):
        #2 op texts, 1 str. both expr must be int, returns bool#
        #1) ==
        if self.type_of[ctx.expr(0)] == PrimitiveType.Bool and self.type_of[
            ctx.expr(1)] == PrimitiveType.Bool and ctx.op.text == '==':
            self.type_of[ctx] = PrimitiveType.Bool
        elif self.type_of[ctx.expr(0)] == PrimitiveType.Int and self.type_of[
            ctx.expr(1)] == PrimitiveType.Int and ctx.op.text == '==':
            self.type_of[ctx] = PrimitiveType.Bool
        elif self.type_of[ctx.expr(0)] == PrimitiveType.Int and self.type_of[
            ctx.expr(1)] == PrimitiveType.Int and ctx.op.text == '<':
            self.type_of[ctx] = PrimitiveType.Bool
        elif self.type_of[ctx.expr(0)] == PrimitiveType.Int and self.type_of[
            ctx.expr(1)] == PrimitiveType.Int and ctx.op.text == '<=':
            self.type_of[ctx] = PrimitiveType.Bool
        else:
            self.type_of[ctx] = PrimitiveType.ERROR
            self.error_log.add(ctx, Category.INVALID_BINARY_OP, F"Can't do a binary operation with types:"
                                                                F"{ctx.expr(0).getText()}, {ctx.expr(1).getText()} and operation: {ctx.op.text}")

    def exitVariable(self, ctx: NimbleParser.VariableContext):
        #resolve_locally on scope with variable name.
        #check the current scope for the variable symbol
        if not self.current_scope.resolve_locally(ctx.getText()):
            self.type_of[ctx] = PrimitiveType.ERROR
            self.error_log.add(ctx, Category.UNDEFINED_NAME, F"{ctx.getText()} is undefined")
            return

        #Find the type of the variable
        self.type_of[ctx] = self.current_scope.resolve_locally(ctx.getText())



    def exitStringLiteral(self, ctx: NimbleParser.StringLiteralContext):
        self.type_of[ctx] = PrimitiveType.String

    def exitBoolLiteral(self, ctx: NimbleParser.BoolLiteralContext):
        self.type_of[ctx] = PrimitiveType.Bool
