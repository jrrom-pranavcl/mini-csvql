# mini-CSVQL

A small SQL interpreter to interact with CSV files.

## Features:

- Case insensitive
- REPL and server frontend
- Supported commands:
  - `DROP`
  - `INSERT`
  - `PRINT`
  - `SELECT`
  - `SHOW`
  - `UPDATE`
  - `USE`

## Syntax:

### Database creation

In mini-CSVQL, databases are just directories with a `database.json` file. To create a database, you must use the `CREATE DATABASE` command.

```mysql
CREATE DATABASE name;
```

```
Database name successfully created.
```

### Displaying all the databases

```mysql
SHOW DATABASES;
```

```
name
```

### Selecting a database

```mysql
USE name;
```

```
Database name successfully selected.
```
