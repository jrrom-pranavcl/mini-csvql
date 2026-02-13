from .evaluate import *
import pyparsing as p
import readline
import sys

# ==========================================

datatypes = {
    "FLOAT": p.pyparsing_common.real,
    "INT": p.pyparsing_common.signed_integer,
    "STRING": p.quoted_string().set_parse_action(p.remove_quotes),
}

datatype_constraints = p.MatchFirst(map(p.CaselessKeyword, datatypes.keys()))
datatype = p.MatchFirst(datatypes.values())
number = p.MatchFirst([datatypes["FLOAT"], datatypes["INT"]])

# ==========================================

symbols = """
  ( ) { } ; , + - * / =
"""

LP, RP, LB, RB, SC, CM, ADD, SUB, MUL, DIV, EQ = map(p.Char, symbols.split())

operators = ADD | SUB | MUL | DIV

expressions = {
    "arithmetic": (
        number + p.ZeroOrMore(operators + number),
        evaluate_arithmetic,
    ),
    "values": (
        p.CaselessKeyword("VALUES") + LP + p.delimited_list(datatype) + RP,
        evaluate_values
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
  CREATE DROP SHOW PRINT USE
"""

CREATE, DROP, SHOW, PRINT, USE = map(p.CaselessKeyword, commands.split())

column = p.Group(p.pyparsing_common.identifier + datatype_constraints)
create_subcommands = p.MatchFirst([
    (p.CaselessKeyword("DATABASE") + p.pyparsing_common.identifier),
    (
        p.CaselessKeyword("TABLE") + p.pyparsing_common.identifier
        + p.Group(LP.suppress() + p.DelimitedList(column) + RP.suppress())
    )
])
drop_subcommands = p.MatchFirst(map(p.CaselessKeyword, "DATABASE TABLE".split()))
show_subcommands = p.MatchFirst(map(p.CaselessKeyword, "DATABASES TABLES".split()))

statements = {
    "CREATE": (CREATE + create_subcommands, evaluate_create),
    "DROP": (DROP + drop_subcommands + p.pyparsing_common.identifier, evaluate_drop),
    "SHOW": (SHOW + show_subcommands, evaluate_show),
    "PRINT": (PRINT + expression, evaluate_print),
    "USE": (USE + p.pyparsing_common.identifier, evaluate_use),
}

sql_statement = p.MatchFirst(grammar for grammar, _ in statements.values()) + SC.suppress()

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


@interrupt_return(KeyboardInterrupt, p.ParseException, EOFError, ZeroDivisionError, IndexError, PermissionError)
def repl():
    while True:
        line = input("> ")
        # Multiline support
        while (line[-1] == "\\"):
            line = line[:-1]
            line += input("    ")
        print(
            sql_statement.parseString(line)[0]
        )

# ==========================================
