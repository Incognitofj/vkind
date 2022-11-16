import vk_api
from dbmanager import DBManager


class Searcher:
    """
    Класс для поиска людей
    """
    def __init__(self, token):
        self.vk = vk_api.VkApi(token=token)
        self.api = self.vk.get_api()
        self.db = DBManager()

    def search(self, user_id):
        """
        Метод поиска для заданного пользователя по сохраненным параметрам поиска
        :param user_id: id пользователя, с которым работаем
        :return: список найденных людей
        """
        params = {}
        filters = self.db.getAllFilters(user_id)
        for f in filters:
            params[f[0]] = f[1]
        return self.api.users.search(**params, has_photo=1, count=1000)

    def getTop3(self, user_id):
        """
        Метод поиска трех фото
        :param user_id: id пользователя, с которым работаем
        :return: список из максимум трех фото (может быть меньше)
        """
        photos = self.api.photos.get(owner_id=user_id, album_id='profile')
        # Соберем id фото в один список и получим по ним информацию
        photos_list = ""
        for photo in photos['items']:
            if len(photos_list) > 0:
                photos_list += ","
            photos_list += f"{photo['owner_id']}_{photo['id']}"
        info = self.api.photos.getById(photos=photos_list, extended=1)
        # Найдем три самых популярных фото
        top3 = []
        photos = []
        for i in info:
            rate = i['likes']['count'] + i['comments']['count']
            photos.append({'photo': i, 'rate': rate})
        photos.sort(key=lambda ph: ph['rate'], reverse=True)
        for i in range(min(3, len(photos))):
            top3.append(photos[i]['photo'])
        # Выберем самые качественные фото
        best_photos = []
        max_pic = None
        for photo in top3:
            for pic in photo['sizes']:
                if max_pic is None or pic['width'] > max_pic['width']:
                    max_pic = pic
            best_photos.append(max_pic)
        return best_photos

    def getBuddy(self, user_id, n):
        """
        Метод получения данных человека, которые нужно вывести в чат
        :param user_id: id пользователя, с которым работаем
        :param n: количество людей, которых нужно найти
        :return: список найденных людей
        """
        buddies = []
        result = self.search(user_id)
        for item in result['items']:
            if self.db.hasExclusion(user_id, item['id']):
                continue
            if item['can_access_closed']:
                photos = self.getTop3(item['id'])
                if len(photos) >= 3:
                    buddy = {
                        'id': item['id'],
                        'name': f"{item['first_name']} {item['last_name']}",
                        'photos': photos
                    }
                    buddies.append(buddy)
            if len(buddies) == n:
                break
        return buddies
