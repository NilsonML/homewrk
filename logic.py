from databaseclass import Database
from newutils import check_date, check_request, chek_type_product, get_float_value, get_int_input

db = Database('Projectwarehouse.sqlite3')

current_warehouse = None
NEEDS_WAREHOUSE = {3, 4, 5, 6, 7}  # действия, для которых нужен выбранный склад

def main_menu():
    global current_warehouse
    print('''
        1 - Создать новый склад
        2 - Выбрать склад, с которым человек будет работать по его имени
        3 - Добавить товар на склад
        4 - Выкупить товар со склада
        5 - Посмотреть товары на складе отсортированные по общей стоимости
        6 - Проверить наличие товара на складе по его названию
        7 - Проверить срок годности/гарантию товара
        8 - Удалить склад
        9 - Выход из программы
        ''')
    if current_warehouse:
        data = db.list_of_products(current_warehouse, 'name')
        print(*data, sep ='\n')
    request = int(check_request())
    if request in NEEDS_WAREHOUSE and current_warehouse is None:
        print('Сначала создайте или выберите склад (пункты 1 и 2)')
        return
    match request:
        case 1:
            name = input('Введите название склада: ').strip()
            new_warehouse = db.create_warehouse(name)
            if new_warehouse:
                print('Склад создан! \n')
                current_warehouse = new_warehouse
            else:
                print('Не удалось создать склад')
        case 2:
            print(*db.list_of_warehouses(), sep = '\n')
            name = input('Введите название склада: ').strip()
            new_warehouse = db.current_warehouse(name)
            if new_warehouse:
                print('Склад изменен! \n')
                current_warehouse = new_warehouse
            else:
                print('Не удалось поменять склад')
        case 3:
            name_of_product = input("Введите название продукта: ")
            amount = get_float_value("Сколько товара вы хотите заказать: ")
            price = get_float_value("Какая цена товара: ")
            type = chek_type_product("прод или непрод: ")
            date = check_date("Какой срок годности формат(гггг-мм-дд): ")
            db.add_product(name_of_product, amount, price, type, date, current_warehouse)    
        case 4:
            id = get_int_input('Введите id продукта: ')
            amount = get_float_value('Введите количество, которое хотите купить: ')
            if not db.delete_product(amount, id):
                print('Нет такого товара или его недостаточно на складе')
        case 5:
            # По общей стоимости партии (цена × количество), как в меню
            data = db.list_of_products(current_warehouse, 'total')
            print(*data, sep='\n')
        case 6:
            info_id = get_int_input('Введите id для получения информации о продукте: ')
            info = db.get_info_product(info_id)
            print(*info) if info else print('Товар не найден')
        case 7:
            prod_id = get_int_input('Введите id продукта: ')
            days_left = db.check_date_of_product(prod_id)
            print(f'{days_left} дней' if days_left is not None else 'Товар не найден')
        case 8:
            name = input('Введите названия склад, который хотите удалить: ')
            deleted_id = db.current_warehouse(name)
            if db.delete_warehouse(name):
                if deleted_id == current_warehouse:
                    current_warehouse = None  # удалили выбранный склад
                print('Склад удалён')
            else:
                print('Склад не найден')
        case 9:
            exit()
