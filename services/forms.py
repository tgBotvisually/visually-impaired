import aiohttp
import asyncio
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
    Базовый адрес API можно переопределить переменной `FORMS_PUBLIC_API`.
    Аутентификация: Bearer-токен в переменной окружения `AUTH_YANDEX_FORMS`.
    """

    def __init__(self):
        self.base_url = config.YAFORMS_BASE_URL
        self.api_base_url = config.FORMS_PUBLIC_API
        self.api_token = config.AUTH_YANDEX_FORMS

    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    async def get_form_data(
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
                json=payload,
                headers=self._headers(),
            ) as resp:
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

    async def export_results(
        self,
        survey_id: str,
        format: str,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """
        Экспорт ответов. format in ('json', 'csv', 'xlsx')
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
