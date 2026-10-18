"""Тесты слоя БД на базе в памяти (:memory:) — без файлов на диске."""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from databaseclass import Database  # noqa: E402

FUTURE = (dt.date.today() + dt.timedelta(days=10)).isoformat()


@pytest.fixture
def db():
    database = Database(":memory:")
    database.create_warehouse("main")
    return database


def wid(db):
    return db.current_warehouse("main")


def test_restock_existing_product_increases_amount(db):
    """Раньше: синтаксическая ошибка в UPDATE (set(amount = amount+?))."""
    db.add_product("milk", 5, 80, "прод", FUTURE, wid(db))
    db.add_product("milk", 3, 80, "прод", FUTURE, wid(db))
    rows = db.list_of_products(wid(db))
    assert len(rows) == 1 and rows[0][2] == 8


def test_sorting_actually_sorts(db):
    """Раньше: ORDER BY ? не сортировал."""
    for name, amount, price in [("a", 1, 30), ("b", 10, 10), ("c", 2, 20)]:
        db.add_product(name, amount, price, "непрод", FUTURE, wid(db))
    assert [r[1] for r in db.list_of_products(wid(db), "price")] == ["b", "c", "a"]
    assert [r[1] for r in db.list_of_products(wid(db), "total")] == ["a", "c", "b"]  # 30, 40, 100


def test_unknown_sort_column_rejected(db):
    with pytest.raises(ValueError):
        db.list_of_products(wid(db), "price; drop table products")


def test_partial_and_full_buy(db):
    db.add_product("tv", 5, 1000, "непрод", FUTURE, wid(db))
    pid = db.list_of_products(wid(db))[0][0]
    assert db.delete_product(2, pid) is True
    assert db.get_info_product(pid)[2] == 3
    assert db.delete_product(10, pid) is False          # больше, чем есть
    assert db.delete_product(3, pid) is True
    assert db.get_info_product(pid) is None             # выкупили всё
    assert db.delete_product(1, 999) is False           # несуществующий id


def test_days_left_with_datetime_input(db):
    """Раньше datetime сохранялся с временем, и разбор '%Y-%m-%d' падал."""
    deadline = dt.datetime.combine(dt.date.today() + dt.timedelta(days=7), dt.time())
    db.add_product("cheese", 1, 300, "прод", deadline, wid(db))
    pid = db.list_of_products(wid(db))[0][0]
    assert db.check_date_of_product(pid) == 7


def test_warehouses(db):
    assert db.create_warehouse("main") is None          # дубликат
    assert db.create_warehouse("") is None
    other = db.create_warehouse("second")
    db.add_product("x", 1, 1, "непрод", FUTURE, other)
    assert db.delete_warehouse("second") is True
    assert db.current_warehouse("second") is None
    assert db.list_of_products(other) == []             # товары удалены вместе со складом
