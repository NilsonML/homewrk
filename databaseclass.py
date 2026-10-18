"""
databaseclass.py — хранение складов и товаров в SQLite.

Все значения передаются в запросы через параметры (?), а не через f-строки:
так невозможна SQL-инъекция. Исключение — ORDER BY: имя колонки нельзя
передать параметром, поэтому оно выбирается из белого списка.
"""

import datetime as dt
import sqlite3

# ORDER BY ? НЕ работает: параметр подставляется как строковая константа,
# и все строки "равны" — сортировки нет. Поэтому выбираем выражение из словаря.
ORDER_BY = {
    "name": "name",
    "price": "price",
    "total": "price * amount",   # общая стоимость партии
}


class Database:
    def __init__(self, name: str):
        self.connection = sqlite3.connect(name)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        cur = self.connection.cursor()
        cur.execute("""create table if not exists warehouses
                    (id integer primary key autoincrement, name text unique)""")
        cur.execute("""create table if not exists products
        (
                    id integer primary key autoincrement,
                    name varchar(20),
                    amount float, price float, type varchar(7),
                    date date,
                    warehouse_id integer,
                    foreign key (warehouse_id) references warehouses(id))""")
        self.connection.commit()

    @staticmethod
    def _to_iso_date(value) -> str:
        """Дата хранится как 'ГГГГ-ММ-ДД'. Объект datetime sqlite сохранил бы
        как 'ГГГГ-ММ-ДД ЧЧ:ММ:СС', и проверка срока годности падала бы на разборе."""
        if isinstance(value, (dt.datetime, dt.date)):
            return value.strftime("%Y-%m-%d")
        return str(value)[:10]

    def add_product(self, name, amount, price, type, date, warehouse_id):
        """Новая позиция или пополнение существующей (то же имя, цена, тип, дата)."""
        date = self._to_iso_date(date)
        cur = self.connection.cursor()
        cur.execute("select id from products where name = ? and price = ? and type = ? "
                    "and date = ? and warehouse_id = ?",
                    [name, price, type, date, warehouse_id])
        data = cur.fetchone()
        if not data:
            cur.execute("""insert into products(name, amount, price, type, date, warehouse_id)
                        values (?, ?, ?, ?, ?, ?)""",
                        [name, amount, price, type, date, warehouse_id])
        else:
            # Было: set(amount = amount+?) — синтаксическая ошибка SQLite
            cur.execute("update products set amount = amount + ? where id = ?", [amount, data[0]])
        self.connection.commit()

    def delete_product(self, amount, id) -> bool:
        """Выкупить amount единиц. False, если товара нет или его меньше, чем просят."""
        cur = self.connection.cursor()
        cur.execute("select amount from products where id = ?", [id])
        row = cur.fetchone()
        if row is None or amount <= 0 or amount > row[0]:
            return False
        if amount == row[0]:
            cur.execute("delete from products where id = ?", [id])
        else:
            cur.execute("update products set amount = amount - ? where id = ?", [amount, id])
        self.connection.commit()
        return True

    def get_info_product(self, id):
        cur = self.connection.cursor()
        cur.execute("select * from products where id = ?", [id])
        return cur.fetchone()

    def list_of_products(self, warehouse_id, order_by="name"):
        if order_by not in ORDER_BY:
            raise ValueError(f"Сортировка возможна по: {', '.join(ORDER_BY)}")
        cur = self.connection.cursor()
        cur.execute(f"select * from products where warehouse_id = ? order by {ORDER_BY[order_by]}",
                    [warehouse_id])
        return cur.fetchall()

    def check_date_of_product(self, id):
        """Сколько дней осталось до конца срока годности / гарантии (None, если товара нет)."""
        cur = self.connection.cursor()
        cur.execute("select date from products where id = ?", [id])
        row = cur.fetchone()
        if row is None:
            return None
        deadline = dt.date.fromisoformat(row[0][:10])
        return (deadline - dt.date.today()).days

    def list_of_warehouses(self):
        cur = self.connection.cursor()
        cur.execute("select * from warehouses")
        return cur.fetchall()

    def create_warehouse(self, name):
        """id нового склада или None, если имя пустое или уже занято."""
        if not name or self.current_warehouse(name) is not None:
            return None
        cur = self.connection.cursor()
        cur.execute("insert into warehouses(name) values (?)", [name])
        self.connection.commit()
        return cur.lastrowid

    def delete_warehouse(self, name) -> bool:
        warehouse_id = self.current_warehouse(name)
        if warehouse_id is None:
            return False
        cur = self.connection.cursor()
        # Сначала товары склада, иначе они остались бы "ничьими"
        cur.execute("delete from products where warehouse_id = ?", [warehouse_id])
        cur.execute("delete from warehouses where id = ?", [warehouse_id])
        self.connection.commit()
        return True

    def current_warehouse(self, name):
        cur = self.connection.cursor()
        cur.execute("select id from warehouses where name = ?", [name])
        data = cur.fetchone()
        return data[0] if data else None
