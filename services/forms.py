import aiohttp
from typing import Optional, Dict

from .models import FormData, Validation
from config import config
from pprint import pprint


class BaseYandexForms:
    def __init__(self):
        self.base_url = config.YAFORMS_BASE_URL
        self.api_base_url = config.FORMS_PUBLIC_API
        self.api_token = config.AUTH_YANDEX_FORMS

    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_token}',
        }

    async def _start_export(
        self,
        survey_id: str,
        format: str,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """
        Запускает фоновый процесс экспорта ответов. Возвращает id операции.
        """
        owns = False
        if session is None:
            session = aiohttp.ClientSession()
            owns = True
        try:
            url = f'{self.api_base_url}/surveys/{survey_id}/answers/export'
            payload = {'format': format}
            async with session.post(
                url,
                headers=self._headers(),
                json=payload,
            ) as resp:
                print(resp.status)
                if resp.status == 202:
                    data = await resp.json()
                    return data.get('id')
        finally:
            if owns:
                await session.close()

    async def _check_finished(
        self,
        operation_id: str,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        owns = False
        if session is None:
            session = aiohttp.ClientSession()
            owns = True
        try:
            url = f'{self.api_base_url}/operations/{operation_id}'
            async with session.get(
                url,
                headers=self._headers(),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('status') == 'ok'
        finally:
            if owns:
                await session.close()

    async def _get_result(
        self,
        survey_id: str,
        operation_id: str,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        owns = False
        if session is None:
            session = aiohttp.ClientSession()
            owns = True
        try:
            url = (
                f'{self.api_base_url}/surveys/{survey_id}/answers/export-results'
            )
            params = {'task_id': operation_id}
            async with session.get(
                url,
                params=params,
                headers=self._headers(),
            ) as resp:
                if resp.status == 200:
                    return await resp.read()
        finally:
            if owns:
                await session.close()


class YandexForms(BaseYandexForms):
    """
    Клиент для работы с Яндекс Формами.

    Поддерживает:
    - получение списка вопросов формы
    - заполнение формы
    - выгрузка результатов прохождения формы

    Базовый адрес сервиса Яндекс Формы можно переопределить
    переменной 'YAFORMS_BASE_URL'
    Базовый адрес API можно переопределить переменной `FORMS_PUBLIC_API`.
    Аутентификация: Bearer-токен в переменной окружения `AUTH_YANDEX_FORMS`.
    """

    async def get_form_data(
        self,
        survey_id: str,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """
        Возвращает структуру/вопросы формы по `survey_id`.
        """
        owns = False
        if session is None:
            session = aiohttp.ClientSession()
            owns = True

        try:
            url = f'{self.api_base_url}/surveys/{survey_id}/form'

            async with session.get(
                url,
                headers=self._headers(),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return FormData(**data)
                else:
                    error_text = await resp.text()
                    raise Exception(f"Error {resp.status}: {error_text}")
        finally:
            if owns:
                await session.close()

    async def fill_the_form(
        self,
        survey_id: str,
        answers: Dict,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """Отправляет ответы в форму."""
        owns = False
        if session is None:
            session = aiohttp.ClientSession()
            owns = True

        try:
            url = f'{self.api_base_url}/surveys/{survey_id}/form'

            async with session.post(
                url,
                json=answers,
                headers=self._headers(),
            ) as resp:
                if resp.status == 200:
                    return True
                else:
                    error_text = await resp.text()
                    raise Exception(f"Error {resp.status}: {error_text}")

        finally:
            if owns:
                await session.close()

    async def export_results(
        self,
        survey_id: str,
        format: str,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """
        Экспорт ответов. format in ('csv', 'xlsx')
        Возвращает bytes содержимое файла.
        """
        owns = False
        if session is None:
            session = aiohttp.ClientSession()
            owns = True
        try:
            operation_id = await self._start_export(
                survey_id,
                format,
                session=session,
            )
            if not operation_id:
                return None

            finished = False
            while not finished:
                finished = await self._check_finished(
                    operation_id,
                    session=session,
                )

            result = await self._get_result(
                survey_id,
                operation_id,
                session=session,
            )
            return result
        finally:
            if owns:
                await session.close()


ya_forms = YandexForms()
