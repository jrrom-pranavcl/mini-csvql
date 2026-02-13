from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from .constraints import datatypes
import csv
import json
import os
import polars as pl
import pyparsing as p
import shutil
from functools import reduce
from operator import and_, or_

# ==========================================
# Helpers
# ==========================================


def create_config():
    return {"created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


def is_database(dir: Path):
    return (dir / "database.json").exists()


def check_if_state_path_exists(func):
    def wrapper(tokens):
        if not State.path:
            return "Database not selected."
        return func(tokens)

    return wrapper


def check_if_obeys_constraints(file: Path, values: list[Any]):
    df = pl.read_csv(file)

    if len(values) != len(df.columns):
        return "The number of values does not match the number of columns."

    constraints = df.row(0)

    for i in range(len(values)):
        to_check = str(values[i])

        if constraints[i] == "STRING" and type(values[i]) == str:
            to_check = f"'{to_check}'"

        try:
            if not datatypes[constraints[i]].parse_string(to_check):
                return "It cannot be inserted because it does not follow constraints."
        except p.ParseException as e:
            return "It cannot be inserted because it does not follow constraints."

    return True


def database_location(table):
    return State.path / (table + ".csv")

def filter_df(df: pl.DataFrame, tokens) -> pl.DataFrame:
    to_expr = lambda col, op, val: getattr(pl.col(col), {
        '=': '__eq__', '>': '__gt__', '<': '__lt__',
        '>=': '__ge__', '<=': '__le__', '!=': '__ne__'
    }[op])(val)
    
    conditions = [to_expr(*tokens[i:i+3]) for i in range(0, len(tokens), 4) if i + 2 < len(tokens)]
    operators = [and_ if tokens[i] == 'AND' else or_ for i in range(3, len(tokens), 4)]
    
    return df.filter(reduce(
        lambda acc, pair: pair[0](acc, pair[1]),
        zip(operators, conditions[1:]),
        conditions[0]
    ))

def cast_cols_to_avoid_str_failure(df: pl.DataFrame):
    constraints = dict(zip(df.columns, df.row(0)))
    df = df.slice(1)
    
    # We need to cast columns otherwise the whole thing will EXPLODE!!!!
    type_map = {"INT": pl.Int64, "FLOAT": pl.Float64, "STRING": pl.String}
    df = df.select([
        pl.col(col).cast(type_map.get(constraints[col], pl.String))
        for col in df.columns
    ])

    return df


def clean_table(df: pl.DataFrame):
    result = str(df).split("\n")
    skip_patterns = ("null", "shape", "---", "│ str", "i64", "f64")
    result = "\n".join(
        line for line in result if not any(pattern in line for pattern in skip_patterns)
    )

    return result

@dataclass
class State:
    path: Path | None = None


# ==========================================
# Expressions
# ==========================================


def evaluate_arithmetic(tokens):
    return eval("".join(map(str, tokens)))

def evaluate_boolean(tokens):
    return [tokens]

def evaluate_values(tokens):
    result = []
    for token in tokens:
        if token in ["(", ")", "VALUES"]:
            continue
        result.append(token)
    return [result]


def create_starter_frame(name, constraint_pairs: list[list[str]]):
    columns = [pair[0] for pair in constraint_pairs]
    constraints = [pair[1] for pair in constraint_pairs]

    # Create DataFrame with constraints as first row
    df = pl.DataFrame([constraints], schema=columns, orient="row")
    df.write_csv((State.path / name).with_suffix(".csv"))


# ==========================================
# Statements
# ==========================================

# =======
# For tables and databases
# =======


def evaluate_create(tokens):
    """
    FORMAT:
    ['CREATE', 'DATABASE', 'utils']
    ['CREATE', 'TABLE', 'utils']
    """
    print(tokens)
    _, command, name = tokens[:3]
    name = Path(name)
    if command == "DATABASE":
        config = create_config()
        if name.exists():
            return "A file or directory with the same name already exists."
        name.mkdir()
        with (name / "database.json").open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return f"Database {str(name)} successfully created."
    if command == "TABLE":
        columns_pairs = tokens[3]
        columns_pairs = cast(list[list[str]], columns_pairs)
        if not State.path:
            return "Database not selected."
        create_starter_frame(name, columns_pairs)
        return f"Table {str(name)} successfully created"


def evaluate_drop(tokens):
    """
    FORMAT:
    ['DROP', 'DATABASE', 'hi']
    ['DROP', 'TABLE', 'hi']
    """
    _, command, name = tokens
    name = Path(name)
    if command == "DATABASE":
        if not name.exists():
            return "Directory does not exist."
        if not is_database(name):
            return "Directory is not a database."
        shutil.rmtree(name)
        return f"Database {str(name)} successfully dropped."
    if command == "TABLE":
        if not State.path:
            return "Database not selected."
        table = Path(State.path / name).with_suffix(".csv")
        if not table.exists():
            return "Specified table does not exist."
        table.unlink()
        return "Table successfully dropped."


def evaluate_show(tokens):
    """
    Format:
    ['SHOW', 'DATABASES']
    ['SHOW', 'TABLES']
    """
    _, command = tokens
    working_dir = Path(".")
    if command == "DATABASES":
        result = ""
        for dir in working_dir.iterdir():
            if is_database(dir):
                result += str(dir) + " "
        if result == "":
            return "No databases in the current directory."
        return result
    if command == "TABLES":
        if not State.path:
            return "Database not selected."
        result = ""
        for file in State.path.glob("*.csv"):
            result += str(file.stem) + " "
        if result == "":
            return "No tables in the current database."
        return result


# =======
# For tables
# =======


@check_if_state_path_exists
def evaluate_insert(tokens):
    """
    Format: ['INSERT', 'INTO', 'teachers', [101, 'TeacherName']]
    """
    table, values = tokens[2:]
    State.path = cast(Path, State.path)
    file = database_location(table)
    if not file.exists():
        return f"The table {table} does not exist in the database {State.path.stem}"
    result = check_if_obeys_constraints(file, values)
    if result == True:
        with open(file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(values)
            return f"Successfully inserted into table {table}"
    return result

@check_if_state_path_exists
def evaluate_delete(tokens):
    """
    format: ['DELETE', 'FROM', 'student', 'WHERE', ['marks', '<', 50]]
    """
    table = tokens[2]
    file = database_location(table)
    if not file.exists():
        return f"The table {table} does not exist in the database"

    df = pl.read_csv(file)
    constraints = df.row(0)
    df = cast_cols_to_avoid_str_failure(df)
    
    try:
        to_delete = filter_df(df, tokens[4])
        df = df.join(to_delete, on=df.columns, how="anti")
    except Exception as e:
        return f"{e}"

    df_as_strings = df.select([pl.col(c).cast(pl.String) for c in df.columns])
    new_df = pl.DataFrame([constraints], schema=df_as_strings.columns, orient="row")
    new_df = pl.concat([new_df, df_as_strings])
    new_df.write_csv(file)

    return f"Deleted {len(to_delete.rows())} rows."

@check_if_state_path_exists
def evaluate_select(tokens):
    """
    Format:
    ['SELECT', '*', 'FROM', 'student']
    ['SELECT', ['name', 'marks'], 'FROM', 'student']
    ['SELECT', '*', 'FROM', 'student', 'WHERE', ['marks', '>', 30, 'AND', 'marks', '<', 100]]
    ['SELECT', ['name', 'marks'], 'FROM', 'student', 'WHERE', ['marks', '>', 30, 'AND', 'marks', '<', 100]]
    """
    selected, table = tokens[1], tokens[3]
    file = database_location(table)
    if not file.exists():
        return f"The table {table} does not exist in the database"

    df = pl.read_csv(file)
    df = cast_cols_to_avoid_str_failure(df)
    
    # Apply WHERE filter if present
    if len(tokens) > 5 and tokens[4] == "WHERE":
        try:
            df = filter_df(df, tokens[5])
        except Exception as e:
            return f"{e}"
    
    df = df.select(*selected)

    return clean_table(df)

# =======
# Utility
# =======


def evaluate_print(tokens):
    """
    Format:
    ['PRINT', 'hi']
    ['PRINT', [123, 123.123, 'hi']]
    """
    return tokens[1]


def evaluate_use(tokens):
    """
    Format: ['USE', 'hi']
    """
    _, database = tokens
    selected = Path(database)
    if not is_database(selected):
        return "The specified database does not exist."
    State.path = selected
    return f"Database {database} successfully selected."
