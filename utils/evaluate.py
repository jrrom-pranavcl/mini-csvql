import pyparsing as p

# ==========================================
# Expressions
# ==========================================


def evaluate_arithmetic(tokens):
    return eval("".join(map(str, tokens)))

def evaluate_values(tokens):
    result = []
    for token in tokens:
        if token in ["(", ")", "VALUES"]: continue
        result.append(token)
    return [result]
# ==========================================
# Statements
# ==========================================


def evaluate_print(tokens):
    print(tokens[1])
