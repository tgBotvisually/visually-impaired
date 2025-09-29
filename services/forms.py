import aiohttp
from typing import Optional, Dict

from config import config


class YandexForms:
    """
    Клиент для работы с Яндекс Формами.

    Поддерживает:
    - получение списка форм
    - получение списка вопросов формы
    - отправку ответов (и экспорт ответов, если требуется получить выгрузку)

    Базовый адрес сервиса Яндекс Формы можно переопределить
    переменной 'YAFORMS_BASE_URL'
    Базовый адрес API можно переопределить переменной `API_YAFORMS_BASE_URL`.
    Аутентификация: OAuth-токен в переменной окружения `AUTH_YANDEX_FORMS`.
    """

    def __init__(self):
        self.base_url = config.YAFORMS_BASE_URL
        self.api_base_url = config.API_YAFORMS_BASE_URL
        self.api_token = config.AUTH_YANDEX_FORMS

    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'OAuth {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    async def list_forms(
        self,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """
        Возвращает список доступных форм.
        """
        pass

    async def get_form_questions(
        self,
        form_id: str,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """
        Возвращает структуру/вопросы формы по `form_id`.
        """
        pass

    async def submit_answers(
        self,
        form_id: str,
        answers: list,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """Отправляет ответы в форму."""
        pass

    async def export_responses(
        self,
        form_id: str,
        format_: str = 'json',
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """Экспорт ответов из формы."""
        pass
