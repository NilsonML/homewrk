# Warehouse Manager

Console app for managing warehouses and goods, built as a learning project in two iterations:

1. **OOP version** (`main.py`, `utils.py`): classes `Warehouse`, `Product`, `Food`, `Equipment` with dunder methods (`__getitem__`, `__setitem__`, `__contains__`, `__iadd__`, comparison operators for sorting). The original assignment is in [docs/TASK.md](docs/TASK.md).
2. **SQLite version** (`main_db.py`, `logic.py`, `databaseclass.py`): the same domain with persistent storage.

**Stack:** Python · sqlite3 · pytest

## Features (SQLite version)

- Create, select and delete warehouses (deleting a warehouse removes its goods)
- Add goods: name, quantity, price, type (food / non-food), expiry or warranty date; restocking an existing item increases its quantity
- Sell N units with a check that enough stock is available
- List goods sorted by name, price or **total value** (price × quantity)
- Look up an item by id; days left until expiry / end of warranty

## Run

```bash
python main_db.py      # SQLite version, data is stored in Projectwarehouse.sqlite3
python main.py         # OOP version (in-memory)
pytest                 # tests for the database layer
```

## Design notes

- All SQL values go through query parameters (`?`), never string formatting, so SQL injection is impossible.
- `ORDER BY` cannot take a parameter (it would sort by a constant), so the sort column is chosen from a whitelist.
- Dates are stored as ISO strings `YYYY-MM-DD`.
- Tests use an in-memory database (`:memory:`): fast and leave no files behind.
