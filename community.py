from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.upload import VkUpload
from searcher import Searcher
from dbmanager import DBManager
import requests
from io import BytesIO


class Community:
    """
    Класс для работы с сообществом
    """

    def __init__(self, community_token, user_token):
        self.vk = vk_api.VkApi(token=community_token)
        self.api = self.vk.get_api()
        self.longpoll = VkLongPoll(self.vk)
        self.search = Searcher(user_token)
        self.upload = VkUpload(self.vk)
        self.db = DBManager()

    def upload_photo(self, url, user_id):
        """
        Метод загрузки фото
        :param url: Ссылка на фото
        :param user_id: id пользователя/сообщества, которому загружается фото
        :return: параметры загруженного фото
        """
        err = None
        try:
            img = requests.get(url).content
            f = BytesIO(img)
            response = self.upload.photo_messages(f, user_id)[0]
            owner_id = response['owner_id']
            photo_id = response['id']
            access_key = response['access_key']
        except Exception:
            return "Произошла ошбика при загрузке файла. Попробуйте повторить позднее.", None, None, None
        return err, owner_id, photo_id, access_key

    def sendMessage(self, user_id, message):
        """
        Метод отправки сообщений пользователю
        :param user_id: id пользователя
        :param message: сообщение
        """
        self.vk.method('messages.send', {
            'user_id': user_id,
            'message': message,
            'random_id': randrange(10 ** 7),
        })

    def sendPhoto(self, user_id, owner_id, photo_id, access_key):
        """
        Метод отправки сообщения
        :param user_id: id пользователя, которому отправляется сообщение
        :param owner_id: id владельца фото
        :param photo_id: id фото
        :param access_key: ключ доступа
        """
        attachment = f'photo{owner_id}_{photo_id}_{access_key}'
        self.vk.method('messages.send', {
            'peer_id': user_id,
            'user_id': user_id,
            'attachment': attachment,
            'random_id': randrange(10 ** 7),
        })

    def listen(self):
        """
        Метод ожидания новых сообщений
        """
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:

                if event.to_me:
                    request = event.text.lower()
                    user_id = event.user_id
                    if "помоги" in request or "помощь" in request:
                        self.help(user_id)
                    elif "=" in request:
                        msg = self.setParam(event.user_id, request)
                        self.sendMessage(user_id, msg)
                    elif request == "параметры":
                        params = self.getParams(event.user_id)
                        self.sendMessage(user_id, params)
                    elif request == "сбрось":
                        self.delParams(user_id)
                        self.sendMessage(user_id, "Готово")
                    elif request == "ищи":
                        self.sendMessage(user_id, "Начинаю поиск. Подождите немного...")
                        err, buddies = self.search.getBuddy(user_id, 2)
                        if err is not None:
                            self.sendMessage(user_id, err)
                        else:
                            for buddy in buddies:
                                self.db.addExclusion(event.user_id, buddy['id'])
                                self.sendMessage(user_id, buddy['name'])
                                self.sendMessage(user_id, f"https://vk.com/id{buddy['id']}")
                                for photo in buddy['photos']:
                                    url = photo['url']
                                    err, owner_id, photo_id, access_key = self.upload_photo(url, event.user_id)
                                    if err is not None:
                                        self.sendMessage(user_id, err)
                                    else:
                                        self.sendPhoto(event.user_id, owner_id, photo_id, access_key)
                    else:
                        self.sendMessage(user_id, "Не поняла вашего вопроса...")

    def help(self, user_id):
        """
        Метод вывода пользователю информации по работе с ботом
        :param user_id: id пользователя, которому отправляется сообщение
        """
        self.sendMessage(user_id, """Вы можете использовать следующие команды:\n
                                  * ищи - для запуска поиска\n
                                  * сбрось - для сброса настроек поиска\n
                                  * <параметр> = <значение>, где <параметр> - один из списка:
                                  age_from, age_to, sex, hometown, status,
                                  а <значение> - соответствующее ему значение\n
                                  * параметры - для просмотра текущих значений параметров""")

    def setParam(self, user_id, param):
        """
        Метод задания параметра поиска
        :param user_id: id пользователя, который работает с ботом
        :param param: имя и значение параметра, введенные пользователем
        :return: Ответное сообщение (все хорошо или ошибка)
        """
        err, msg, name, value = self.db.testFilter(param)
        if err:
            return msg
        else:
            self.db.setFilter(user_id, name, value)
            return "Понял, принял"

    def getParams(self, user_id):
        """
        Метод получения параметров из базы
        :param user_id: id пользователя, с которым работаем
        :return: Список параметров (в виде строки)
        """
        filters = self.db.getAllFilters(user_id)
        result = ""
        for f in filters:
            if not result == "":
                result = result + "\n"
            result += f"{f[0]} = {f[1]}"
        if result == "":
            return "Параметры не заданы"
        else:
            return result

    def delParams(self, user_id):
        """
        Метод очищает список параметров поиска для заданного пользователя
        :param user_id: id пользователя, с которым работаем
        """
        self.db.clearAllFilters(user_id)
