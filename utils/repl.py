from .evaluate import *
import pyparsing as p
import readline
import sys

# ==========================================

datatypes = {
    "FLOAT": p.pyparsing_common.ieee_float,
    "INT": p.pyparsing_common.signed_integer,
    "STRING": p.quoted_string().set_parse_action(p.remove_quotes),
}

datatype_constraints = p.MatchFirst(map(p.CaselessKeyword, datatypes.keys()))

# ==========================================

symbols = """
  ( ) { } ; , + - * / =
"""

LP, RP, LB, RB, SC, CM, ADD, SUB, MUL, DIV, EQ = map(p.Char, symbols.split())

operators = ADD | SUB | MUL | DIV

expressions = {
    "arithmetic": (
        datatypes["INT"] + p.ZeroOrMore(operators + datatypes["INT"]),
        evaluate_arithmetic,
    )
}

for grammar, handler in expressions.values():
    grammar.add_parse_action(handler)

expression = p.MatchFirst(
    # We need to evaluate expressions first otherwise they will be incorrectly thought of as datatypes
    list(grammar for grammar, _ in expressions.values())
    +
    # Now the datatypes
    list(datatypes.values())
)

# ==========================================

commands = """
  CREATE PRINT
"""

INSERT, PRINT = map(p.CaselessKeyword, commands.split())

statements = {"PRINT": (PRINT + expression, evaluate_print)}

sql_statement = p.MatchFirst(grammar for grammar, _ in statements.values()) + SC

for grammar, handler in statements.values():
    grammar.add_parse_action(handler)

# ==========================================


def interrupt_return(*interrupts):
    def decorator(func):
        def wrapper():
            try:
                func()
            except interrupts as e:
                print("\n", e)
                exit(0)

        return wrapper

    return decorator


@interrupt_return(KeyboardInterrupt, p.ParseException)
def repl():
    while True:
        line = input("> ")
        sql_statement.parseString(line)


# ==========================================
