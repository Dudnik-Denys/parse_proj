import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests
import json
from fake_useragent import UserAgent
from collections import namedtuple

load_dotenv()


class FilmsParser:
    _URL = 'https://rezka.ag'
    _USER_AGENT = UserAgent()
    _HEADERS = {'User-Agent': _USER_AGENT.random}
    _PROXIES = {'http': f'socks5://{os.getenv("LOGIN")}:{os.getenv("PASSWORD")}@{os.getenv("PROXY")}:50101',
                'https': f'socks5://{os.getenv("LOGIN")}:{os.getenv("PASSWORD")}@{os.getenv("PROXY")}:50101'}

    def __init__(self, parse_format: str = 'json', pages_count: int = 10, genre: str = '', best: bool = True):
        self._available_formats = ('json', )
        self.__session = requests.Session()
        self.__result = ()
        self.parse_format = parse_format
        self.pages_count = pages_count
        self.genre = genre
        self.best = best
        self._base_url = (genre, best)

    @property
    def parse_format(self) -> str:
        return self._parse_format

    @parse_format.setter
    def parse_format(self, new_format: str) -> None:
        if new_format in self._available_formats:
            self._parse_format = new_format
        else:
            raise ValueError(f'Invalid parsing format. Please, enter valid type format from '
                             f'formats list: {self._available_formats}')

    def _cook(self, link: str) -> BeautifulSoup:
        response = self.__session.get(link, headers=FilmsParser._HEADERS, proxies=FilmsParser._PROXIES)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'lxml')

    def _get_json_info(self, film_page: BeautifulSoup) -> dict:
        FilmInfo = namedtuple('FilmInfo', ['title', 'description'])
        data = film_page.select_one('table.b-post__info').select('tr')
        description = {}

        for tr in data:
            table = [td for td in tr if td != ' ']
            if len(table) == 2:
                info = FilmInfo(*table)
                parsed = self._parse_info(info)
                description.update(parsed)

        result = {'title': film_page.select_one('div.b-post__title h1').text,
                  'description': description}
        return result

    @staticmethod
    def _parse_info(film_info) -> dict:
        try:
            title = film_info.title.select_one('h2').text
        except AttributeError:
            title = film_info.title.text
        description = film_info.description
        try:
            match title:
                case 'Рейтинги':
                    links = [link.text for link in description.select('a')]
                    ratings = [rating.text for rating in description.select('span.bold')]
                    result = ', '.join(f'{key}: {value}' for key, value in dict(zip(links, ratings)).items())
                    return {title: result}
                case 'Входит в списки':
                    return {title: ', '.join([link.text for link in description.select('a')])}
                case 'Слоган':
                    return {title: description.text}
                case 'Дата выхода':
                    return {title: description.text + description.select_one('a').text}
                case 'Год:':
                    return {'Дата выхода': description.select_one('a').text}
                case 'Страна':
                    return {title: ', '.join([country.text for country in description.select('a')])}
                case 'Режиссер':
                    return {title: ', '.join([creator.text for creator in description.select('span[itemprop="name"]')])}
                case 'Жанр':
                    return {title: ', '.join([genre.text for genre in description.select('span[itemprop="genre"]')])}
                case 'В качестве':
                    return {title: description.text}
                case 'В переводе':
                    return {title: description.text}
                case 'Возраст':
                    return {title: description.select_one('span').text}
                case 'Время':
                    return {title: description.text}
                case 'Из серии':
                    return {title: ', '.join([link.text for link in description.select('a')])}
                case _:
                    return {title: None}
        except AttributeError:
            return {title: None}

    @property
    def _base_url(self) -> str:
        return self.__base_url

    @_base_url.setter
    def _base_url(self, data: tuple):
        genre, best = data
        result = '/films'
        if best:
            result += '/best'
        self.__base_url = FilmsParser._URL + result + genre

    @staticmethod
    def _get_films(page: BeautifulSoup) -> list:
        try:
            films = [film['href'] for film in
                     page.select_one('div.b-content__inline_items').select('div.b-content__inline_item-link a')]
        except AttributeError:
            raise ValueError('Can\'t get films page')
        return films

    def _write_to_json(self):
        with open('result.json', 'w', encoding='utf-8') as file:
            json.dump(self.__result, file, indent=4, ensure_ascii=False)

    def parse(self):
        for page in range(1, self.pages_count + 1):
            films_page = self._cook(f'{self._base_url}/page/{page}')
            films = self._get_films(films_page)
            for film in films:
                link = self._cook(film)
                data = self._get_json_info(link)
                self.__result += (data, )
        self._write_to_json()

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._parse_format}, {self.pages_count}, {self.genre}, {self.best})'
