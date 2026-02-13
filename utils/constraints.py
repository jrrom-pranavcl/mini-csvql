import pyparsing as p

# File to stop circular imports

datatypes = {
    "FLOAT": p.pyparsing_common.real,
    "INT": p.pyparsing_common.signed_integer,
    "STRING": p.quoted_string().set_parse_action(p.remove_quotes),
}

datatype_constraints_keywords = dict(
    map(lambda key: (key, p.CaselessKeyword(key)), datatypes.keys())
)
datatype_constraints = p.MatchFirst(map(p.CaselessKeyword, datatypes.keys()))
