from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import os
import polars as pl
import pyparsing as p
import shutil

# ==========================================
# Helpers
# ==========================================

def create_config():
    return {
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def is_database(dir: Path):
    return (dir / "database.json").exists()

@dataclass
class State:
    path: Path | None = None

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

def create_starter_frame(name, constraint_pairs: list[list[str]]):
    columns = [pair[0] for pair in constraint_pairs]
    constraints = [pair[1] for pair in constraint_pairs]
    
    # Create DataFrame with constraints as first row
    df = pl.DataFrame([constraints], schema=columns, orient="row")
    df.write_csv((State.path / name).with_suffix(".csv"))
    return

# ==========================================
# Statements
# ==========================================

# =======
# For tables and databases
# =======

def evaluate_create(tokens):
    _, command, name = tokens[:3]
    name = Path(name)
    if (command == "DATABASE"):
        config = create_config()
        if name.exists():
            return "A file or directory with the same name already exists."
        name.mkdir()
        with (name / "database.json").open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return f"Database {str(name)} successfully created."
    if (command == "TABLE"):
        columns_pairs = tokens[3]
        if not State.path:
            return "Database not selected."
        create_starter_frame(name, columns_pairs)
        return f"Table {str(name)} successfully created"
        
def evaluate_drop(tokens):
    _, command, name = tokens
    name = Path(name)
    if (command == "DATABASE"):
        if not name.exists():
            return "Directory does not exist."
        if not is_database(name):
            return "Directory is not a database."
        shutil.rmtree(name)
        return f"Database {str(name)} successfully dropped."
    if (command == "TABLE"):
        if not State.path:
            return "Database not selected."
        table = Path(State.path / name).with_suffix(".csv")
        if not table.exists():
            return "Specified table does not exist."
        table.unlink()
        return "Table successfully dropped."

def evaluate_show(tokens):
    _, command = tokens
    working_dir = Path(".")
    if (command == "DATABASES"):
        result = ""
        for dir in working_dir.iterdir():
            if is_database(dir):
                result += str(dir) + " "
        if result == "": return "No databases in the current directory."
        return result
    if (command == "TABLES"):
        if not State.path:
            return "Database not selected."
        result = ""
        for file in State.path.glob("*.csv"):
            result += str(file.stem) + " "
        if result == "": return "No tables in the current database."
        return result

# =======
# Utility
# =======

def evaluate_print(tokens):
    return tokens[1]

def evaluate_use(tokens):
    _, database = tokens
    selected = Path(database)
    if not is_database(selected):
        return "The specified database does not exist."
    State.path = selected
    return f"Database {database} successfully selected."
