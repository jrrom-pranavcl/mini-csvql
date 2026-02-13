import pyparsing as p

# ==========================================
# Expressions
# ==========================================


def evaluate_arithmetic(tokens):
    return eval("".join(map(str, tokens)))


# ==========================================
# Statements
# ==========================================


def evaluate_print(tokens):
    print(tokens[1])
