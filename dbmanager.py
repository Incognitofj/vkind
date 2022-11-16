import sqlite3


class DBManager:
    """
    Класс для работы с базой данных
    """
    def __init__(self):
        self.con = sqlite3.connect('../../A/PY/VKinder/db.db')

    @staticmethod
    def testFilter(user_filter):
        """
        Метод для проверки заданного пользователем параметра поиска
        :param user_filter: имя и значение параметра одной строкой
        :return: ошибка (True - есть, False - нет), имя параметра, значение параметра
        """
        result = user_filter.split('=')
        if not len(result) == 2:
            return True, "Неверное задание параметра", None, None
        name = result[0].strip()
        value = result[1].strip()
        if name not in ['age_from', 'age_to', 'sex', 'hometown', 'status']:
            return True, "Недопустимое имя параметра", None, None
        return False, "", name, value

    def getFilter(self, user_id, name):
        """
        Метод получения значения параметра поиска
        :param user_id: id пользователя, с которым работаем
        :param name: имя параметра
        :return: значение параметра или None, если параметр не найден
        """
        data = self.con.execute(f"SELECT value FROM filter WHERE user_id = '{user_id}' AND name = '{name}'")
        if len(list(data)) <= 0:
            return None
        else:
            return data.fetchall()[0][0]

    def setFilter(self, user_id, name, value):
        """
        Метод сохранения параметра в базе данных
        :param user_id: id пользователя, с которым работаем
        :param name: имя параметра
        :param value: значение параметра
        """
        old_value = self.getFilter(user_id, name)
        if old_value is None:
            self.con.execute(f"INSERT INTO filter (user_id, name, value) VALUES ('{user_id}', '{name}', '{value}')")
        else:
            self.con.execute(f"UPDATE filter SET value = '{value}' WHERE user_id = '{user_id}' AND name = '{name}'")
        self.con.commit()

    def getAllFilters(self, user_id):
        """
        Метод получения всех параметров поиска для заданного пользователя
        :param user_id: id пользователя, с которым работаем
        :return: список все параметров (имя, значение)
        """
        data = self.con.execute(f"SELECT name, value FROM filter WHERE user_id = '{user_id}'")
        return data.fetchall()

    def clearAllFilters(self, user_id):
        """
        Метод удаления всех параметров для заданного пользователя
        :param user_id: id пользователя, с которым работаем
        """
        self.con.execute(f"DELETE FROM filter WHERE user_id = '{user_id}'")
        self.con.commit()

    def addExclusion(self, user_id, buddy_id):
        """
        Метод добавляения в базу пользователя, которого больше не нужно выдавать при поиске
        :param user_id: id пользователя, с которым работаем
        :param buddy_id: id пользователя, которого нужно пропускать при поиске
        """
        self.con.execute(f"INSERT INTO exclude (user_id, buddy_id) VALUES ('{user_id}', '{buddy_id}')")
        self.con.commit()

    def hasExclusion(self, user_id, buddy_id):
        """
        Метод проверки, есть ли в базе пользователь, которого нужно пропускать при поиске
        :param user_id: id пользователя, с которым работаем
        :param buddy_id: id пользователя, которого ищем в базе
        :return: True - пользователь в списке, False - пользователя нет в списке
        """
        data = self.con.execute(f"SELECT * FROM exclude WHERE user_id = '{user_id}' AND buddy_id = '{buddy_id}'")
        if len(list(data)) <= 0:
            return False
        else:
            return True
